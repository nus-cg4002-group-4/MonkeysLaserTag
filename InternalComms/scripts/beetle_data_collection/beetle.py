from bluepy import btle

from packet import PacketId, GvPacket, RHandDataPacket
from state import State
from crc import custom_crc16, custom_crc32
from constants import *
from write import write_to_csv

import time
import struct

class Beetle():

    def __init__(self, mac_address: str):
        
        # Properties
        self.beetle = None
        self.mac_address = mac_address
        self.busy_processing = False
        self.packet_dropped = 0
        self.packet_window = []

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
        self.receive_data(0.2, 0.1)

    def complete_handshake(self):
        while(not self.handshake_replied):
            pass
        message = HANDSHAKE_MSG_ACK
        self.characteristic.write(bytes(message, "utf-8"))
        print("Handshake successful!")
        self.handshake_complete = True

    def _reset_flags(self):
        self.handshake_replied = False
        self.handshake_complete = False
        self.ble_connected = False
    
    def is_init_handshake_completed(self):
        return self.handshake_replied

    """
    Others
    """

    def set_to_connect(self):
        print("Setting to connect state")
        self.state = State.connect

    def set_to_receive(self):
        print("Setting to receive state, ready to receive data.")
        self.state = State.receive

    def set_to_wait_ack(self):
        print("Setting to ack state")
        self.state = State.ack

    def handshake(self, timeout=3):
        start_time = time.time()
        print("Initiating handshake...")

        self.init_handshake()

        while True:
            if time.time() - start_time > timeout:
                print(f"Handshake timed out after {timeout} seconds")
                raise btle.BTLEException(message="Timed out")
            # Check for the completion of _init_handshake
            if self.is_init_handshake_completed():
                break

        self.complete_handshake()

    def connect_ble(self, max_retries=3):
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
            
    def receive_data(self, duration=10000000000, polling_interval=INTERVAL_RATE):

        end_time = time.time() + duration
        # Reminder to use this to break the loop
        while time.time() < end_time:
            # Need to check again on the timeout, can be longer and recover the packets
            if self.beetle.waitForNotifications(timeout=polling_interval):
                continue

    def send_ack(self, seq_no) -> None:
        self.characteristic.write(bytes(str(seq_no), "utf-8"))

    def disconnect(self) -> None:
        self.beetle.disconnect()

    def initiate_program(self):

        while True:

            try:
                if self.state == State.connect:
                    self._reset_flags()
                    self.connect_ble()
                    self.handshake()
                    if self.handshake_complete: 
                        self.set_to_receive()

                elif self.state == State.receive:

                    if not self.busy_processing:
                        self.receive_data()
                else:
                    # Raise error and reconnect
                    raise btle.BTLEException
                

            except btle.BTLEException as e:
                print(f"Beetle with {self.mac_address} has disconnected")
                print(f"{e}")
                self.disconnect()
                self._reset_flags()
                self.set_to_connect()


class ReadDelegate(btle.DefaultDelegate):

    def __init__(self, beetle_instance):
        btle.DefaultDelegate.__init__(self)
        self.error_packetid_count = 0
        self.count = 0
        self.beetle = beetle_instance
        self.packet_buffer = b""
        self.seq_no = 0
        self.trigger_record = 0
        self.file_count = 0
        self.timer = 0

    def handleNotification(self, cHandle, data):
        
        # Append data to buffer
        self.packet_buffer += data

        if self.is_packet_complete(self.packet_buffer):
            # take out first 20 bytes of packet
            self.process_packet(self.packet_buffer[:20])
            # reset buffer to remaining bytes
            self.packet_buffer = self.packet_buffer[20:]

    def process_packet(self, data):
        # print("Received packet " + str(struct.unpack('B', data[1:2])) + ":" + str(repr(data)))
        try:
            pkt_id = PacketId(data[0])
            if (pkt_id == PacketId.GV_PKT):

                pass

                # pkt = struct.unpack('BBBBBB', data[:6])
                # pkt_data = GvPacket(*pkt)
                
                # crc = struct.unpack('I', data[16:])[0]
                # assert crc == custom_crc32(data[:6])
                
                # # Update sequence number afterwards to send ack
                # self.seq_no = pkt_data.seq_no
                # if self.beetle.handshake_complete:
                #     self.beetle.send_ack(self.seq_no)
                #     print(f"Ack sent for {self.seq_no}")

                # # TODO: Write data to ssh server

                # print(f"GvPacket received successfully: {pkt_data}")

            elif (pkt_id == PacketId.RHAND_PKT):
                
                pkt = struct.unpack('BBhhhhhhHB', data[:17])
                pkt_data = RHandDataPacket(*pkt)

                crc = struct.unpack('H', data[18:])[0]

                assert crc == custom_crc16(data[:17])

                # Resets error count
                self.error_packetid_count = 0

                # CRC is correct and button is pressed
                if pkt_data.bullets == 1 and self.beetle.handshake_complete: 
                    # Assuming bullets == button for recording purposes
                    if not self.trigger_record: # Print it once only
                        print("Action window triggered. Please perform action now.")
                    self.trigger_record = True

                if self.trigger_record:
                    # print(f"Right Hand Packet received successfully: {pkt_data}")
                    self.count += 1
                    if self.count == 1:
                        self.timer = time.time()
                    if len(self.beetle.packet_window) <= RECORD_PACKETS_LIMIT:
                        self.beetle.packet_window.append(pkt_data)
                        # print(f"Packet window length: {len(self.beetle.packet_window)}")
                        # Record 200 packets into a csv file
                        if len(self.beetle.packet_window) == RECORD_PACKETS_LIMIT: 
                            print(f"Action saved. Time taken: {time.time()-self.timer}")
                            self.file_count += 1
                            self.trigger_record = False
                            self.count = 0
                            packets = self.beetle.packet_window
                            self.beetle.packet_window = []
                            write_to_csv(packets, self.file_count)

                # TODO: Write data to ssh server

            elif (pkt_id == PacketId.LHAND_PKT):
                pass
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
        except AssertionError as e:
            # Since assertion error, it will send the ack of the previous frame
            # self.beetle.send_ack(self.seq_no) 

            self.account_packet_loss()

            self.error_packetid_count += 1
            if self.error_packetid_count >= 5:
                print("Packet fragmented and sequence is messed up. Please restart application")
                self.error_packetid_count = 0

            print("CRC do not match, packet corrupted.")
        except btle.BTLEException as e: 
            # Error will be thrown if we try to ack but beetle is not connected
            print(f"Beetle error: {e}") 
        # PacketId conversion failed
        except ValueError as e:
            self.account_packet_loss()

            self.error_packetid_count += 1
            if self.error_packetid_count >= 5:
                print("Packet fragmented and sequence is messed up. Please restart application")
                self.error_packetid_count = 0

        except Exception as e:
            print(f"Error occured: {e}")

    def is_packet_complete(self, data):
        return len(data) >= 20
    
    def account_packet_loss(self):
        if self.trigger_record: 
            self.beetle.packet_dropped += 1
            # append an empty data
            self.beetle.packet_window.append(RHandDataPacket(0,0,0,0,0,0,0,0,0,0)) 
    
        
    