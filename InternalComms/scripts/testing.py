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

from beetle_handler.crc import custom_crc32
from beetle_handler.crc import custom_crc16

# Calculate CRC32 and CRC16 checksums
data = b'\x00\x01\x00\x00\x00\x01'
crc32_result = custom_crc32(data)
# crc16_result = crc16_func(data)

print(f"CRC32: {crc32_result}")
# print(f"CRC16: {crc16_result:04X}")