from bluepy import btle
import keyboard

from packet import PacketId, VestPacket, RHandDataPacket
from state import State
from crc import custom_crc16, custom_crc32
from write import write_to_csv
from exceptions import DuplicateException, HandshakeException, PacketIDException, CRCException
from constants import *

from dataclasses import asdict
import pandas as pd
import sys
import time
import struct
from tabulate import tabulate
from multiprocessing import Queue
import json
import math

SHIELD = 'k'
HEALTH = 'l'

AX_THRESHOLD = 200000
AY_THRESHOLD = 200000
AZ_THRESHOLD = 200000

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Beetle():

    def __init__(self, mac_address: str, beetle_id: int=0):
        
        # Properties
        self.beetle_id = beetle_id
        self.beetle = None
        self.mac_address = mac_address
        
        # Acknowledgements
        self.ack_shield_value = 0
        self.ack_health_value = 0

        # Data Collection purposes
        self.packet_dropped = 0
        self.packet_window = []

        # Timers
        self.statistics_timer = 0
        self.receive_timer = 0

        # Flags
        self.ble_connected = False
        self.handshake_replied = False
        self.handshake_complete = False

        # Flags for gamestate
        self.sent_health = False
        self.sent_shield = False

        # Initialize
        self.set_to_connect()

    def init_handshake(self):
        self.service = self.beetle.getServiceByUUID(SERVICE_UUID)
        self.characteristic = self.service.getCharacteristics(forUUID=CHAR_UUID)[0]
        message = HANDSHAKE_MSG_INIT
        self.characteristic.write(bytes(message, "utf-8"))
        self.receive_data()

    def complete_handshake(self):
        message = HANDSHAKE_MSG_ACK
        self.characteristic.write(bytes(message, "utf-8"))
        self.handshake_complete = True
        print("Handshake successful!")

    def reset_flags(self):
        self.handshake_replied = False
        self.handshake_complete = False
        self.ble_connected = False
        self.sent_health = False
        self.sent_shield = False
        self.sent_reload = False

    def handshake(self, timeout=3):

        # Reset flags for redundancy
        self.handshake_replied = False
        self.handshake_complete = False

        print("Initiating handshake...")

        # Send a init over to beetle
        self.init_handshake()
        
        # Send ack and complete handshake
        self.complete_handshake()

    def connect_ble(self, max_retries=20):
        for _ in range(max_retries):
            try: 
                if self.ble_connected:
                    print("Already connected")
                    return
                self.beetle = btle.Peripheral(self.mac_address)
                self.beetle.setDelegate(ReadDelegate(self))
                print(f"Successfully connected to {self.mac_address}")
                self.ble_connected = True
                return
            except btle.BTLEException as e:
                print(f"Failed to connect to {self.mac_address}")
            
    def receive_data(self, duration=3, polling_interval=INTERVAL_RATE):

        end_time = time.time() + duration
        while time.time() < end_time:
            if self.handshake_replied:
                return
            self.beetle.waitForNotifications(timeout=polling_interval)
        
        raise HandshakeException("Handshake timed out.")
                

    def send_ack(self, seq_no) -> None:
        self.characteristic.write(bytes(str(seq_no), "utf-8"))

    def on_keypress(self, key: str, fn):
        current_time = time.time()
        if keyboard.is_pressed(key):
            if current_time - self.last_press_time >= 1:
                print(f'{key} pressed!')
                self.last_press_time = current_time
                fn() # execute fn

    def try_writing_to_beetle(self, data: str):
        if self.handshake_complete:
            getDict = json.loads(data)

            # "{\"player_id\": 1, \"action\": \"reload\", \"game_state\": {\"p1\": {\"hp\": 100, \"bullets\": 6, \"grenades\": 2, \"shield_hp\": 0, \"deaths\": 0, \"shields\": 3}, \"p2\": {\"hp\": 100, \"bullets\": 6, \"grenades\": 2, \"shield_hp\": 0, \"deaths\": 0, \"shields\": 3}}}"
            
            print("getDict action: ", getDict['action'])

            if self.beetle_id == 1 and getDict['action'] == 'reload' and self.beetle.delegate.bullets == 0:
                self.send_reload()
            elif self.beetle_id == 2:
                self.send_shield(getDict['gamestate']['p2']['shield_hp'])
                self.send_health(getDict['gamestate']['p2']['hp'])
    
    # def try_writing_to_beetle(self):
    #     self.on_keypress("h", self.send_health)
    #     self.on_keypress("j", self.send_shield)
    #     self.on_keypress("r", self.send_reload)

    def send_reload(self): # simulate reload action
        print(f"{bcolors.OKBLUE}Reloading for {self.beetle_id}{bcolors.ENDC}")
        self.characteristic.write(bytes('r', "utf-8"))
        self.sent_reload = True
    
    def send_shield(self, value): # simulate gamestate update
        # Invoke gamestate to receive data for gamestate in beetle
        self.emit_gamestate(type=SHIELD, value=value)
        self.ack_shield_value = value
        self.sent_shield = True

    def send_health(self, value): # simulate gamestate update
        # Invoke gamestate to receive data for gamestate in beetle
        self.emit_gamestate(type=HEALTH, value=value)
        self.ack_health_value = value
        self.sent_health = True

    def emit_gamestate(self, type, value):
        self.characteristic.write(bytes(f'g', "utf-8"))
        self.characteristic.write(bytes(str(type), "utf-8"))
        self.characteristic.write(bytes(str(value), "utf-8"))
        self.ack_gamestate_timer = time.time()

    def disconnect(self) -> None:
        self.beetle.disconnect()

    def initiate_program(self, 
                         node_to_server: Queue,
                         node_from_server: Queue
                         #stats_queue: Queue
                         ):
        """Main function to run the program."""
        
        # Initiate the node to send to server
        self.node_to_server = node_to_server

        # Used for keyboard events
        self.last_press_time = time.time()

        # Used for statistics
        self.statistics_timer = time.time()

        # Used for beetle's automatic re-connection
        self.receive_timer = time.time()

        # Used for acknowledgements
        self.ack_gamestate_timer = time.time()

        while True:

            current_time = time.time()

            if current_time - self.statistics_timer >= 0.05:
                statistics = { self.beetle_id: 
                                {
                                    'Connected': f"{bcolors.OKGREEN}Connected{bcolors.ENDC}" if self.ble_connected else f"Disconnected",
                                    'Handshake': f"{bcolors.OKGREEN}Completed{bcolors.ENDC}" if self.handshake_complete else f"Waiting",
                                    'Packets received': self.beetle.delegate.count if self.handshake_complete else 0,
                                    'kbps': float(self.beetle.delegate.count * 20 * 8 / (1000 * (time.time() - self.start_timer))) if self.handshake_complete else 0,
                                    'Packets fragmented': self.beetle.delegate.fragmented_count if self.handshake_complete else 0,
                                    'Packets corrupted': self.beetle.delegate.corrupted_count if self.handshake_complete else 0
                                }
                            }

                # stats_queue.put(statistics) # Right now, stats queue is offline

                self.statistics_timer = current_time
            
            try:
                if self.handshake_complete and time.time() - self.receive_timer >= 3:
                    self.set_to_connect()

                if self.state == State.RECEIVE:

                    self.beetle.waitForNotifications(timeout=INTERVAL_RATE)

                elif self.state == State.CONNECT:
                    if self.ble_connected:
                        self.disconnect()
                    self.reset_flags()
                    self.connect_ble()

                    # Redundant check but hopefully it will prevent unforeseen errors
                    if self.ble_connected:
                        self.set_to_handshake()

                elif self.state == State.HANDSHAKE:
                    
                    self.handshake()

                    # Redundant check but hopefully it will prevent unforeseen errors
                    if self.handshake_complete: 
                        self.set_to_receive()

                else:
                    # Raise error and reconnect
                    raise btle.BTLEException(message="Invalid state.")
                
                # To simulate receiving an item in queue
                # If event occurs and handshake is complete, try writing to beetle
                if self.handshake_complete:

                    # Attempt to event to beetle
                    if not node_from_server.empty():
                        data = node_from_server.get()
                        self.try_writing_to_beetle(data)

                    # Simulate if shield, health or reload is not updated properly
                    self.check_gamestate_sent(current_time)

            except HandshakeException as e:
                print(f"{e}")
                print(f"Restarting HANDSHAKE for {self.mac_address}")
                self.set_to_handshake()   

            except btle.BTLEException as e:
                print(f"BTLEException: {e}")
                print(f"Restarting CONNECT for {self.mac_address}")
                self.disconnect()
                self.reset_flags()
                self.set_to_connect()

    def check_gamestate_sent(self, current_time):
        if current_time - self.ack_gamestate_timer >= 0.7:
            if self.sent_shield:
                if self.beetle.delegate.shield != self.ack_shield_value:
                    self.send_shield()
                else:
                    self.sent_shield = False
                        
            if self.sent_health:
                if self.beetle.delegate.health != self.ack_health_value:
                    self.send_health()
                else:
                    self.sent_health = False

            if self.sent_reload:
                if self.beetle.delegate.bullets != 6:
                    self.send_reload()
                else:
                    self.sent_reload = False
    
    def set_to_connect(self):
        print("Setting to connect state")
        self.state = State.CONNECT

    def set_to_handshake(self):
        self.state = State.HANDSHAKE

    def set_to_receive(self):
        print("Setting to receive state, ready to receive data.")
        self.state = State.RECEIVE

