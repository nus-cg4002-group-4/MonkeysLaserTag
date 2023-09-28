import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import random
import json
import asyncio
from helpers.RelayServer import RelayServer

class RelayServerJobs:
    def __init__(self):
        self.relay_server = RelayServer()
        self.processes = []
    
    async def receive_from_relay_node(self, conn_socket, relay_server_to_engine):
        msg = await self.relay_server.receive_from_node(conn_socket)
        if self.relay_server.is_running:
            relay_server_to_engine.put('request')
            print('Received from relay node: ', msg)

    def receive_from_relay_node_task(self, conn_socket, relay_server_to_engine):
        while self.relay_server.is_running:
            try:
                asyncio.run(self.receive_from_relay_node(conn_socket, relay_server_to_engine))
            except Exception as e:
                print(e)
                break
            except:
                break

    def get_dummy_packet(self):
        packet = {
            'p1': 2
        }

        p = json.dumps(packet).encode()
        return str(len(p)) + '_' + p.decode()
    
    def send_to_relay_node_task(self, conn_socket, relay_server_to_node):
        while True:
            try:
                msg = relay_server_to_node.get()
                msg = self.get_dummy_packet()
                print('Sent to relay node: ', msg)
                self.relay_server.send_to_node(msg.encode(), conn_socket)
                time.sleep(40)
            except:
                break
        
    def relay_server_job(self, relay_server_to_engine, relay_server_to_node):
        conn_count = 0
        
        while conn_count < 2:
            try:
                conn_socket = self.relay_server.start_connection()
                print(f'Relay node {conn_count + 1} connected')

                process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_socket, relay_server_to_engine), daemon=True)
                self.processes.append(process_receive)
                process_receive.start()

                process_send = Process(target=self.send_to_relay_node_task, args=(conn_socket, relay_server_to_node), daemon=True)
                self.processes.append(process_send)
                process_send.start()

            except:
                break
            else:
                conn_count += 1
                time.sleep(.5)
        
        try:
            for p in self.processes:
                p.join()

        except KeyboardInterrupt: 
            print('Terminating Relay Server Job')

        self.close_job()
        return True
    
    def close_job(self):
        self.relay_server.close_connection()
        
        
        
    
    