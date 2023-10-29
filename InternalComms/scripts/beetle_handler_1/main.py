from multiprocessing import Process, Queue
from beetle import Beetle, bcolors
from constants import BEETLE_MACS, BEETLE1_MAC, BEETLE2_MAC, BEETLE3_MAC, BEETLE4_MAC
import pandas as pd
import time
from tabulate import tabulate
import json

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

dummy_node_to_imu = Queue()
dummy_node_to_vest = Queue()

beetle_1 = Beetle(BEETLE4_MAC, beetle_id=1)
process_1 = Process(target=beetle_1.initiate_program, args=(queue_1, dummy_node_to_imu))
processes.append(process_1)

beetle_2 = Beetle(BEETLE1_MAC, beetle_id=2)
process_2 = Process(target=beetle_2.initiate_program, args=(queue_2, dummy_node_to_vest))
processes.append(process_2)

# beetle = Beetle(BEETLE3_MAC, beetle_id=1)
# process_2 = Process(target=beetle.initiate_program, args=(queue_1, dummy_node_to_imu))
# processes.append(process_2)

getDictP1 = {"player_id": 1, "action": "gun", "game_state": {"p1": {"hp": 100, "bullets": 0, "grenades": 2, "shield_hp": 30, "deaths": 0, "shields": 3}, "p2": {"hp": 99, "bullets": 6, "grenades": 2, "shield_hp": 0, "deaths": 1, "shields": 3}}}

try:
    process_1.start()
    process_2.start()

    current_time = time.time()

    while True:



        if time.time() - current_time > 3:
            hp = "shield_hp"

            if (getDictP1["game_state"]["p1"]["shield_hp"] <= 0): hp = "hp"
            # if (getDictP1["game_state"]["p1"]["shield_hp"]) <= 0: 
            #     getDictP1["game_state"]["p1"]["shield_hp"] = 30
            # else: 
            getDictP1["game_state"]["p1"][hp] -= 10
            print(getDictP1["game_state"]["p1"][hp])
            dummy_node_to_vest.put(json.dumps(getDictP1))
            current_time = time.time()
        # if not queue_1.empty():
        #     data = queue_1.get(timeout=0.1)
        #     # print(list(data.values())[0])
        #     df.iloc[0] = list(data.values())[0]

        # if not queue_2.empty():
        #     data = queue_2.get(timeout=0.1)
        #     # print(list(data.values())[0])
        #     df.iloc[1] = list(data.values())[0]

        # print(tabulate(df, headers='keys', tablefmt='fancy_grid'))
        # if not dummy_node_to_imu.empty(): print(dummy_node_to_imu.get(timeout=0.1))


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