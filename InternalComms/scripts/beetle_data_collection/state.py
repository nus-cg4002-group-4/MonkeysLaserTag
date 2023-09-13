from enum import Enum

class State(Enum):
    connect = 0
    receive = 1
    ack = 2
