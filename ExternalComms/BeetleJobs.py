import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import random
import json
import curses
import asyncio

import getch
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
    
    def recv_from_beetle_job(self, node_to_server):
        print('Input msg below:')
        while True:
            try:
                # TODO: Put Beetle code here
                # Use keyboard input and dummy msg for now
                a = getch.getche()
                msg = self.get_dummy_packet()
                node_to_server.put(msg)

                # Exit sequence
                if a == '@': break
                time.sleep(0.1)
                # TODO: send to beetle
            except Exception as e:
                print(e)
                break
            except:
                curses.endwin()
                break
        print('Exiting input mode')

    def send_to_beetle_job(self, node_to_beetle):
        while True:
            try:
                data = node_to_beetle.get()
                # TODO: send to beetle
            except:
                break 

    def send_to_server_job(self, node_to_server):   
        while True:
            try:
                data = node_to_server.get()
                self.relay_node.send_to_server(data)
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
        # Decide if it's for IMU or IR
        if data == 'imu':
            node_to_imu.put(data)
        elif data == 'ir':
            node_to_ir.put(data)

    


        
    
    
    