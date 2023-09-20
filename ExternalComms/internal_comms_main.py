import time
from multiprocessing import Lock, Process, Queue, current_process

from RelayNode import RelayNode
from BeetleJobs import BeetleJobs


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

            # Send to IMU Process
            self.send_to_imu_process = Process(target=self.beetle_jobs.send_to_beetle_job, 
                                                args=(self.node_to_imu,))
            self.processes.append(self.send_to_imu_process)
            self.send_to_imu_process.start()

             # Send to IR Process
            self.send_to_ir_process = Process(target=self.beetle_jobs.send_to_beetle_job, 
                                                args=(self.node_to_ir,))
            self.processes.append(self.send_to_ir_process)
            self.send_to_ir_process.start()

            # Receive from IMU Process
            self.recv_from_imu_process = Process(target=self.beetle_jobs.recv_from_beetle_job, 
                                                args=(self.node_to_server,))
            self.processes.append(self.recv_from_imu_process)
            self.recv_from_imu_process.start()

            # Receive from IR Process
        
            for p in self.processes:
                p.join()
        except KeyboardInterrupt:
            print('Terminating Main')
        
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
