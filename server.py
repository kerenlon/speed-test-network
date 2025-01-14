import socket
import struct
import threading
import time
from typing import Tuple, List, Optional
from enum import Enum
import signal
import sys
from common import *


class ServerStatistics:
    """Track server statistics"""
    def __init__(self):
        self.total_tcp_connections = 0
        self.total_udp_connections = 0
        self.total_bytes_sent = 0
        self.start_time = time.time()
        self._lock = threading.Lock()

    def add_tcp_connection(self):
        with self._lock:
            self.total_tcp_connections += 1

    def add_udp_connection(self):
        with self._lock:
            self.total_udp_connections += 1

    def add_bytes_sent(self, bytes_count: int):
        with self._lock:
            self.total_bytes_sent += bytes_count

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def __str__(self) -> str:
        return (f"Server Statistics:\n"
                f"Uptime: {self.get_uptime():.2f} seconds\n"
                f"Total TCP connections: {self.total_tcp_connections}\n"
                f"Total UDP connections: {self.total_udp_connections}\n"
                f"Total bytes sent: {self.total_bytes_sent:,} bytes")


class SpeedTestServer:
    def __init__(self):
        self.tcp_port = 0
        self.udp_port = 0
        self.running = False
        self.tcp_socket: Optional[socket.socket] = None
        self.udp_socket: Optional[socket.socket] = None
        self.broadcast_socket: Optional[socket.socket] = None
        self.active_connections: List[threading.Thread] = []
        self.stats = ServerStatistics()
        self.stop_event = threading.Event()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n{Colors.YELLOW}Shutting down server...{Colors.RESET}")
        self.stop()

    def start(self):
        """Start the server and begin broadcasting offers."""
        try:
            self._setup_sockets()
            self.running = True

            ip_address = self._get_ip_address()
            print(f"{Colors.GREEN}Server started, listening on IP address {ip_address}{Colors.RESET}")

            self._start_server_threads()
            self._main_loop()

        except Exception as e:
            print(f"{Colors.RED}Fatal error starting server: {str(e)}{Colors.RESET}")
        finally:
            self.stop()

    def _get_ip_address(self) -> str:
        """Get the server's IP address"""
        try:
            # Try to get the primary non-localhost IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            # Fallback to hostname method
            return socket.gethostbyname(socket.gethostname())

    def _setup_sockets(self):
        """Setup all necessary sockets with proper error handling"""
        try:
            # Setup TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind(('', 0))
            self.tcp_port = self.tcp_socket.getsockname()[1]
            self.tcp_socket.listen(MAX_CONNECTIONS)

            # Setup UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind(('', 0))
            self.udp_port = self.udp_socket.getsockname()[1]

            # Setup broadcast socket
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        except Exception as e:
            raise RuntimeError(f"Failed to setup sockets: {str(e)}")

    def _start_server_threads(self):
        """Start all server threads"""
        threads = [
            (self._broadcast_offers, "BroadcastThread"),
            (self._handle_udp_requests, "UDPHandlerThread")
        ]

        for target, name in threads:
            thread = threading.Thread(target=target, name=name)
            thread.daemon = True
            thread.start()
            self.active_connections.append(thread)

    def _main_loop(self):
        """Main server loop accepting TCP connections"""
        self.tcp_socket.settimeout(1.0)  # Allow for checking stop_event

        while not self.stop_event.is_set():
            try:
                client_socket, address = self.tcp_socket.accept()
                if len(self.active_connections) < MAX_CONNECTIONS:
                    self._start_tcp_client_thread(client_socket, address)
                else:
                    print(f"{Colors.YELLOW}Maximum connections reached, rejecting client {address}{Colors.RESET}")
                    client_socket.close()
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"{Colors.RED}Error accepting TCP connection: {str(e)}{Colors.RESET}")

    def _start_tcp_client_thread(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Start a new thread for handling TCP client"""
        thread = threading.Thread(
            target=self._handle_tcp_client,
            args=(client_socket, address),
            name=f"TCPClient-{address[0]}:{address[1]}"
        )
        thread.daemon = True
        thread.start()
        self.active_connections.append(thread)

    def _broadcast_offers(self):
        """Broadcast offer messages every second."""
        while not self.stop_event.is_set():
            try:
                offer_message = struct.pack('!IbHH',
                                            MAGIC_COOKIE,
                                            MSG_TYPE_OFFER,
                                            self.udp_port,
                                            self.tcp_port)
                self.broadcast_socket.sendto(offer_message, ('<broadcast>', BROADCAST_PORT))
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"{Colors.RED}Error broadcasting offer: {str(e)}{Colors.RESET}")

    def _handle_udp_requests(self):
        """Handle UDP requests from clients."""
        self.udp_socket.settimeout(1.0)  # Allow for checking stop_event

        while not self.stop_event.is_set():
            try:
                data, addr = self.udp_socket.recvfrom(BUFFER_SIZE)
                self._process_udp_request(data, addr)
                self.stats.add_udp_connection()
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"{Colors.RED}Error in UDP handling: {str(e)}{Colors.RESET}")

    def _process_udp_request(self, data: bytes, addr: Tuple[str, int]):
        """Process a single UDP request"""
        try:
            magic_cookie, msg_type, file_size = struct.unpack('!IbQ', data)

            if magic_cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST:
                return

            packet_size = BUFFER_SIZE - 21
            total_packets = (file_size + packet_size - 1) // packet_size

            for i in range(total_packets):
                if self.stop_event.is_set():
                    break

                payload_size = min(packet_size, file_size - i * packet_size)
                payload = b'0' * payload_size

                udp_response = struct.pack(
                    f'!IbQQ{payload_size}s',
                    MAGIC_COOKIE,
                    MSG_TYPE_PAYLOAD,
                    total_packets,
                    i,
                    payload
                )

                self.udp_socket.sendto(udp_response, addr)
                self.stats.add_bytes_sent(payload_size)

                # Small delay to prevent overwhelming the network
                time.sleep(0.001)

        except struct.error:
            print(f"{Colors.RED}Malformed UDP request from {addr}{Colors.RESET}")

    def _handle_tcp_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle TCP client connection and file transfer."""
        try:
            client_socket.settimeout(5)  # Set timeout for receiving data
            data = client_socket.recv(BUFFER_SIZE).decode()
            file_size = int(data.strip())

            chunk_size = min(BUFFER_SIZE, file_size)
            dummy_data = b'0' * chunk_size
            bytes_sent = 0

            while bytes_sent < file_size and not self.stop_event.is_set():
                to_send = min(chunk_size, file_size - bytes_sent)
                client_socket.send(dummy_data[:to_send])
                bytes_sent += to_send
                self.stats.add_bytes_sent(to_send)

            self.stats.add_tcp_connection()

        except socket.timeout:
            print(f"{Colors.YELLOW}TCP client {address} timed out{Colors.RESET}")
        except Exception as e:
            if not self.stop_event.is_set():
                print(f"{Colors.RED}Error handling TCP client {address}: {str(e)}{Colors.RESET}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def stop(self):
        """Stop the server and cleanup resources."""
        self.running = False
        self.stop_event.set()

        # Print final statistics
        print(f"\n{Colors.BLUE}{self.stats}{Colors.RESET}")

        # Close all sockets
        for sock in [self.tcp_socket, self.udp_socket, self.broadcast_socket]:
            if sock:
                try:
                    sock.close()
                except:
                    pass

        # Wait for threads to finish
        for thread in self.active_connections:
            if thread.is_alive():
                thread.join(timeout=1.0)
