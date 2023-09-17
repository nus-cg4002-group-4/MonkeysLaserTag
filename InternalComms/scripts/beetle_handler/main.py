from multiprocessing import Process
from beetle import Beetle
from constants import BEETLE_MACS, BEETLE1_MAC, BEETLE2_MAC, BEETLE3_MAC
import pandas as pd


data = {'Connected', 'Handshake', 'Packets received', 'Speed' }

processes = []

beetle_1 = Beetle(BEETLE1_MAC, beetle_id=1)
process_1 = Process(target=beetle_1.initiate_program)
processes.append(process_1)
process_1.start()

# beetle_2 = Beetle(BEETLE2_MAC, beetle_id=2)
# process_2 = Process(target=beetle_2.initiate_program)
# processes.append(process_2)
# process_2.start()

# beetle_3 = Beetle(BEETLE3_MAC, beetle_id=3)
# process_3 = Process(target=beetle_3.initiate_program)
# processes.append(process_3)
# process_3.start()

# for mac in BEETLE_MACS:
#     beetle = Beetle(mac, beetle_id=beetle_id)
#     process = Process(target=beetle.initiate_program)
#     processes.append(process)
#     process.start()
#     beetle_id += 1

try:
    for process in processes:
        process.join()
except KeyboardInterrupt:
    print("Terminating processes...")
    for process in processes:
        process.terminate()
    for process in processes:
        process.join()

# try:
#     beetle = Beetle(BEETLE3_MAC, 1)
#     beetle.initiate_program()
# except KeyboardInterrupt:
#     if beetle.ble_connected: 
#         beetle.disconnect()
#     print("Stopping...")

# Notes from TA:
# Threads can identify packet id
# alternate seq number between 0 and 1 can alr, donnid 255
# Packet header needs to be length of the packet
# multiprocessing allows queues 