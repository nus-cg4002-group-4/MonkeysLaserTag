import time
from multiprocessing import Lock, Process, Queue, current_process
import queue

from helpers.RelayServer import RelayServer

class RelayServerJobs:
    def __init__(self):
        self.relay_server = RelayServer()
        self.processes = []
    
    def receive_from_relay_node_task(self, conn_socket, relay_server_to_parser):
        while True:
            try:
                msg = self.relay_server.receive_from_node(conn_socket)
                print('Received from relay node: ', msg)
                relay_server_to_parser.put(msg)
            except:
                break
    
    def send_to_relay_node_task(self, conn_socket, relay_server_to_node):
        while True:
            try:
                msg = relay_server_to_node.get()
                print('Sent to relay node: ', msg)
                self.relay_server.send_to_node(msg, conn_socket)
            except:
                break
        
    def relay_server_job(self, relay_server_to_parser, relay_server_to_node):
        conn_count = 0
        
        while conn_count < 2:
            try:
                conn_socket = self.relay_server.start_connection()
                print(f'Relay node {conn_count + 1} connected')

                process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_socket, relay_server_to_parser), daemon=True)
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
        
        
        
    
    