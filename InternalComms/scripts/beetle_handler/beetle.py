from bluepy import btle

from packets import PacketId
from states import State
from constants import *

from time import time

class Beetle():

    def __init__(self, mac_address: str):
        
        # Properties
        self.beetle = None
        self.mac_address = mac_address

        # Flags
        self.ble_connected = False
        self.handshake_replied = False
        self.handshake_complete = False

        # Initialize
        self.set_to_connect()


    """
    Private functions
    """

    def _init_handshake(self):
        self.service = self.beetle.getServiceByUUID(SERVICE_UUID)
        self.characteristic = self.service.getCharacteristics(forUUID=CHAR_UUID)[0]
        message = 'h'
        self.characteristic.write(bytes(message, "utf-8"))
        self.receive_data(0.1, 0.1)

    def _complete_handshake(self):
        while(not self.handshake_replied):
            pass
        message = 'd'
        self.characteristic.write(bytes(message, "utf-8"))
        print("Handshake success")
        self.handshake_complete = True

    def _reset_flags(self):
        self.handshake_replied = False
        self.handshake_complete = False
        self.ble_connected = False
        self.set_to_connect()
    
    def _is_init_handshake_completed(self):
        return self.handshake_replied

    """
    Others
    """

    def set_to_connect(self):
        print("Setting to connect state")
        self.state = State.connect

    def set_to_receive(self):
        print("Setting to receive state")
        self.state = State.receive

    def set_to_wait_ack(self):
        print("Setting to ack state")
        self.state = State.ack

    def handshake(self, timeout=5):
        start_time = time()
        print("Initiating handshake...")

        self._init_handshake()

        while True:
            if time() - start_time > timeout:
                print(f"Handshake timed out after {timeout} seconds")
                raise btle.BTLEException(message="Timed out")
            # Check for the completion of _init_handshake
            if self._is_init_handshake_completed():
                break

        self._complete_handshake()

    def connect_ble(self, max_retries=3):
        for _ in range(max_retries):
            try: 
                if self.ble_connected:
                    print("Already connected")
                    return
                self.beetle = btle.Peripheral(self.mac_address)
                self.beetle.setDelegate(ReadDelegate(self))
                print("Successfully connected to BLE")
                self.ble_connected = True
                return
            except btle.BTLEException as e:
                print("Failed to connect to BLE")
            
    def receive_data(self, duration=10000000000, polling_interval=INTERVAL_RATE):

        end_time = time() + duration
        while time() < end_time:
            # Need to check again on the timeout, can be longer and recover the packets
            if self.beetle.waitForNotifications(timeout=polling_interval):
                continue

    def initiate_program(self):

        while True:

            try:
                if self.state == State.connect:

                    self.connect_ble()
                    self.handshake()
                    if self.handshake_complete: 
                        self.set_to_receive()

                elif self.state == State.receive:

                    self.receive_data()

                elif self.state == State.ack:
                    pass
                else:
                    # Error handling
                    pass

            except btle.BTLEException:
                print(f"Beetle with {self.mac_address} has disconnected")
                self.disconnect()
                self._reset_flags()
                self.set_to_connect()

    def disconnect(self):
        self.beetle.disconnect()

class ReadDelegate(btle.DefaultDelegate):

    def __init__(self, beetle_instance):
        btle.DefaultDelegate.__init__(self)
        self.count = 0
        self.beetle = beetle_instance
        self.packet_buffer = b""

    def handleNotification(self, cHandle, data):
        self.packet_buffer += data
        # take out first 20 bytes of packet
        # reset buffer to remaining bytes
        if self.is_packet_complete(self.packet_buffer):
            self.process_packet(self.packet_buffer[:20])
            self.packet_buffer = self.packet_buffer[20:]
            return
        
        # Discard packets that were sent before handshake
        self.packet_buffer = b""

    def process_packet(self, data):
        self.count +=1
        print("Received packet " + str(self.count) + ":" + str(repr(data)))
        try:
            pkt_id = PacketId(data[0])

            if (pkt_id == PacketId.GV_PKT):
                pass
            elif (pkt_id == PacketId.RHAND_PKT):
                pass
            elif (pkt_id == PacketId.LHAND_PKT):
                pass
            elif (pkt_id == PacketId.GAMESTATE_PKT):
                pass
            elif (pkt_id == PacketId.ACK_PKT):
                pass
            elif (pkt_id == PacketId.H_PKT):
                self.beetle.handshake_replied = True
                print("Setting flag to True")
            else:
                pass
        except:
            print("Packet id not found")
            pass

    def is_packet_complete(self, data):
        return len(data) >= 20