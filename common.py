# Constants for UDP
BROADCAST_PORT = 13117  # Used by both server to broadcast and client to listen
MAGIC_COOKIE = 0xabcddcba  # Used in packet validation
BUFFER_SIZE = 1024  # Shared buffer size for network operations
UDP_TIMEOUT = 2  # Timeout for UDP packets in seconds
BROADCAST_INTERVAL = 1  # Interval between broadcast offers
MAX_CONNECTIONS = 5  # Max TCP connections

# Message type constants
MSG_TYPE_OFFER = 0x2  # Server -> Client offer message
MSG_TYPE_REQUEST = 0x3  # Client -> Server request message
MSG_TYPE_PAYLOAD = 0x4  # Server -> Client payload message


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'  # Success messages
    BLUE = '\033[94m'  # Info messages
    RED = '\033[91m'  # Error messages
    YELLOW = '\033[93m'  # Warning messages
    RESET = '\033[0m'  # Reset color
