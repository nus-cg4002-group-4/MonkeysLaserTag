# These checksums mimics the library used in Arduino
# Package library referenced from: CRC (Rob Tillaart) https://github.com/RobTillaart/CRC/
# Translated by Weida to python

def custom_crc16(data):
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8001 if crc & 1 else crc >> 1
    return crc

def custom_crc32(data):
    crc = 0x00000000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x04C11DB7 if crc & 1 else crc >> 1
    return crc
