from bluepy import btle
import keyboard

from packet import PacketId, GvPacket, RHandDataPacket
from state import State
from crc import custom_crc16, custom_crc32
from constants import *
from write import write_to_csv
from exceptions import DisconnectException, HandshakeException, PacketIDException, CRCException

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

        # Timers
        self.keep_alive_timer = 0
        self.prev_receive_timer = 0
        self.receive_timer = 0

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
    
    def wait_handshake_reply(self, timeout, start_time):
        while not self.handshake_replied:
            if time.time() - start_time > timeout:
                raise HandshakeException(message="Beetle handshake timed out.")
    

    """
    Others
    """

    def handshake(self, timeout=3):

        # Reset flags for redundancy
        self.handshake_replied = False
        self.handshake_complete = False

        start_time = time.time()

        print("Initiating handshake...")

        # Send a init over to beetle
        self.init_handshake()

        # Wait for reply. If timeout, restart connection protocol again
        self.wait_handshake_reply(timeout, start_time)
        
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

        """
            Uncomment this for keep alive
        """

        # Writes a keep alive 'x' byte to the beetle every second
        # elif (current_time - self.keep_alive_timer >= 0.1):
        #     self.characteristic.write(bytes('x', "utf-8"))
        #     self.keep_alive_timer = current_time

    def send_reload(self): # simulate reload action
        self.characteristic.write(bytes('r', "utf-8"))

    def disconnect(self) -> None:
        self.beetle.disconnect()

    def initiate_program(self): # Missing stats queue from main program

        last_press_time = 0
        self.keep_alive_timer = time.time()
        self.receive_timer = time.time()

        """Main function to run the program."""

        while True:

            current_time = time.time()

            # if current_time - self.keep_alive_timer >= 0.05:
            #     statistics = { self.beetle_id: 
            #                     {
            #                         'Connected': f"{bcolors.OKGREEN}Connected{bcolors.ENDC}" if self.ble_connected else f"Disconnected",
            #                         'Handshake': f"{bcolors.OKGREEN}Completed{bcolors.ENDC}" if self.handshake_complete else f"Waiting",
            #                         'Packets received': self.beetle.delegate.count if self.handshake_complete else 0,
            #                         'kbps': float(self.beetle.delegate.count * 20 * 8 / (1000 * (time.time() - self.start_timer))) if self.handshake_complete else 0,
            #                         'Packets fragmented': self.beetle.delegate.fragmented_count if self.handshake_complete else 0,
            #                         'Packets corrupted': self.beetle.delegate.corrupted_count if self.handshake_complete else 0
            #                     }
            #                 }

            #     stats_queue.put(statistics)

            self.keep_alive_timer = current_time


            try:                    

                if self.state == State.RECEIVE:

                    self.beetle.waitForNotifications(timeout=INTERVAL_RATE)

                elif self.state == State.CONNECT:

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
                    # This continuously checks if the beetle is still connected.
                    # But i have temporarily disabled it because it is not necessary,
                    # May interfere with reading packets on beetle end
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
        self.error_packetid_count = 0
        self.count = 0
        self.beetle = beetle_instance
        self.packet_buffer = b""
        self.seq_no = 0
        self.trigger_record = 0
        self.file_count = 0
        self.timer = 0

        # self.start = False
        self.last_press_time = 0

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
            # Check packet id
            if data[0] < 0 or data[0] > 5:
                raise PacketIDException()
            
            pkt_id = PacketId(data[0])  

            if (pkt_id == PacketId.GV_PKT):

                pass

            elif (pkt_id == PacketId.RHAND_PKT):
                
                pkt = struct.unpack('BBhhhhhhHB', data[:17])
                pkt_data = RHandDataPacket(*pkt)

                crc = struct.unpack('H', data[18:])[0]

                if crc != custom_crc16(data[:17]):
                    raise CRCException()

                # Resets error count
                self.error_packetid_count = 0

                # CRC is correct and button is pressed
                if not self.beetle.handshake_complete:
                    # pass
                    return

                if pkt_data.bullets == 1 and time.time() - self.last_press_time >= 0.5: 
                    # Assuming bullets == button for recording purposes
                    self.last_press_time = time.time()

                    if not self.trigger_record:
                        print("Action window triggered. Please perform action now.")
                        self.trigger_record = True

                    elif self.trigger_record:
                        print(f"Action saved. Time taken: {time.time()-self.timer}")
                        self.trigger_record = False
                        self.start = False
                        self.file_count += 1
                        self.count = 0
                        packets = self.beetle.packet_window
                        self.beetle.packet_window = []
                        write_to_csv(packets, self.file_count)

                if pkt_data.bullets == 0 and self.trigger_record:
                    self.start = True
                    self.count += 1
                    print(f"Right Hand Packet received successfully: {pkt_data}")

                    if self.count == 1:
                        self.timer = time.time()
                    if len(self.beetle.packet_window) <= RECORD_PACKETS_LIMIT:
                        self.beetle.packet_window.append(pkt_data)
                        # print(f"Packet window length: {len(self.beetle.packet_window)}")
                        # Record 200 packets into a csv file
                        # if len(self.beetle.packet_window) == RECORD_PACKETS_LIMIT: 
                            # print(f"Action saved. Time taken: {time.time()-self.timer}")
                            # self.file_count += 1
                            # self.trigger_record = False
                            # self.count = 0
                            # packets = self.beetle.packet_window
                            # self.beetle.packet_window = []
                            # write_to_csv(packets, self.file_count)

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
        except PacketIDException or AssertionError as e:
            # PacketId conversion failed
            print("Packet id not found.")
            # Accounting packet loss for action window
            # Can be modified to just track packet loss
            self.account_packet_loss()

            # If there are 5 consecutive packets that do not match the CRC, 
            # we assume that the packets are jumbled and we need to re-handshake
            self.track_corrupted_packets()
        except CRCException as e:
            # Since assertion error, it will send the ack of the previous frame
            # self.beetle.send_ack(self.seq_no) 

            print("CRC do not match, packet corrupted.")
            # Accounting packet loss for action window
            # Can be modified to just track packet loss
            self.account_packet_loss()

            # If there are 5 consecutive packets that do not match the CRC, 
            # we assume that the packets are jumbled and we need to re-handshake
            self.track_corrupted_packets()

        except btle.BTLEException as e: 
            # Error will be thrown if we try to ack but beetle is not connected
            # Should not have this error since we are able to catch it in the initiate program fn.
            print(f"Beetle error: {e}") 

        except Exception as e:
            print(f"Error occured: {e}")

    def track_corrupted_packets(self):
        self.error_packetid_count += 1
        if self.error_packetid_count >= 5:
            print("Packet fragmented and sequence is messed up. Re-handshaking...")
            self.error_packetid_count = 0
            self.beetle.set_to_connect()

    def is_packet_complete(self, data):
        return len(data) >= 20
    
    def account_packet_loss(self):
        if self.trigger_record: 
            self.beetle.packet_dropped += 1
            # append an empty data
            self.beetle.packet_window.append(RHandDataPacket(0,0,0,0,0,0,0,0,0,0)) 
    
        
    