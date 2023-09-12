# from bluepy import btle 

# # Beetle 1: D0:39:72:E4:8E:67
# beetle1 = "D0:39:72:E4:8E:67"
# fakebeetle = "D0:39:72:E4:8E:68"

# def bleConnect(beetle):
#     try: 
#         p = btle.Peripheral(beetle)
#         print("Success!")
#         print(p)
#     except:
#         print("Could not connect.")

# bleConnect(beetle1)
# bleConnect(fakebeetle)
# from bluepy import btle

# beetle1 = "D0:39:72:E4:8E:67"

# def bleConnect(beetle):
#     try:
#         p = btle.Peripheral(beetle)
#         print("Connection successful with details:")
#         print(p)
#     except:
#         print("Unable to connect to beetle")
#         # Error handling - timeout

# bleConnect(beetle1)

# # setDelegate
# # waitForNotifications 

# from beetle_handler.crc import custom_crc32
# from beetle_handler.crc import custom_crc16

# # Calculate CRC32 and CRC16 checksums
# data = b'\x00\x01\x00\x00\x00\x01'
# crc32_result = custom_crc32(data)
# # crc16_result = crc16_func(data)

# print(f"CRC32: {crc32_result}")
# # print(f"CRC16: {crc16_result:04X}")


def custom_crc32(data):
    crc = 0x00000000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x04C11DB7 if crc & 1 else crc >> 1
    return crc  # XOR with 0xFFFFFFFF to ensure remainder is 0

def encode_crc32(data):
    crc = custom_crc32(data)
    return data + crc.to_bytes(4, byteorder='big')

def decode_crc32(data_with_crc):
    # Separate the data and received CRC value
    data_length = len(data_with_crc) - 4
    received_crc = int.from_bytes(data_with_crc[-4:], byteorder='big')
    received_data = data_with_crc[:data_length]

    # Calculate the CRC over the received data
    crc = 0x00000000
    for byte in received_data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x04C11DB7 if crc & 1 else crc >> 1

    # Check if the calculated CRC is equal to 0
    if crc == received_crc:
        return received_data  # Data is valid
    else:
        return None  # Data may be corrupted

# Example usage:
original_data = b'YourDataToEncode'
encoded_data = encode_crc32(original_data)
decoded_data = decode_crc32(encoded_data)
if decoded_data is not None:
    print("Data is valid:", decoded_data.decode('utf-8'))
else:
    print("Data may be corrupted.")