class ReadDelegate(btle.DefaultDelegate):

    def __init__(self, beetle_instance):
        btle.DefaultDelegate.__init__(self)
        self.count = 0
        self.beetle = beetle_instance

        self.ack_count = 0

        # Keeps track of the sequence number sent for vestpackets
        self.seq_no = -1
        self.corrupted_packet_counter = 0
        self.corrupted_count = 0
        self.trigger_record = 0 # For data collection purposes

        # Handling fragmented packets
        self.packet_buffer = b""
        self.total_calls = 0
        self.fragmented_count = 0
        # Fragmented count = total calls to handleNotifications - number of times packet is processed
        self.shield = 0
        self.health = 0

        self.prev_button_press = 0
        self.prev_hit = 0

        self.last_10_packets = []
        self.accel_sums: list(int) = [0, 0, 0] # ax, ay, az
        self.old_accel_sums = [0, 0, 0]
        self.send_to_ext = False
        self.add_to_queue = False

    def handleNotification(self, cHandle, data):
        if self.total_calls == 0: 
            self.beetle.start_timer = time.time()
            self.bullets = 6

        self.beetle.receive_timer = time.time() # Update current time

        self.total_calls += 1
        
        # Append data to buffer
        self.packet_buffer += data

        if self.is_packet_complete(self.packet_buffer):
            # take out first 20 bytes of packet
            self.process_packet(self.packet_buffer[:20])
            # reset buffer to remaining bytes
            self.packet_buffer = self.packet_buffer[20:]

    def process_packet(self, data):

        # Statistics/debugging purposes
        # self.count += 1 # Number of packets processed
        self.fragmented_count = self.total_calls - self.count # Number of fragmented packets

        # print("Received packet " + str(struct.unpack('B', data[1:2])) + ":" + str(repr(data)))
        try:
            # Check packet id
            if data[0] < 1 or data[0] > 5:
                raise PacketIDException()
            
            pkt_id = PacketId(data[0])  

            if (pkt_id == PacketId.VEST_PKT):

                unprocessed_vest_data = data[:7]

                # = means native with no alignment, default is @ with alignment.
                pkt = struct.unpack('=BBBHH', unprocessed_vest_data)
                pkt_data = VestPacket(
                    *pkt
                )
                
                crc = struct.unpack('I', data[16:])[0]
                if crc != custom_crc32(unprocessed_vest_data):
                    raise CRCException()
                                
                if pkt_data.seq_no == self.seq_no:
                    # May receive packets while still handshaking
                    # Clears the buffer on the vest side 
                    self.beetle.send_ack(pkt_data.seq_no)
                    print(pkt_data)
                    raise DuplicateException()
                
                self.corrupted_packet_counter = 0

                # # Update sequence number afterwards to send ack
                self.seq_no = pkt_data.seq_no
                if self.beetle.handshake_complete:
                    self.beetle.send_ack(self.seq_no)

                # Check if packet received for Beetle() gamestate emissions
                self.shield = pkt_data.shield
                self.health = pkt_data.health

                if self.prev_hit and not pkt_data.ir_rcv and self.beetle.node_to_server:
                    print("Hit")
                    self.beetle.node_to_server.put({'pkt_id': 2, 'hit': 1}) # pkt_id = 2

                self.prev_hit = pkt_data.ir_rcv
                # print(f"VestPacket received successfully: {pkt_data}")

            elif (pkt_id == PacketId.RHAND_PKT):
                
                pkt = struct.unpack('BBhhhhhhHB', data[:17])
                pkt_data = RHandDataPacket(*pkt)

                crc = struct.unpack('H', data[18:])[0]

                if crc != custom_crc16(data[:17]):
                    raise CRCException()
                
                # Resets error count since packet received successfully
                self.corrupted_packet_counter = 0

                # print(f"{self.beetle.beetle_id}: \
                #       Right Hand Packet received successfully: {pkt_data}")

                # Convert pkt_data to a dictionary
                pkt_dict = asdict(pkt_data)

                # Convert dict_values to a list and then iterate to create AI_data
                AI_data = { 
                    key: value for key, value in pkt_dict.items() if key != 'button_press' and key != 'seq_no'
                }

                # print(AI_data)

                if self.prev_button_press == 1 and pkt_data.button_press == 0:
                    print("shot")
                    self.beetle.node_to_server.put({'pkt_id' : 3, 'button_press' : 1}) # pkt_id 3

                self.prev_button_press = pkt_data.button_press

                if self.beetle.handshake_complete:

                    self.last_10_packets.append(pkt_dict)

                    if len(self.last_10_packets) >= 10:

                        for pkt in self.last_10_packets:
                            self.accel_sums[0] += pkt['ax']
                            self.accel_sums[1] += pkt['ay']
                            self.accel_sums[2] += pkt['az']
                        
                        # perform comparison
                        dp = 1

                        # check that the first 10 packets are initialized first
                        if self.old_accel_sums[0] != 0:
                            dp = self.normalized_dot_product(self.accel_sums, self.old_accel_sums)
                            # print(dp)

                        if dp < 0.5 and not self.send_to_ext:
                            self.send_to_ext = True
                            self.add_to_queue = True
                            print("Sending to ext comms")
                        #reset
                        self.old_accel_sums = self.accel_sums
                        self.accel_sums = [0, 0, 0]

                        # do not reset the 10 packets if sending to ext comms, cos u wanna append it
                        if not self.add_to_queue:
                            self.last_10_packets = []

                    if self.send_to_ext:

                        # Append the first 10 packets that is the start of the action
                        if self.add_to_queue:
                            for pkt in self.last_10_packets:

                                prev_10_ai_data = { 
                                    key: value for key, value in pkt.items() if key != 'button_press' and key != 'seq_no'
                                }
                                self.beetle.node_to_server.put(prev_10_ai_data)
                                self.count += 1
                            self.add_to_queue = False

                        print(self.count)

                        self.beetle.node_to_server.put(AI_data) # pkt_id 1
                        self.count += 1

                        # Append the remaining 70 packets
                        if (self.count >= 80):
                            self.send_to_ext = False
                            self.count = 0
                            print("Sent 80 packets to ext comms")

            elif (pkt_id == PacketId.GAMESTATE_PKT):
                pass
            elif (pkt_id == PacketId.ACK_PKT):
                pass
            elif (pkt_id == PacketId.H_PKT):
                self.beetle.handshake_replied = True
            else:
                pass
        except struct.error as e:
            print(f"Struct cannot be unpacked: {e}")
        except PacketIDException or CRCException as e:

            self.corrupted_count += 1 # Statistics purposes

            # It will send the ack of the previous frame
            if self.beetle.beetle_id != 1: # ID of beetle for Glove, no ack
                self.beetle.send_ack(self.seq_no)
            
            # PacketId conversion failed
            print("Packet id not found/CRC Corrupted")
            # Accounting packet loss for action window
            # Can be modified to just track packet loss
            self.account_packet_loss()

            # If there are 5 consecutive packets that do not match the CRC/Packet ID, 
            # we assume that the packets are jumbled and we need to re-handshake
            self.track_corrupted_packets()
        except DuplicateException as e:
            print(f"Duplicated packet is dropped.")
            self.track_corrupted_packets()
        except btle.BTLEException as e: 
            # Error will be thrown if we try to ack but beetle is not connected
            # Should not have this error since we are able to catch it in the initiate program fn.
            print(f"Beetle error: {e}") 

        except Exception as e:
            print(f"Error occured: {e}")
            self.track_corrupted_packets

    def track_corrupted_packets(self):
        self.corrupted_packet_counter += 1
        if self.corrupted_packet_counter >= 5:
            print("Packets jumbled and sequence is messed up. Re-handshaking...")
            self.corrupted_packet_counter = 0
            self.beetle.set_to_connect()

    def is_packet_complete(self, data):
        return len(data) >= 20

    def account_packet_loss(self): 
        if self.trigger_record: 
            self.beetle.packet_dropped += 1
            # append an empty data
            self.beetle.packet_window.append(RHandDataPacket(0,0,0,0,0,0,0,0,0,0)) 
    
    def dataclass_to_dict(self, dataclass_instance, attribute):
        return {
            field.name: getattr(dataclass_instance, field.name)
            for field in dataclass_instance.__dataclass_fields__.values()
            if field.name in attribute
        }
    
    def normalized_dot_product(self, vec1, vec2):
        mag1 = math.sqrt(vec1[0]**2 + vec1[1]**2 + vec1[2]**2)
        mag2 = math.sqrt(vec2[0]**2 + vec2[1]**2 + vec2[2]**2)
        norm_vec1 = [v/mag1 for v in vec1]
        norm_vec2 = [v/mag2 for v in vec2]
        return norm_vec1[0]*norm_vec2[0] + norm_vec1[1]*norm_vec2[1] + norm_vec1[2]*norm_vec2[2]
    