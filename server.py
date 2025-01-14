import socket
import struct
import time
import threading
from common import *
from typing import Tuple, List


class SpeedTestServer:
    def __init__(self, server_ip, server_port=5001):
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = False
        self.server_socket = None

    def start(self):
        """Start the server to listen for incoming connections."""
        try:
            self.server_socket = self._create_server_socket()
            print(
                f"{Colors.GREEN}Server started, waiting for clients on {self.server_ip}:{self.server_port}...{Colors.RESET}")

            self.running = True
            while self.running:
                self._handle_incoming_connections()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Shutting down server...{Colors.RESET}")
        finally:
            self._cleanup()

    def _setup_udp_socket(self):
        """Setup UDP socket"""
        try:
            # Create a UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Bind the socket to the given UDP port
            self.udp_socket.bind(('', self.udp_port))
            print(f"UDP socket setup successfully on port {self.udp_port}")
        except Exception as e:
            print(f"{Colors.RED}Error setting up UDP socket: {str(e)}{Colors.RESET}")
            self.running = False

    def _setup_tcp_socket(self):
        """Setup TCP socket"""
        try:
            # Create a TCP socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Bind the socket to the given TCP port
            self.tcp_socket.bind(('', self.tcp_port))
            self.tcp_socket.listen(MAX_CONNECTIONS)  # Set the maximum number of connections
            print(f"TCP socket setup successfully on port {self.tcp_port}")
        except Exception as e:
            print(f"{Colors.RED}Error setting up TCP socket: {str(e)}{Colors.RESET}")
            self.running = False

    def _handle_udp_requests(self):
        """Handle incoming UDP requests for speed test"""
        try:
            data, addr = self.udp_socket.recvfrom(BUFFER_SIZE)
            magic_cookie, msg_type, file_size = struct.unpack('!IbQ', data)

            if magic_cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_REQUEST:
                print(f"Received UDP request from {addr}, sending response...")
                self._send_udp_offer(addr)
        except Exception as e:
            print(f"{Colors.RED}Error handling UDP request: {str(e)}{Colors.RESET}")

    def _send_udp_offer(self, addr: Tuple[str, int]):
        """Send UDP offer to client"""
        ports = (12345, 12346)  # Example ports
        response = struct.pack('!IbQ', MAGIC_COOKIE, MSG_TYPE_OFFER, *ports)
        self.udp_socket.sendto(response, addr)

    def _handle_tcp_connections(self):
        """Handle TCP connections"""
        try:
            conn, addr = self.tcp_socket.accept()
            print(f"Connection established with {addr}")

            file_size = int(conn.recv(1024).decode())  # Receive the file size
            self._handle_tcp_transfer(conn, file_size)
        except Exception as e:
            print(f"{Colors.RED}Error handling TCP connection: {str(e)}{Colors.RESET}")

    def _handle_tcp_transfer(self, conn: socket.socket, file_size: int):
        """Handle the actual TCP transfer"""
        total_received = 0
        start_time = time.time()

        while total_received < file_size:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            total_received += len(data)
            conn.send(data)  # Echo the data back to simulate transfer

        print(f"{Colors.GREEN}TCP transfer finished, total time: {time.time() - start_time:.2f} seconds{Colors.RESET}")
        conn.close()

    def _cleanup(self):
        """Cleanup resources (close the socket)."""
        if self.server_socket:
            self.server_socket.close()
            print("Server socket closed.")
