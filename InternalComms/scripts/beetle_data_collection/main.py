from multiprocessing import Process
from beetle import Beetle
from constants import BEETLE_MACS, BEETLE1_MAC, BEETLE2_MAC, BEETLE3_MAC

if __name__ == "__main__":

    # processes = []

    # for mac in BEETLE_MACS:
    #     beetle = Beetle(mac)
    #     process = Process(target=beetle.initiate_program)
    #     processes.append(process)
    #     process.start()

    # try:
    #     for process in processes:
    #         process.join()
    # except KeyboardInterrupt:
    #     print("Terminating processes...")
    #     for process in processes:
    #         process.terminate()
    #     for process in processes:
    #         process.join()

    try:
        beetle = Beetle(BEETLE3_MAC)
        beetle.initiate_program()
    except KeyboardInterrupt:
        print("Stopping...")

# Notes from TA:
# Threads can identify packet id
# alternate seq number between 0 and 1 can alr, donnid 255
# Packet header needs to be length of the packet
# multiprocessing allows queues 