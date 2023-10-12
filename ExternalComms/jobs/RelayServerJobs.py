import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import random
import json
import asyncio
from helpers.RelayServer import RelayServer
from helpers.Parser import Parser

class RelayServerJobs:
    def __init__(self):
        self.relay_server = RelayServer()
        self.parser = Parser()
        self.processes = []

        self.relay_node_to_parser = Queue()

    def send_from_parser(self, node_to_parser, relay_server_to_engine):
        while True:
            try:
                data = node_to_parser.get()
                data_arr = self.parser.convert_to_arr(data)
                #print('data_arr', 'data arr')
                pkt_id, msg = self.parser.decide_dest(data_arr)
                if pkt_id == 1:
                    # hand
                    # send to ai
                    continue
                elif pkt_id == 2:
                    # goggle
                    relay_server_to_engine.put((pkt_id, msg))
                elif pkt_id == 3:
                    # bullet
                    relay_server_to_engine.put((pkt_id, msg))
            
                
            except Exception as e:
                print(e)
                break
            except:
                break
    

    async def receive_from_relay_node(self, conn_socket_num, node_to_parser):
        print('recv from relay node')
        print(conn_socket_num)
        try:
            msg = await self.relay_server.receive_from_node(conn_socket_num)
            if self.relay_server.is_running:
                node_to_parser.put(msg)
                print('Received from relay node: ', 'msg')

        except Exception as e:
            print(e)

    def receive_from_relay_node_task(self, conn_socket_num, action_to_engine):
        while self.relay_server.is_running:
            try:
                asyncio.run(self.receive_from_relay_node(conn_socket_num, action_to_engine))
            except Exception as e:
                print(e)
                break
            except:
                break

    def get_dummy_packet(self):
        packet = {
            'p1': 2,
            'dummy': 3
        }

        p = json.dumps(packet).encode()
        return str(len(p)) + '_' + p.decode()
    
    def send_to_relay_node_task(self, conn_socket_num, relay_server_to_node):
        while True:
            try:
                # Send dummy message to relay node every 10 s
                
                msg = relay_server_to_node.get()
                #msg = self.get_dummy_packet()
                print('Sent to relay node: ', msg)
                self.relay_server.send_to_node(msg.encode(), conn_socket_num)

            except Exception as e:
                print(e, 'got errrr')
                break
            except:
                break
        
    def relay_server_job(self, relay_server_to_engine, relay_server_to_node):
        conn_count = 0
        process_parse = Process(target=self.send_from_parser, args=(self.relay_node_to_parser, relay_server_to_engine), daemon=True)
        self.processes.append(process_parse)
        process_parse.start()

        while conn_count < 2:
            try:
                conn_socket = self.relay_server.start_connection(conn_count)
                print(f'Relay node {conn_count + 1} connected')

                process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_count, self.relay_node_to_parser), daemon=True)
                self.processes.append(process_receive)
                process_receive.start()

                process_send = Process(target=self.send_to_relay_node_task, args=(conn_count, relay_server_to_node), daemon=True)
                self.processes.append(process_send)
                process_send.start()
            except Exception as e:
                print(e)
                break
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
        
        
        
    
    