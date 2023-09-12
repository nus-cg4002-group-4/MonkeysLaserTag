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
class GvPacket:
    pkt_id: int
    seq_no: int
    # IR Receivers
    ir_rcv_1: int
    ir_rcv_2: int
    # IR Transmitters
    ir_trm_1: int
    ir_trm_2: int

@dataclass
class RHandDataPacket:
    pkt_id: int
    seq_no: int
    ir_trm: int
    button: int
    flex: int
    # Gyro
    yaw: int
    pitch: int
    roll: int
    # Accel
    x: int
    y: int
    z: int

@dataclass
class LHandDataPacket:
    pkt_id: int
    seq_no: int
    # Gyro
    yaw: int
    pitch: int
    roll: int
    # Accel
    x: int
    y: int
    z: int

