from enum import Enum

# Network constants
BROADCAST_PORT = 13117  # Used by both server to broadcast and client to listen
MAGIC_COOKIE = 0xabcddcba  # Used in packet validation
BUFFER_SIZE = 1024  # Shared buffer size for network operations

# Message type constants
MSG_TYPE_OFFER = 0x2  # Server -> Client offer message
MSG_TYPE_REQUEST = 0x3  # Client -> Server request message
MSG_TYPE_PAYLOAD = 0x4  # Server -> Client payload message


class ClientState(Enum):
    """Represents the possible states of the client application."""
    STARTUP = 1  # Initial state when client starts
    LOOKING_FOR_SERVER = 2  # Actively listening for server offers
    SPEED_TEST = 3  # Conducting speed test with server


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'  # Success messages
    BLUE = '\033[94m'  # Info messages
    RED = '\033[91m'  # Error messages
    YELLOW = '\033[93m'  # Warning messages
    RESET = '\033[0m'  # Reset color
