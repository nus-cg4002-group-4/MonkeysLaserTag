import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import random
import json
import curses
import asyncio

from RelayNode import RelayNode

class BeetleJobs:
    def __init__(self):
        self.processes = []
        self.relay_node = None
    
    def get_dummy_packet(self):
        packet = {
            'pkt_id': random.choice(range(4)),
            'ax': random.choice(range(20, 60)),
            'ay': random.choice(range(-60,-20)),
            'az': random.choice(range(1000, 1200))
        }

        p = json.dumps(packet).encode()
        return str(len(p)) + '_' + p.decode()

    def send_to_beetle_job(self, node_to_beetle):
        while True:
            try:
                data = node_to_beetle.get()
                # TODO: send to beetle
            except:
                break 

    def send_to_server_job(self, node_to_server):   
        print('start sending')
        while True:
            try:
                # TODO: Remove data formatting part
                data = node_to_server.get()
                p = str(list(data.values()))
                msg = str(len(p.encode())) + '_' + p
                
                print(msg)
                print('send')
                self.relay_node.send_to_server(msg)
            except Exception as e:
                print(e)
                break
            except:
                break


    def recv_from_server_job(self, node_to_imu, node_to_ir):
        while self.relay_node.is_running:
            try:
                asyncio.run(self.recv_from_server(node_to_imu, node_to_ir))
            except Exception as e:
                print(e)
                break
            except:
                break
        print('end job')
    
    async def recv_from_server(self, node_to_imu, node_to_ir):
        data = await self.relay_node.receive_from_server()
        print(f'{bcolors.OKGREEN}Received from Server: {data}{bcolors.ENDC}')
        # TODO: Decide if it's for IMU or IR
        # if data == 'imu':
        #     node_to_imu.put(data)
        # elif data == 'ir':
        #     node_to_ir.put(data)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


        
    
    
    