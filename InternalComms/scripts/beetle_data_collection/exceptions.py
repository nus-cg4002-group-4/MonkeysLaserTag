class HandshakeException(Exception):
    """Exception raised when a handshake fails."""

    def __init__(self, message="Handshake failed."):
        super().__init__(message)

class DisconnectException(Exception):
    """Exception raised when a beetle is disconnected."""

    def __init__(self, message="Beetle disconnected."):
        super().__init__(message)

class PacketIDException(Exception):
    """Exception raised when a packet ID is invalid."""

    def __init__(self, message="Invalid packet ID. (Packet ID not found)"):
        super().__init__(message)

class CRCException(Exception):
    """Exception raised when a CRC checksum fails."""

    def __init__(self, message="CRC checksum failed, packet corrupted."):
        super().__init__(message)