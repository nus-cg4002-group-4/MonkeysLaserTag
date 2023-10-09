from enum import Enum
from dataclasses import dataclass

class PacketId(Enum):
    RHAND_PKT = 1
    VEST_PKT = 2
    GAMESTATE_PKT = 3
    ACK_PKT = 4
    H_PKT = 5

@dataclass
class VestPacket:
    pkt_id: int
    seq_no: int
    # IR Receivers
    ir_rcv_1: int
    ir_rcv_2: int
    health: int
    shield: int
    

@dataclass
class RHandDataPacket:
    pkt_id: int
    seq_no: int
    # Accel
    ax: int
    ay: int
    az: int
    # Gyro
    gx: int
    gy: int
    gz: int
    flex: int
    bullets: int

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

