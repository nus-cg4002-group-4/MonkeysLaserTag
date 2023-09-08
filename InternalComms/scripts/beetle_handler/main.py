from multiprocessing import Process
from beetle import Beetle
from constants import BEETLE_MACS

if __name__ == "__main__":

    processes = []

    for mac in BEETLE_MACS:
        beetle = Beetle(mac)
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

    # beetle = Beetle(BEETLE2_MAC, access_queue=access_queue)
    # beetle.initiate_program()

# Notes from TA:
# Threads can identify packet id
# alternate seq number between 0 and 1 can alr, donnid 255
# Packet header needs to be length of the packet
# multiprocessing allows queues 