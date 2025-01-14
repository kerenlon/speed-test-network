import argparse
from time import sleep
from common import *


class SpeedTest:
    """Main class to handle both client and server functionality"""

    def __init__(self):
        self.client = None
        self.server = None

    def start_client(self):
        """Initialize and start client"""
        try:
            from client import SpeedTestClient
            self.client = SpeedTestClient()
            print(f"{Colors.BLUE}Starting client mode...{Colors.RESET}")
            self.client.start()
        except Exception as e:
            print(f"{Colors.RED}Failed to start client: {str(e)}{Colors.RESET}")

    def start_server(self):
        """Initialize and start server"""
        try:
            from server import SpeedTestServer
            self.server = SpeedTestServer()
            print(f"{Colors.BLUE}Starting server mode...{Colors.RESET}")
            self.server.start()
        except Exception as e:
            print(f"{Colors.RED}Failed to start server: {str(e)}{Colors.RESET}")

    @staticmethod
    def main():
        """Main entry point with argument parsing"""
        parser = argparse.ArgumentParser(description='Speed Test Application')
        parser.add_argument('mode', choices=['client', 'server'],
                            help='Run as client or server')

        args = parser.parse_args()
        speed_test = SpeedTest()

        try:
            if args.mode == 'client':
                speed_test.start_client()
            else:
                speed_test.start_server()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Shutting down...{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")


if __name__ == "__main__":
    SpeedTest.main()