import socket
import struct
from common import SERVER_ADDRESS, SERVER_UDP_PORT


class Client:

    def __init__(self):
        pass

    def start(self):
        print("Client started, listening to offer requests...")
        self.listen_to_offer()

    def listen_to_offer(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
            receiver.bind((SERVER_ADDRESS, SERVER_UDP_PORT))

            while True:
                data, addr = receiver.recvfrom(1024)
                msg = Client.hexify(struct.unpack('>LLLL', data), [0, 1])

                print(msg)
                print(addr)

    @staticmethod
    def hexify(data: tuple, lst_indx: list):
        temp = list(data)
        for indx in lst_indx:
            temp[indx] = hex(temp[indx])
        return tuple(temp)
