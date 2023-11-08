import time
from multiprocessing import Process, Queue, Value
import queue
import random
import json
import asyncio
from helpers.RelayServer import RelayServer, ClientDisconnectException
from helpers.Parser import Parser
from helpers.Dma import Dma
from jobs.GameEngineJobs import bcolors
import sys, os
import numpy as np

WINDOW = 60
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
                9: 'raise hand',
                10: 'lower hand'
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
    
    def print(self, msg, player_id):
        print(f"{bcolors.OKBLUE if player_id == 1 else bcolors.OKCYAN} {msg} {bcolors.ENDC}")
    
    def send_to_ai_task(self, relay_server_to_ai, relay_server_to_engine, engine_to_vis, conn_num):
        packets = []
        count = 0
        while True:
            try:
                data_arr = relay_server_to_ai.get(timeout=20)
                packets.append(data_arr[1:])

                count += 1
                # if True:
                if count == WINDOW:
                        # DMA stuff
                    self.dma.send_to_ai_input_2d(np.array(packets), conn_num + 1)
                    player_id, ai_result, certainty = self.dma.recv_from_ai()
                    # ai_result, certainty = (3 if conn_num == 0 else 7, 0.5)
                    self.print(f"player: {player_id} action: {actions[ai_result]} {ai_result} certainty: {certainty}", conn_num + 1)
                    if certainty > 0.4 and ai_result != 9 and ai_result != 10:
                        relay_server_to_engine.put((1, f'{conn_num + 1} {ai_result}'))
                    else:
                        engine_to_vis.put(f'idle {conn_num + 1}')
                    packets[:] = []
                    time.sleep(1)
                    try:
                        while True:
                            relay_server_to_ai.get_nowait()
                    except queue.Empty:
                        self.print(f"now empty queue", conn_num + 1)
                    count = 0
            except queue.Empty:
                count = 0
                packets[:] = []
                print(f"Discarded relay packets")
            except Exception as e:
                print(e)
                break
            except e:
                break

    def send_from_parser(self, node_to_parser, bullet_to_engine_p1, relay_server_to_ai_p1, bullet_to_engine_p2, relay_server_to_ai_p2, is_node1_connected, is_node2_connected, engine_to_vis):
        while True:
            try:
                player_id, data = node_to_parser.get()
                data_arr = self.parser.convert_to_arr(data)
                pkt_id, msg = self.parser.decide_dest(data_arr, player_id)
                if pkt_id == 1:
                    # hand
                    # send to ai
                    if player_id == 1:
                        relay_server_to_ai_p1.put(data_arr)
                        is_node1_connected.value = 1
                    else:
                        relay_server_to_ai_p2.put(data_arr)
                        is_node2_connected.value = 1
                    continue
                elif pkt_id == 2:
                    # goggle
                    print('pkt ', 2)
                    if player_id == 1:
                        bullet_to_engine_p2.put((pkt_id, msg))
                        is_node1_connected.value = 1
                    else:
                        bullet_to_engine_p1.put((pkt_id, msg))
                        is_node2_connected.value = 1
                elif pkt_id == 3:
                    # bullet
                    print('pket', 3)
                    if player_id == 1:
                        bullet_to_engine_p1.put((pkt_id, msg))
                        is_node1_connected.value = 1
                    else:
                        bullet_to_engine_p2.put((pkt_id, msg))
                        is_node2_connected.value = 1
                elif pkt_id == 8:
                    print('pket', 8)
                    if player_id == 1:
                        is_node1_connected.value = 0
                        engine_to_vis.put(msg)
                    else:
                        is_node2_connected.value = 0
                        engine_to_vis.put(msg)
                elif pkt_id == 9:
                    if player_id == 1:
                        is_node1_connected.value = 1
                        engine_to_vis.put(msg)
                    else:
                        is_node2_connected.value = 1
                        engine_to_vis.put(msg)
        
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
                #print('Received from relay node: ', msg, conn_socket_num + 1)
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
    
    def send_to_relay_node_task(self, relay_server_to_node, is_connected, socket_update, conn_num):
        while True:
            try:
                msg = relay_server_to_node.get()
                if is_connected.value:
                    self.relay_server.send_to_node(self.packet_to_len_str(msg).encode(), conn_num)
                else:
                    print('waiting to reconnect', 'node 1')
                    new_socket = socket_update.get()
                    self.relay_server.conn_sockets[conn_num] = new_socket
            except Exception as e:
                print(e, 'got errrr')
                break
            except:
                break
    
    def initialize(self):
        self.dma.initialize()
        pass
    
    def relay_server_job_player(self, relay_server_to_engine, relay_server_to_node, relay_server_to_ai, relay_server_to_parser, engine_to_vis, conn_num):
        try:
            process_send_to_ai = Process(target=self.send_to_ai_task, args=(relay_server_to_ai, relay_server_to_engine, engine_to_vis, conn_num), daemon=True)
            self.processes.append(process_send_to_ai)
            process_send_to_ai.start()

            # process_rcv_from_ai = Process(target=self.receive_from_ai_task, args=(relay_server_to_engine,), daemon=True)
            # self.processes.append(process_rcv_from_ai)
            # process_rcv_from_ai.start()

            conn_socket = self.relay_server.start_connection(conn_num)
            print(f'Relay node {conn_num + 1} connected')

            is_client_connected = self.is_client1_connected if conn_num == 0 else self.is_client2_connected
            socket_update = self.client1_socket_update if conn_num == 0 else self.client2_socket_update

            process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_num, relay_server_to_parser, is_client_connected, socket_update), daemon=True)
            self.processes.append(process_receive)
            process_receive.start()

            process_send = Process(target=self.send_to_relay_node_task, args=(relay_server_to_node, is_client_connected, socket_update, conn_num), daemon=True)
            self.processes.append(process_send)
            process_send.start()

        except Exception as e: 
            print(e)
        except:
            print('err in relay server')
        
        try:
            for p in self.processes:
                p.join()

        except KeyboardInterrupt: 
            print('Terminating Relay Server Job ', conn_num)

        self.close_job()
        return True
    
    
    def close_job(self):
        self.relay_server.close_connection()
        
        
        
    
    
