import time
from multiprocessing import Lock, Process, Queue, current_process
from beetle import Beetle, bcolors
from constants import BEETLE_MACS, BEETLE1_MAC, BEETLE2_MAC, BEETLE3_MAC, BEETLE4_MAC
import pandas as pd
import time
from tabulate import tabulate
            # 'Connected': f"{bcolors.OKGREEN}Connected{bcolors.ENDC}" if self.ble_connected else f"{bcolors.WARNING}Disconnected{bcolors.ENDC}",

from RelayNode import RelayNode
from BeetleJobs import BeetleJobs

statistics = {
    'Connected': [f"Disconnected", f"Disconnected", f"Disconnected"],
    'Handshake': [f"Waiting", f"Waiting", f"Waiting"],
    'Packets received': [0, 0, 0],
    'kbps': [0, 0, 0],
    'Packets fragmented': [0, 0, 0],
    'Packets corrupted': [0, 0, 0],
}

df = pd.DataFrame(statistics, index=[1, 2, 3])



class Brain:
    def __init__(self):
        self.processes = []

        self.send_to_server_process = None
        self.recv_from_server_process = None
        self.send_to_imu_process = None
        self.send_to_ir_process = None
        
        self.beetle_jobs = None

        self.node_to_server = Queue()
        self.node_to_imu = Queue()
        self.node_to_ir = Queue()

    def start_processes(self):
        try:
            # DEFINE JOBS
            self.beetle_jobs = BeetleJobs()
            self.beetle_jobs.relay_node = RelayNode()
            self.beetle_jobs.relay_node.connect_to_server()
            
            
            # DEFINE PROCESSES
            # Send To Server Process   
            self.send_to_server_process = Process(target=self.beetle_jobs.send_to_server_job, 
                                                args=(self.node_to_server,))
            self.processes.append(self.send_to_server_process)
            self.send_to_server_process.start()

            # Receive from Server Process   
            self.recv_from_server_process = Process(target=self.beetle_jobs.recv_from_server_job, 
                                                args=(self.node_to_imu, self.node_to_ir))
            self.processes.append(self.recv_from_server_process)
            self.recv_from_server_process.start()

            # Receive from IMU Process
            beetle_1 = Beetle(BEETLE1_MAC, beetle_id=1)
            process_1 = Process(target=beetle_1.initiate_program, args=(self.node_to_server, self.node_to_imu))
            self.processes.append(process_1)
            process_1.start()

            # Receive from IR Process
            beetle_2 = Beetle(BEETLE4_MAC, beetle_id=2)
            process_2 = Process(target=beetle_2.initiate_program, args=(self.node_to_server, self.node_to_ir))
            self.processes.append(process_2)
            process_2.start()

            # # Send to IMU Process
            # self.send_to_imu_process = Process(target=self.beetle_jobs.send_to_beetle_job, 
            #                                     args=(self.node_to_imu, beetle_1))
            # self.processes.append(self.send_to_imu_process)
            # self.send_to_imu_process.start()

            #  # Send to IR Process
            # self.send_to_ir_process = Process(target=self.beetle_jobs.send_to_beetle_job, 
            #                                     args=(self.node_to_ir, beetle_2))
            # self.processes.append(self.send_to_ir_process)
            # self.send_to_ir_process.start()

            # TODO: Format the data into required format + str
        
            for p in self.processes:
                p.join()
        except KeyboardInterrupt:
            print('Terminating Main')
            for process in self.processes:
                process.terminate()
        
        except Exception as e:
            print(e, 'meow')
        
        self.beetle_jobs.relay_node.end_client()
        print('Closed socket for Relay Node')

        return True
    

if __name__ == "__main__":
    print ("Running Relay Node")
    brain = Brain()
    try:
        brain.start_processes()
    except KeyboardInterrupt:
        print('Exiting')
