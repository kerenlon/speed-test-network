import struct
import socket
import threading
from time import sleep
from Exceptions import ServerBroadcastException
from Globals import SERVER_ADDRESS, UDP_MAGIC_COOKIE, UDP_MSG_TYPE_OFFER, SERVER_UDP_PORT, SERVER_TCP_PORT


class Server:

    def __init__(self, address=None):
        self.running = False

    def start(self):
        self.running = True
        print(f'Server started, listening on IP address {SERVER_ADDRESS}')
        broadcast_thread = threading.Thread(name='broadcast_thread', target=self.broadcast)
        broadcast_thread.start()

    def broadcast(self):
        if not self.running:
            raise ServerBroadcastException('Server not running')

        timeout = 1
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            msg = struct.pack('>LLLL', UDP_MAGIC_COOKIE,
                              UDP_MSG_TYPE_OFFER,
                              SERVER_UDP_PORT,
                              SERVER_TCP_PORT)

            while Server.check_running(self):
                sender.sendto(msg, (SERVER_ADDRESS, SERVER_UDP_PORT))
                sleep(timeout)

    @staticmethod
    def check_running(server):
        return server.running
