import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import random
import json
import asyncio
from helpers.RelayServer import RelayServer
from helpers.Parser import Parser
from helpers.Dma import Dma
import sys, os
import numpy as np

WINDOW = 80
REMOVE = 20
cfd = f'{sys.path[0]}/../HardwareAi/HLS_CNN'
dir = os.path.join(cfd, 'old_values_for_testing')

class RelayServerJobs:
    def __init__(self):
        self.relay_server = RelayServer()
        self.parser = Parser()
        self.processes = []
        self.relay_node_to_parser = Queue()
        self.dma = Dma()
    
    def send_to_ai_task(self, relay_server_to_ai):
        packets = []
        count = 0
        while True:
            try:
                for file in os.listdir(dir):
                    if file.endswith(".in"):
                        print('Testing file', file)
                        f = open(os.path.join(dir, file), 'r')
                        data = f.read().split(',')
                        self.dma.send_to_ai(data)
                # data_arr = relay_server_to_ai.get()
                # packets.append(data_arr)
                # count += 1

                # if count == WINDOW:
                #     # DMA stuff
                #     count = WINDOW - REMOVE
                #     
                #     #self.dma.send_to_ai_input_2d(n)
                #     packets[:] = packets[REMOVE:WINDOW + 1]
            
            except Exception as e:
                print(e)
                break
            except e:
                break
    
    def receive_from_ai_task(self, relay_server_to_engine):
        while True:
            try:
                ai_result = self.dma.recv_from_ai()
                relay_server_to_engine.put((1, '1 ' + str(ai_result)))
                # relay_server_to_engine.put((1, '1 3'))
                # time.sleep(60)
                # print('put')
            
            except Exception as e:
                print(e)
                break
            except e:
                break

    def send_from_parser(self, node_to_parser, relay_server_to_engine, relay_server_to_ai):
        while True:
            try:
                data = node_to_parser.get()
                data_arr = self.parser.convert_to_arr(data)
                #print('data_arr', 'data arr')
                pkt_id, msg = self.parser.decide_dest(data_arr)
                if pkt_id == 1:
                    # hand
                    # send to ai
                    relay_server_to_ai.put(data_arr)
                    continue
                elif pkt_id == 2:
                    # goggle
                    print('pkt ', 2)
                    relay_server_to_engine.put((pkt_id, msg))
                elif pkt_id == 3:
                    # bullet
                    print('pket', 3)
                    relay_server_to_engine.put((pkt_id, msg))
                
            except Exception as e:
                print(e)
                break
            except:
                break
    

    async def receive_from_relay_node(self, conn_socket_num, node_to_parser):
        # print('recv from relay node')
        # print(conn_socket_num)
        try:
            msg = await self.relay_server.receive_from_node(conn_socket_num)
            if self.relay_server.is_running:
                node_to_parser.put(msg)
                #print('Received from relay node: ', 'msg')

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

    def packet_to_len_str(self, packet):

        p = packet.encode()
        return str(len(p)) + '_' + p.decode()
    
    def send_to_relay_node_task(self, conn_socket_num, relay_server_to_node):
        while True:
            try:
                # Send dummy message to relay node every 10 s
                
                msg = relay_server_to_node.get()
                #msg = self.get_dummy_packet()
                print('Sent to relay node: ', msg)
                self.relay_server.send_to_node(self.packet_to_len_str(msg).encode(), conn_socket_num)

            except Exception as e:
                print(e, 'got errrr')
                break
            except:
                break
        
    def relay_server_job(self, relay_server_to_engine, relay_server_to_node, relay_server_to_ai):
        conn_count = 0
        self.dma.initialize()
        process_parse = Process(target=self.send_from_parser, args=(self.relay_node_to_parser, relay_server_to_engine, relay_server_to_ai), daemon=True)
        self.processes.append(process_parse)
        process_parse.start()

        process_send_to_ai = Process(target=self.send_to_ai_task, args=(relay_server_to_ai,), daemon=True)
        self.processes.append(process_send_to_ai)
        process_send_to_ai.start()

        process_rcv_from_ai = Process(target=self.receive_from_ai_task, args=(relay_server_to_engine,), daemon=True)
        self.processes.append(process_rcv_from_ai)
        process_rcv_from_ai.start()

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
        
        
        
    
    