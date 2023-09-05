from __future__ import annotations
from bluepy import btle
from enum import Enum
from abc import ABC, abstractmethod
import logging
import time

BEETLE1_MAC = "D0:39:72:E4:8E:67"
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

    def __init__(self, mac_address: str):
        self.beetle = None
        self.mac_address = mac_address
        self.has_handshake_replied = False
        self.set_to_connect()

    """
    Private functions
    """

    def _init_handshake(self):
        self.service = self.beetle.getServiceByUUID(SERVICE_UUID)
        self.characteristic = self.service.getCharacteristics(forUUID=CHAR_UUID)[0]
        message = "h"
        self.characteristic.write(bytes(message, "utf-8"))
        self.poll_for_data(0.5, 0.5)

    def _complete_handshake(self):
        while(not self.has_handshake_replied):
            pass
        message = 'd'
        self.characteristic.write(bytes(message, "utf-8"))
        logging.info("Handshake success")

    """
    Others
    """

    def set_to_connect(self):
        logging.info("Setting to connect state")
        self.state = States.connect

    def set_to_receive(self):
        logging.info("Setting to receive state")
        self.state = States.receive

    def set_to_wait_ack(self):
        logging.info("Setting to ack state")
        self.state = States.ack

    def handshake(self):
        logging.info("Initiating handshake")
        self._init_handshake()
        self._complete_handshake()

    def initiate_program(self):

        while True:

            # logging.info(self.state)

            if self.state == States.connect:
                self.connect_ble()
                self.handshake()
                self.set_to_receive()
            elif self.state == States.receive:
                self.poll_for_data()
            elif self.state == States.ack:
                pass
            else:
                # Error handling
                pass



    def connect_ble(self):
        self.beetle = btle.Peripheral(self.mac_address)
        self.beetle.setDelegate(ReadDelegate(self))
        logging.info("Successfully connected to BLE")

    def poll_for_data(self, duration=0, time_interval=0):
        # if duration and time_interval:
            end_time = time.time() + duration
            while time.time() < end_time:
                if self.beetle.waitForNotifications(time_interval):
                    continue
        # else:
        #     self.beetle.waitForNotifications()

    def disconnect(self):
        self.beetle.disconnect()

class ReadDelegate(btle.DefaultDelegate):

    def __init__(self, beetle_instance):
        btle.DefaultDelegate.__init__(self)
        self.count = 0
        self.beetle = beetle_instance

    def handleNotification(self, cHandle, data):
        self.count +=1
        # logging.info("Received packet " + str(self.count) + ":", repr(data))
        logging.info("Received packet " + str(self.count) + ":" + str(repr(data)))
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
                self.beetle.has_handshake_replied = True
                logging.info("Setting flag to True")
            else:
                pass
        except:
            logging.info("Packet id not found")
            pass


if __name__ == "__main__":
    beetle = BEETLE1_MAC
    b = Beetle(beetle)
    logging.getLogger().setLevel(logging.INFO)
    try:
        b.initiate_program()
    finally:
        b.disconnect()


