import time
from multiprocessing import Process, Queue, Value
import queue
import random
import json
import asyncio
from helpers.RelayServer import RelayServer, ClientDisconnectException
from helpers.Parser import Parser
from helpers.Dma import Dma
import sys, os
import numpy as np

WINDOW = 80
REMOVE = 20
cfd = f'{sys.path[0]}/../HardwareAi/HLS_CNN'
dir = os.path.join(cfd, 'old_values_for_testing')
actions = {
                0: 'grenade',
                1: 'shield',
                2: 'reload',
                7: 'web',
                6: 'portal',
                3: 'punch',
                5: 'hammer',
                4: 'spear',
                8: 'logout',
                9: 'raise hand'
        }

class RelayServerJobs:
    def __init__(self):
        self.relay_server = RelayServer()
        self.parser = Parser()
        self.processes = []
        self.dma = Dma()
        self.is_client1_connected = Value('i', 1)
        self.is_client2_connected = Value('i', 1)
        self.client1_socket_update = Queue()
        self.client2_socket_update = Queue()
    
    def send_to_ai_task(self, relay_server_to_ai, relay_server_to_engine, conn_num):
        packets = []
        count = 0
        while True:
            try:
                data_arr = relay_server_to_ai.get(timeout=20)
                packets.append(data_arr[1:])

                count += 1

                if count == WINDOW:
                        # DMA stuff
                    print('80 reached ', conn_num + 1)
                    count = WINDOW - REMOVE
                    self.dma.send_to_ai_input_2d(np.array(packets))
                    ai_result, certainty = self.dma.recv_from_ai()
                    # ai_result, certainty = (3, 0.5)
                    print(actions[ai_result], ai_result, ' ',  certainty, ' certainty')
                    if certainty > 0.4 and ai_result != 9:
                        relay_server_to_engine.put((1, f'{conn_num + 1} {ai_result}'))
                    packets[:] = []
                    time.sleep(1)
                    try:
                        while True:
                            relay_server_to_ai.get_nowait()
                    except queue.Empty:
                        print('now empty queue.')

                    count = 0
            except queue.Empty:
                count = 0
                packets[:] = []
                print('Discarded relay packets')
            except Exception as e:
                print(e)
                break
            except e:
                break
    
    # def receive_from_ai_task(self, relay_server_to_engine):
    #     recents = [-1] * 3
        
    #     while True:
    #         try:
    #             ai_result, certainty = self.dma.recv_from_ai()
    #             print(actions[ai_result], ai_result, ' ',  certainty, ' certainty')
    #             if certainty > 0.4 and ai_result != 9:
    #                 relay_server_to_engine.put((1, '1 ' + str(ai_result)))
    #             #recents.pop(0)
    #             #recents.append(ai_result)
    #             # relay_server_to_engine.put((1, '1 3'))
    #             # time.sleep(60)
    #             # print('put')
            
    #         except Exception as e:
    #             print(e)
    #             break
    #         except e:
    #             break

    def send_from_parser(self, node_to_parser, relay_server_to_engine_p1, relay_server_to_ai_p1, relay_server_to_engine_p2, relay_server_to_ai_p2):
        while True:
            try:
                player_id, data = node_to_parser.get()
                data_arr = self.parser.convert_to_arr(data)
                #print('data_arr', 'data arr')
                pkt_id, msg = self.parser.decide_dest(data_arr)
                if pkt_id == 1:
                    # hand
                    # send to ai
                    if player_id == 1:
                        relay_server_to_ai_p1.put(data_arr)
                    else:
                        relay_server_to_ai_p2.put(data_arr)
                    continue
                elif pkt_id == 2:
                    # goggle
                    print('pkt ', 2)
                    if player_id == 1:
                        relay_server_to_engine_p1.put((pkt_id, msg))
                    else:
                        relay_server_to_engine_p2.put((pkt_id, msg))
                elif pkt_id == 3:
                    # bullet
                    print('pket', 3)
                    if player_id == 1:
                        relay_server_to_engine_p1.put((pkt_id, msg))
                    else:
                        relay_server_to_engine_p2.put((pkt_id, msg))
                
            except Exception as e:
                print(e, 'a')
                break
            except:
                break
    

    async def receive_from_relay_node(self, conn_socket_num, node_to_parser, is_connected, client_socket_update):
        # print('recv from relay node')
        # print(conn_socket_num)
        try:
            msg = await self.relay_server.receive_from_node(conn_socket_num)
            if self.relay_server.is_running:
                node_to_parser.put((conn_socket_num + 1, msg))
                print('Received from relay node: ', msg, conn_socket_num + 1)
        except ClientDisconnectException:
            is_connected.value = 0
            new_socket = self.relay_server.re_accept_connection(conn_socket_num)
            client_socket_update.put(new_socket)
            is_connected.value = 1

    def receive_from_relay_node_task(self, conn_socket_num, action_to_engine, is_connected, client_socket_update):
        while self.relay_server.is_running:
            try:
                asyncio.run(self.receive_from_relay_node(conn_socket_num, action_to_engine, is_connected, client_socket_update))
            except Exception as e:
                print(e)
                break
            except:
                break

    def packet_to_len_str(self, packet):
        p = packet.encode()
        return str(len(p)) + '_' + p.decode()
    
    def send_to_relay_node_task(self, relay_server_to_node):
        while True:
            try:
                msg = relay_server_to_node.get()
                if self.is_client1_connected.value:
                    self.relay_server.send_to_node(self.packet_to_len_str(msg).encode(), 0)
                else:
                    print('waiting to reconnect', 'node 1')
                    new_socket = self.client1_socket_update.get()
                    self.relay_server.conn_sockets[0] = new_socket

                if self.is_client2_connected.value:
                    self.relay_server.send_to_node(self.packet_to_len_str(msg).encode(), 1)
                else:
                    print('waiting to reconnect', 'node 2')
                    new_socket = self.client2_socket_update.get()
                    self.relay_server.conn_sockets[1] = new_socket
            except Exception as e:
                print(e, 'got errrr')
                break
            except:
                break
    
    def initialize(self):
        self.dma.initialize()
        pass
    
    def relay_server_job_player(self, relay_server_to_engine, relay_server_to_node, relay_server_to_ai, relay_server_to_parser, conn_count):
        try:
            process_send_to_ai = Process(target=self.send_to_ai_task, args=(relay_server_to_ai, relay_server_to_engine, conn_count), daemon=True)
            self.processes.append(process_send_to_ai)
            process_send_to_ai.start()

            # process_rcv_from_ai = Process(target=self.receive_from_ai_task, args=(relay_server_to_engine,), daemon=True)
            # self.processes.append(process_rcv_from_ai)
            # process_rcv_from_ai.start()

            conn_socket = self.relay_server.start_connection(conn_count)
            print(f'Relay node {conn_count + 1} connected')

            is_client_connected = self.is_client1_connected if conn_count == 0 else self.is_client2_connected
            socket_update = self.client1_socket_update if conn_count == 0 else self.client2_socket_update

            process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_count, relay_server_to_parser, is_client_connected, socket_update), daemon=True)
            self.processes.append(process_receive)
            process_receive.start()

        except Exception as e:
            print(e)
        except:
            print('err in relay server')
        
        try:
            for p in self.processes:
                p.join()

        except KeyboardInterrupt: 
            print('Terminating Relay Server Job ', conn_count)

        self.close_job()
        return True
    
    
    # def relay_server_job(self, relay_server_to_engine, relay_server_to_node, relay_server_to_ai):
    #     conn_count = 0
    #     self.dma.initialize()
    #     process_parse = Process(target=self.send_from_parser, args=(self.relay_node_to_parser, relay_server_to_engine, relay_server_to_ai), daemon=True)
    #     self.processes.append(process_parse)
    #     process_parse.start()

    #     process_send_to_ai = Process(target=self.send_to_ai_task, args=(relay_server_to_ai,), daemon=True)
    #     self.processes.append(process_send_to_ai)
    #     process_send_to_ai.start()

    #     process_rcv_from_ai = Process(target=self.receive_from_ai_task, args=(relay_server_to_engine,), daemon=True)
    #     self.processes.append(process_rcv_from_ai)
    #     process_rcv_from_ai.start()

    #     while conn_count < 2:
    #         try:
    #             conn_socket = self.relay_server.start_connection(conn_count)
    #             print(f'Relay node {conn_count + 1} connected')

    #             process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_count, self.relay_node_to_parser, self.is_client1_connected, self.client1_socket_update), daemon=True)
    #             self.processes.append(process_receive)
    #             process_receive.start()

    #             process_send = Process(target=self.send_to_relay_node_task, args=(conn_count, relay_server_to_node, self.is_client1_connected, self.client1_socket_update), daemon=True)
    #             self.processes.append(process_send)
    #             process_send.start()
    #         except Exception as e:
    #             print(e)
    #             break
    #         except:
    #             break
    #         else:
    #             conn_count += 1
    #             time.sleep(.5)
        
    #     try:
    #         for p in self.processes:
    #             p.join()

    #     except KeyboardInterrupt: 
    #         print('Terminating Relay Server Job')

    #     self.close_job()
    #     return True
    
    def close_job(self):
        self.relay_server.close_connection()
        
        
        
    
    
