from multiprocessing import Process, Queue
from beetle import Beetle, bcolors
from constants import BEETLE_MACS, BEETLE1_MAC, BEETLE2_MAC, BEETLE3_MAC
import pandas as pd
import time
from tabulate import tabulate
            # 'Connected': f"{bcolors.OKGREEN}Connected{bcolors.ENDC}" if self.ble_connected else f"{bcolors.WARNING}Disconnected{bcolors.ENDC}",

statistics = {
    'Connected': [f"Disconnected", f"Disconnected", f"Disconnected"],
    'Handshake': [f"Waiting", f"Waiting", f"Waiting"],
    'Packets received': [0, 0, 0],
    'kbps': [0, 0, 0],
    'Packets fragmented': [0, 0, 0],
    'Packets corrupted': [0, 0, 0],
}

df = pd.DataFrame(statistics, index=[1, 2, 3])




# for mac in BEETLE_MACS:
#     beetle = Beetle(mac, beetle_id=beetle_id)
#     process = Process(target=beetle.initiate_program)
#     processes.append(process)
#     process.start()
#     beetle_id += 1

processes = []
queue_1 = Queue()
queue_2 = Queue()
queue_3 = Queue()

beetle_1 = Beetle(BEETLE1_MAC, beetle_id=1)
process_1 = Process(target=beetle_1.initiate_program, args=(queue_1,))
processes.append(process_1)

beetle_2 = Beetle(BEETLE2_MAC, beetle_id=2)
process_2 = Process(target=beetle_2.initiate_program, args=(queue_2,))
processes.append(process_2)

beetle_3 = Beetle(BEETLE3_MAC, beetle_id=3)
process_3 = Process(target=beetle_3.initiate_program, args=(queue_3,))
processes.append(process_3)


print(df)

try:
    process_1.start()
    process_2.start()
    process_3.start()

    while True:
        if not queue_1.empty():
            data = queue_1.get(timeout=0.1)
            # print(list(data.values())[0])
            df.iloc[0] = list(data.values())[0]

        if not queue_2.empty():
            data = queue_2.get(timeout=0.1)
            # print(list(data.values())[0])
            df.iloc[1] = list(data.values())[0]
        
        if not queue_3.empty():
            data = queue_3.get(timeout=0.1)
            # print(list(data.values())[0])
            df.iloc[2] = list(data.values())[0]

        print(tabulate(df, headers='keys', tablefmt='fancy_grid'))
    # for process in processes:
    #     process.join()
    


except KeyboardInterrupt:
    print("Terminating processes...")
    for process in processes:
        process.terminate()
    # for process in processes:
    #     process.join()

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