import socket
import threading
import time
from enum import Enum
from common import *
import struct
from typing import Optional, Tuple


class ClientState(Enum):
    """Enum to represent client states"""
    STARTUP = 1
    LOOKING_FOR_SERVER = 2
    SPEED_TEST = 3


class SpeedTestStatistics:
    """Class to track and calculate transfer statistics"""

    def __init__(self):
        self.start_time = time.time()
        self.bytes_transferred = 0
        self.packets_received = 0
        self.total_packets = 0

    def get_duration(self) -> float:
        return time.time() - self.start_time

    def get_speed(self) -> float:
        duration = self.get_duration()
        return (self.bytes_transferred * 8) / duration if duration > 0 else 0

    def get_success_rate(self) -> float:
        return (self.packets_received / self.total_packets * 100) if self.total_packets > 0 else 0


class SpeedTestClient:
    def __init__(self, listen_port=5003):
        self.listen_port = listen_port
        self.running = False
        self.udp_socket = None

    def start(self):
        """Start the client to send/receive data."""
        try:
            self._setup_udp_socket()
            print(f"Client started, listening on port {self.listen_port}...")

            self.running = True
            while self.running:
                # Perform tasks like searching for a server, etc.
                pass
        except KeyboardInterrupt:
            print("Shutting down client...")
        finally:
            self._cleanup()

    def _setup_udp_socket(self):
        """Set up UDP socket with proper error handling."""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.udp_socket.bind(('', BROADCAST_PORT))
        except Exception as e:
            raise RuntimeError(f"Failed to setup UDP socket: {str(e)}")

    def _run_state_machine(self):
        """Run the main state machine."""
        if self.state == ClientState.LOOKING_FOR_SERVER:
            self._handle_server_discovery()
        elif self.state == ClientState.SPEED_TEST:
            self._handle_speed_test()
            self.state = ClientState.LOOKING_FOR_SERVER
            print(f"{Colors.BLUE}All transfers complete, listening to offer requests{Colors.RESET}")

    def _handle_server_discovery(self):
        """Handle the LOOKING_FOR_SERVER state."""
        server_ip, ports = self._wait_for_offer()
        print(f"{Colors.BLUE}Received offer from {server_ip}{Colors.RESET}")

        # Get user parameters only once
        file_size = int(input("Enter file size (bytes): "))
        tcp_connections = int(input("Enter number of TCP connections: "))
        udp_connections = int(input("Enter number of UDP connections: "))

        self.current_server = (server_ip, ports)
        self._setup_transfer_threads(server_ip, ports, file_size, tcp_connections, udp_connections)
        self.state = ClientState.SPEED_TEST

    def _setup_transfer_threads(self, server_ip: str, ports: Tuple[int, int],
                                file_size: int, tcp_count: int, udp_count: int):
        """Set up transfer threads with proper error handling."""
        self.transfer_threads = []

        for i in range(tcp_count):
            thread = threading.Thread(
                target=self._tcp_transfer,
                args=(server_ip, ports[1], file_size, i + 1),
                name=f"TCP-{i + 1}"
            )
            self.transfer_threads.append(thread)

        for i in range(udp_count):
            thread = threading.Thread(
                target=self._udp_transfer,
                args=(server_ip, ports[0], file_size, i + 1),
                name=f"UDP-{i + 1}"
            )
            self.transfer_threads.append(thread)

    def _tcp_transfer(self, server_ip: str, port: int, file_size: int, connection_num: int):
        """Handle TCP file transfer with improved error handling and statistics."""
        stats = SpeedTestStatistics()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # Connection timeout

        try:
            sock.connect((server_ip, port))
            sock.send(f"{file_size}\n".encode())

            last_report_time = time.time()
            while stats.bytes_transferred < file_size and not self.stop_event.is_set():
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    break
                stats.bytes_transferred += len(data)

                # Periodic progress report
                now = time.time()
                if now - last_report_time >= 1.0:
                    print(f"[TCP #{connection_num}] Progress: {stats.bytes_transferred / file_size * 100:.2f}%")
                    last_report_time = now

            print(f"{Colors.GREEN}TCP transfer #{connection_num} finished, "
                  f"total time: {stats.get_duration():.2f} seconds, "
                  f"total speed: {stats.get_speed():.1f} bits/second{Colors.RESET}")

        except socket.timeout:
            print(f"{Colors.RED}TCP transfer #{connection_num} timed out{Colors.RESET}")
        except ConnectionRefusedError:
            print(f"{Colors.RED}TCP transfer #{connection_num} connection refused{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error in TCP transfer #{connection_num}: {str(e)}{Colors.RESET}")
        finally:
            sock.close()

    def _udp_transfer(self, server_ip: str, port: int, file_size: int, connection_num: int):
        """Handle UDP file transfer with improved error handling and statistics."""
        stats = SpeedTestStatistics()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(UDP_TIMEOUT)

        try:
            request = struct.pack('!IbQ', MAGIC_COOKIE, MSG_TYPE_REQUEST, file_size)
            sock.sendto(request, (server_ip, port))

            last_packet_time = time.time()

            while not self.stop_event.is_set():
                try:
                    data, _ = sock.recvfrom(BUFFER_SIZE)
                    current_time = time.time()

                    if current_time - last_packet_time > UDP_TIMEOUT:
                        break

                    last_packet_time = current_time

                    # Handle malformed or unexpected payload sizes
                    try:
                        header_size = struct.calcsize('!IbQQ')
                        magic_cookie, msg_type, total_segments, current_segment = \
                            struct.unpack('!IbQQ', data[:header_size])

                        payload = data[header_size:]

                        if magic_cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
                            continue

                        stats.bytes_transferred += len(payload)
                        stats.packets_received += 1
                        stats.total_packets = total_segments

                    except struct.error:
                        print(
                            f"{Colors.YELLOW}[UDP #{connection_num}] Received malformed packet, skipping.{Colors.RESET}")

                except socket.timeout:
                    break

            print(f"{Colors.GREEN}UDP transfer #{connection_num} finished, "
                  f"total time: {stats.get_duration():.2f} seconds, "
                  f"total speed: {stats.get_speed():.1f} bits/second, "
                  f"percentage of packets received successfully: {stats.get_success_rate():.1f}%{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error in UDP transfer #{connection_num}: {str(e)}{Colors.RESET}")
        finally:
            sock.close()

    def _cleanup(self):
        """Cleanup resources (close the socket)."""
        if self.udp_socket:
            self.udp_socket.close()
            print("Client socket closed.")
