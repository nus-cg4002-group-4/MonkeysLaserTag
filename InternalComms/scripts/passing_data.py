import time
from bluepy import btle
import struct

class Beetle():

    # Seems like we have to hardcode these
    # Service UUID: 0000dfb0-0000-1000-8000-00805f9b34fb
    # Characteristic UUID: 0000dfb2-0000-1000-8000-00805f9b34fb

    def __init__(self, mac_address: str):
        self.mac_address = mac_address

    # For debugging and setting up purposes:
    def _find_service_and_characteristics(self):
        for service in self.beetle.getServices():
            for characteristic in service.getCharacteristics():
                if characteristic.supportsRead():
                    print("Service UUID:", service.uuid)
                    print("Characteristic UUID:", characteristic.uuid)
                    message = "hello from ubuntu"
                    characteristic.write(bytes(message, "utf-8"))
                    print("Message sent:", message)
        self.poll_for_data(2, 1.0)

    def _handshake(self, service_uuid, char_uuid):
        # Debugging purposes:
        # self._find_service_and_characteristics()

        # Actual handshake process:
        self.service = self.beetle.getServiceByUUID(service_uuid)
        characteristic = self.service.getCharacteristics(forUUID=char_uuid)[0]
        message = "hello from ubuntu"
        characteristic.write(bytes(message, "utf-8"))
        print("Message sent:", message)
        self.poll_for_data(2, 1.0)

    def connect(self):
        # try:
            self.beetle = btle.Peripheral(self.mac_address)
            self.beetle.setDelegate(ReadDelegate())

            self._handshake(
                service_uuid="0000dfb0-0000-1000-8000-00805f9b34fb", 
                char_uuid="0000dfb1-0000-1000-8000-00805f9b34fb"
                )
        # except:
        #     print("Beetle connection failed. Check MAC address again")

    def poll_for_data(self, duration, time_interval):
        end_time = time.time() + duration
        while time.time() < end_time:
            if self.beetle.waitForNotifications(time_interval):
                continue
            print("Waiting")

    def disconnect(self):
        self.beetle.disconnect()

class ReadDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print("Handling notification")
        print("Raw data:", repr(data))

        # if len(data) >= 1:
        #     print(struct.unpack("b", data))
        # else:
        #     print("Received data buffer is too short.")

if __name__ == "__main__":
    beetle1_MAC = "D0:39:72:E4:8E:67"
    b = Beetle(beetle1_MAC)
    try:
        b.connect()
    finally:
        b.disconnect()


