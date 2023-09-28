from bluepy import btle
import keyboard

from packet import PacketId, VestPacket, RHandDataPacket
from state import State
from crc import custom_crc16, custom_crc32
from write import write_to_csv
from exceptions import DuplicateException, HandshakeException, PacketIDException, CRCException
from constants import *

import pandas as pd
import sys
import time
import struct
from tabulate import tabulate
from multiprocessing import Queue

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
        self.busy_processing = False

        # Data Collection purposes
        self.packet_dropped = 0
        self.packet_window = []

        # Timers
        self.keep_alive_timer = 0
        self.prev_receive_timer = 0
        self.receive_timer = 0

        # Flags
        self.ble_connected = False
        self.handshake_replied = False
        self.handshake_complete = False

        # Initialize
        self.set_to_connect()



    """
    Private functions
    """

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
        self.start_timer = 0


    """
    Others
    """

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
    
    def try_writing_to_beetle(self, last_press_time: time):
        """Dumps a BTLEException when there is a power loss"""
        
        current_time = time.time()

        # Temporary implementation of reload
        if keyboard.is_pressed("s"):
            if current_time - last_press_time >= 10:
                print('You Pressed s Key!')
                last_press_time = current_time
                self.send_reload()

        # Writes a keep alive 'x' byte to the beetle every second
        # elif (current_time - self.keep_alive_timer >= 0.1):
        #     self.characteristic.write(bytes('x', "utf-8"))
        #     self.keep_alive_timer = current_time

    def send_reload(self): # simulate reload action
        self.characteristic.write(bytes('r', "utf-8"))

    def disconnect(self) -> None:
        self.beetle.disconnect()

    def initiate_program(self, stats_queue: Queue):
        """Main function to run the program."""
        last_press_time = 0
        self.keep_alive_timer = time.time()
        self.receive_timer = time.time()

        while True:

            current_time = time.time()

            if current_time - self.keep_alive_timer >= 0.05:
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

                stats_queue.put(statistics)

                self.keep_alive_timer = current_time
            
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
                
                if self.handshake_complete:
                    self.try_writing_to_beetle(last_press_time)

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
    
    def set_to_connect(self):
        print("Setting to connect state")
        self.state = State.CONNECT

    def set_to_handshake(self):
        self.state = State.HANDSHAKE

    def set_to_receive(self):
        print("Setting to receive state, ready to receive data.")
        self.state = State.RECEIVE

    def set_to_wait_ack(self):
        print("Setting to ack state")
        self.state = State.ACK

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

    def handleNotification(self, cHandle, data):
        if self.total_calls == 0: 
            self.beetle.start_timer = time.time()

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
        self.count += 1 # Number of packets processed
        self.fragmented_count = self.total_calls - self.count # Number of fragmented packets

        # print("Received packet " + str(struct.unpack('B', data[1:2])) + ":" + str(repr(data)))
        try:
            # Check packet id
            if data[0] < 1 or data[0] > 5:
                raise PacketIDException()
            
            pkt_id = PacketId(data[0])  

            if (pkt_id == PacketId.VEST_PKT):

                pkt = struct.unpack('BBBB', data[:4])
                pkt_data = VestPacket(*pkt)
                
                crc = struct.unpack('I', data[16:])[0]
                if crc != custom_crc32(data[:4]):
                    raise CRCException()
                
                if pkt_data.seq_no == self.seq_no:
                    raise DuplicateException()
                
                # # Update sequence number afterwards to send ack
                self.seq_no = pkt_data.seq_no
                if self.beetle.handshake_complete:
                    self.beetle.send_ack(self.seq_no)

                # # TODO: Write data to ssh server

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
                
                # TODO: Write data to ssh server

            # elif (pkt_id == PacketId.LHAND_PKT):
            #     pass
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
            if self.beetle.beetle_id != 3: # ID of beetle for Glove, no ack
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
        except btle.BTLEException as e: 
            # Error will be thrown if we try to ack but beetle is not connected
            # Should not have this error since we are able to catch it in the initiate program fn.
            print(f"Beetle error: {e}") 

        except Exception as e:
            print(f"Error occured: {e}")

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
    
        
    