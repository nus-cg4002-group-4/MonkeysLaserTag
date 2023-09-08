from enum import Enum
from dataclasses import dataclass

class PacketId(Enum):
    GV_PKT = 0
    RHAND_PKT = 1
    LHAND_PKT = 2
    GAMESTATE_PKT = 3
    ACK_PKT = 4
    H_PKT = 5

@dataclass
class gvPacket:
    pkt_id: int
    seq_no: int
    ir_rcv_1: int
    ir_rcv_2: int
    ir_trm_1: int
    ir_trm_2: int