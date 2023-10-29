class HandshakeException(Exception):
    """Exception raised when a handshake fails."""

    def __init__(self, message="Handshake failed."):
        super().__init__(message)

class DuplicateException(Exception):
    """Exception raised when packet is duplicated."""

    def __init__(self, message="Packet is duplicated. Dropping packet..."):
        super().__init__(message)

class PacketIDException(Exception):
    """Exception raised when a packet ID is invalid."""

    def __init__(self, message="Invalid packet ID. (Packet ID not found)"):
        super().__init__(message)

class CRCException(Exception):
    """Exception raised when a CRC checksum fails."""

    def __init__(self, message="CRC checksum failed, packet corrupted."):
        super().__init__(message)