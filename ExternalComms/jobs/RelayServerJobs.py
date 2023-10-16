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

class RelayServerJobs:
    def __init__(self):
        self.relay_server = RelayServer()
        self.parser = Parser()
        self.processes = []
        self.relay_node_to_parser = Queue()
        self.dma = Dma()
        self.is_client1_connected = Value('i', 1)
        self.client1_socket_update = Queue()
    
    def send_to_ai_task(self, relay_server_to_ai):
        packets = []
        count = 0
        while True:
            try:
                
                # for file in os.listdir(dir):
                #     if file.endswith(".in"):
                #         print('Testing file', file)
                #         f = open(os.path.join(dir, file), 'r')
                #         data = f.read().split(',')
                #         self.dma.send_to_ai(data)
                
                data_arr = relay_server_to_ai.get()
                packets.append(data_arr[1:])
                count += 1

                if count == WINDOW:
                        # DMA stuff
                    print('80 reached')
                    count = WINDOW - REMOVE
                    print('sent to ai')
                    self.dma.send_to_ai_input_2d(packets)
                    packets[:] = []
                    time.sleep(2)
                    try:
                        while True:
                            relay_server_to_ai.get_nowait()
                    except queue.Empty:
                        print('now empty queue.')

                    # Send to FPGA # pass
                    # Uncomment for var threshold 
                    # data_var = np.var([s[0] 2 + s[1] 2 + s[2] 2 for s in data_ndarray]) 
                    # if data_var > var_threshold: # # 
                    # Send to FPGA # pass
                    # packets[:] = packets[REMOVE:WINDOW + 1]
            
            except Exception as e:
                print(e)
                break
            except e:
                break
    
    def receive_from_ai_task(self, relay_server_to_engine):
        recents = [-1] * 3
        while True:
            try:
                relay_server_to_engine.put((1, '1 3'))
                time.sleep(7)
                continue
                ai_result, certainty = self.dma.recv_from_ai()
                print(ai_result, ' ',  certainty, ' certainty')
                if certainty > 0.8 and ai_result != -1:
                    relay_server_to_engine.put((1, '1 ' + str(ai_result)))
                #recents.pop(0)
                #recents.append(ai_result)
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
                node_to_parser.put(msg)
                #print('Received from relay node: ', msg)
        except ClientDisconnectException:
            is_connected.value = 0
            new_socket = self.relay_server.re_accept_connection(0)
            client_socket_update.put(new_socket)
            is_connected.value = 1

        except Exception as e:
            print(e)

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
    
    def send_to_relay_node_task(self, conn_socket_num, relay_server_to_node, is_connected, client_socket_update):
        while True:
            try:
                # Send dummy message to relay node every 10 s
                if is_connected.value:
                    msg = relay_server_to_node.get()
                    #msg = self.get_dummy_packet()
                    print('Sent to relay node: ', msg)
                    self.relay_server.send_to_node(self.packet_to_len_str(msg).encode(), conn_socket_num)
                else:
                    print('waiting to reconnect')
                    new_socket = client_socket_update.get()
                    self.relay_server.conn_sockets[0] = new_socket
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

                process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_count, self.relay_node_to_parser, self.is_client1_connected, self.client1_socket_update), daemon=True)
                self.processes.append(process_receive)
                process_receive.start()

                process_send = Process(target=self.send_to_relay_node_task, args=(conn_count, relay_server_to_node, self.is_client1_connected, self.client1_socket_update), daemon=True)
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
        
        
        
    
    
