from enum import Enum

class PacketId(Enum):
    GV_PKT = 0
    RHAND_PKT = 1
    LHAND_PKT = 2
    GAMESTATE_PKT = 3
    ACK_PKT = 4
    H_PKT = 5