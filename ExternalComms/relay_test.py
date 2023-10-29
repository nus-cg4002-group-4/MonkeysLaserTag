import time
from multiprocessing import Lock, Process, Queue, Value, Manager
from multiprocessing.managers import BaseManager
import json
import asyncio
import random
from helpers.RelayServer import RelayServer, ClientDisconnectException
from helpers.Parser import Parser
from multiprocessing.managers import BaseManager
from socket import *

class MyManager(BaseManager): pass

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

class RelayTest:
    def __init__(self):
        self.relay_server = RelayServer()
        self.parser = Parser()
        
        self.relay_server_process = None
        self.parser_process = None
        
        self.relay_server_to_engine = Queue()
        self.relay_server_to_node = Queue()

        self.is_client_connected = Value('i', 1)

        self.relay_node_to_parser = Queue()
        self.dummy_queue = Queue()

        MyManager.register('socket', socket)
        self.manager = MyManager()
        self.manager.start()
        self.conn1 = self.manager.socket(AF_INET, SOCK_STREAM)
        self.conn2 = self.manager.socket(AF_INET, SOCK_STREAM)

    def send_from_parser(self, node_to_parser, relay_server_to_engine):
        while True:
            try:
                data = node_to_parser.get()
                data_arr = self.parser.convert_to_arr(data)
                pkt_id, msg = self.parser.decide_dest(data_arr)
                if pkt_id == 1:
                    # hand
                    # send to ai
                    continue
                elif pkt_id == 2:
                    # goggle
                    relay_server_to_engine.put(msg)
                elif pkt_id == 3:
                    # bullet
                    relay_server_to_engine.put(msg)
            
                print('data arr', data_arr)
            except Exception as e:
                print(e, 'a')
                break
            except:
                break
    

    async def receive_from_relay_node(self, conn_socket, node_to_parser, is_connected, dummy_q):
        # print(conn_socket_num)
        try:
            msg = await self.relay_server.receive_from_node(conn_socket)
            if self.relay_server.is_running:
                node_to_parser.put(msg)
                print('Received from relay node: ', msg)
        except ClientDisconnectException:
            is_connected.value = 0
            new_socket = self.relay_server.re_accept_connection(0)
            self.conn1.value = new_socket
            dummy_q.put(new_socket)
            is_connected.value = 1
        except Exception as e:
            print(e)
            
    def receive_from_relay_node_task(self, conn_socket, relay_node_to_parser, is_connected, dummy_q):
        # print(conn_socket)
        is_connected.value = 1
        while self.relay_server.is_running:
            try:
                asyncio.run(self.receive_from_relay_node(conn_socket.value, relay_node_to_parser, is_connected, dummy_q))
            except Exception as e:
                print(e)
                break
            except:
                break
        print('not running')
    
    def get_dummy_eval_state_json(self):
        state = {
            'player_id': 1,
            'action': random.choice(['grenade', 'portal', 'shield']),
            'game_state': {
                'p1': {
                    'health': 100
                }
            }
        }   
        return state

    def get_dummy_packet(self):
        packet = self.get_dummy_eval_state_json()

        p = json.dumps(packet).encode()
        return str(len(p)) + '_' + p.decode()
    
    def send_to_relay_node_task(self, conn_socket, relay_server_to_node, is_connected, dummy_q):
        print('start sending')
        while True:
            try:
                # Send dummy message to relay node every 10 s
                
                #msg = relay_server_to_node.get()
                if is_connected.value:
                    msg = self.get_dummy_packet()
                    print(f"{bcolors.OKGREEN}'Sent to relay node: {msg}{bcolors.ENDC}")
                    self.relay_server.send_to_node(msg.encode(), self.relay_server.conn_sockets[0])
                    time.sleep(5)
                else:
                    print('waiting to reconnect')
                    new_socket = dummy_q.get()
                    self.relay_server.conn_sockets[0] = new_socket
                    print('send reconnected too')
                
            except Exception as e:
                print(e, 'got errrr')
                break
            except:
                break
    
        
    def relay_server_job(self, relay_server_to_engine, relay_server_to_node):
        conn_count = 0
        processes = []
        process_parse = Process(target=self.send_from_parser, args=(self.relay_node_to_parser, relay_server_to_engine), daemon=True)
        processes.append(process_parse)
        process_parse.start()

        while conn_count < 2:
            try:
                self.conn1.value = self.relay_server.start_connection(conn_count)
                print(f'Relay node {conn_count + 1} connect')

                process_receive = Process(target=self.receive_from_relay_node_task, args=(self.conn1, self.relay_node_to_parser, self.is_client_connected, self.dummy_queue), daemon=True)
                processes.append(process_receive)
                process_receive.start()

                process_send = Process(target=self.send_to_relay_node_task, args=(self.conn1, relay_server_to_node, self.is_client_connected, self.dummy_queue), daemon=True)
                processes.append(process_send)
                process_send.start()
                print('started')

                print('start')
            except Exception as e:
                print(e, 'err')
                break
            except:
                break
            else:
                conn_count += 1
                time.sleep(.5)
        
        try:
            for p in processes:
                p.join()

        except KeyboardInterrupt: 
            print('Terminating Relay Server Job')

        self.close_job()
        return True
    
    def close_job(self):
        self.relay_server.close_connection()
    
    def start_processes(self):
        relay_server_jobs = RelayTest()
        relay_server_process = Process(target=relay_server_jobs.relay_server_job, 
                                                args=(self.relay_server_to_engine, self.relay_server_to_node))
        relay_server_process.start()

        try:
            relay_server_process.join()
        except KeyboardInterrupt: 
            print('Terminating Relay Test')
        
        return True
    
if __name__ == "__main__":
    print ("running relay test")
    try:
        brain = RelayTest()
        brain.start_processes()
    except KeyboardInterrupt:
        print('Exiting')
