import threading
from client import SpeedTestClient
from server import SpeedTestServer


def run_server(host, port):
    server = SpeedTestServer(host, port)
    server.start()


def run_client(listen_port):
    client = SpeedTestClient(listen_port)
    client.start()


if __name__ == "__main__":
    role = input("Enter role (client or server): ").lower()

    if role == 'server':
        host = input("Enter server IP address (default: localhost): ") or "localhost"
        port = int(input(f"Enter server port (default: 5001): ") or 5001)
        print(f"Starting server on {host}:{port}")

        # Start the server in a separate thread
        server_thread = threading.Thread(target=run_server, args=(host, port))
        server_thread.start()
        server_thread.join()  # Wait for the server to finish
    elif role == 'client':
        listen_port = int(input(f"Enter client listen port (default: 5003): ") or 5003)
        print(f"Starting client with listen port: {listen_port}")

        # Start the client
        run_client(listen_port)
    else:
        print("Invalid role. Please enter 'client' or 'server'.")
