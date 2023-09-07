from __future__ import annotations
from bluepy import btle
from enum import Enum
from multiprocessing import Process, Queue
import logging
import time
import asyncio

BEETLE1_MAC = "D0:39:72:E4:8E:67"
BEETLE2_MAC = "D0:39:72:E4:8E:07"
BEETLE_MACS = [BEETLE1_MAC, BEETLE2_MAC]
SERVICE_UUID = "0000dfb0-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "0000dfb1-0000-1000-8000-00805f9b34fb"


"""
There should have 3 main states:
- Connecting/Reconnecting: 
    Automatically performs handshake operation and continues
    Should reset all flags that are used
- Waiting for packet:
    Automatically parse data and send to ssh/ultra96
    Sends ack back to beetle
- Waiting for ack:
    Sends gamestate to beetle
    Waiting for confirmation of packet sent, verify with sequence number
"""
class States(Enum):
    connect = 0
    receive = 1
    ack = 2

class Packet(Enum):
    GV_PKT = 0
    RHAND_PKT = 1
    LHAND_PKT = 2
    GAMESTATE_PKT = 3
    ACK_PKT = 4
    H_PKT = 5

class Beetle():

    def __init__(self, mac_address: str, access_queue: Queue):
        
        # Properties
        self.beetle = None
        self.mac_address = mac_address
        self.access_queue = access_queue

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
        message = "h"
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
        self.state = States.connect

    def set_to_receive(self):
        print("Setting to receive state")
        self.state = States.receive

    def set_to_wait_ack(self):
        print("Setting to ack state")
        self.state = States.ack

    def handshake(self, timeout=5):
        start_time = time.time()
        print("Initiating handshake...")

        self._init_handshake()

        while True:
            if time.time() - start_time > timeout:
                print("Handshake timed out after", timeout, "seconds")
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
            
    def receive_data(self, duration=0, time_interval=0):

        end_time = time.time() + duration
        while time.time() < end_time:
            if self.beetle.waitForNotifications(time_interval):
                continue

    def initiate_program(self):

        while True:

            try:
                if self.state == States.connect:
                    self.access_queue.put(self.mac_address)
                    self.connect_ble()
                    self.handshake()
                    if self.handshake_complete: 
                        self.set_to_receive()
                    self.access_queue.get()
                elif self.state == States.receive:
                    self.access_queue.put(self.mac_address)
                    self.receive_data(duration=500, time_interval=0.05)
                    self.access_queue.get()
                elif self.state == States.ack:
                    pass
                else:
                    # Error handling
                    pass
            except btle.BTLEException:
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
        if self.is_packet_complete(self.packet_buffer):
            self.process_packet(data)
            self.packet_buffer = b""

    def process_packet(self, data):
        self.count +=1
        print("Received packet " + str(self.count) + ":" + str(repr(data)))
        try:
            pkt_id = Packet(data[0])

            if (pkt_id == Packet.GV_PKT):
                pass
            elif (pkt_id == Packet.RHAND_PKT):
                pass
            elif (pkt_id == Packet.LHAND_PKT):
                pass
            elif (pkt_id == Packet.GAMESTATE_PKT):
                pass
            elif (pkt_id == Packet.ACK_PKT):
                pass
            elif (pkt_id == Packet.H_PKT):
                self.beetle.handshake_replied = True
                print("Setting flag to True")
            else:
                pass
        except:
            print("Packet id not found")
            pass

    def is_packet_complete(self, data):
        return len(data) == 20



if __name__ == "__main__":

    access_queue = Queue()
    processes = []

    for mac in BEETLE_MACS:
        beetle = Beetle(mac, access_queue)
        process = Process(target=beetle.initiate_program)
        processes.append(process)
        process.start()

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("Terminating processes...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.join()

# Notes from TA:
# Threads can identify packet id
# alternate seq number between 0 and 1 can alr, donnid 255
# Packet header needs to be length of the packet
# multiprocessing allows queues 
