from enum import Enum

class State(Enum):
    CONNECT = 0
    HANDSHAKE = 1
    RECEIVE = 2
    ACK = 3
