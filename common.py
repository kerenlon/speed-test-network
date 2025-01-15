# Message encodings
UDP_MAGIC_COOKIE = 0xabcddcba
UDP_MSG_TYPE_OFFER = 0x2
UDP_MSG_TYPE_REQUEST = 0x3
UDP_MSG_TYPE_PAYLOAD = 0x4

SERVER_ADDRESS = '172.0.1.4'
SERVER_UDP_PORT = 5005
SERVER_TCP_PORT = 9999



class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'  # Success messages
    BLUE = '\033[94m'  # Info messages
    RED = '\033[91m'  # Error messages
    YELLOW = '\033[93m'  # Warning messages
    RESET = '\033[0m'  # Reset color
