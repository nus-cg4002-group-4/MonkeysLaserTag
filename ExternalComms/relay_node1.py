from socket import *
import json
import base64
import time
from multiprocessing import Process
import asyncio
from time import perf_counter


class RelayNode:
    def __init__(self):
        #self.server_host = 'makerslab-fpga-16.d2.comp.nus.edu.sg'
        self.server_host = 'localhost'
        self.server_port = 26483
        self.server_pw = None
        self.conn_socket = None
        self.connection_count = 0
        self.timeout = 60
    
    async def recv_text(self, timeout, conn_socket):
        text_received   = ""
        success         = False
        if True:
            loop = asyncio.get_event_loop()
            try:
                while True:
                    # recv length followed by '_' followed by json
                    data = b''
                    while not data.endswith(b'_'):
                        start_time = perf_counter()
                        task = loop.sock_recv(conn_socket, 1)
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: relay client disconnected')
                        break
                    data = data.decode("utf-8")
                    length = int(data[:-1])
                    data = b''
                    while len(data) < length:
                        start_time = perf_counter()
                        task = loop.sock_recv(conn_socket, length - len(data))
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: relay client disconnected')
                        break
                    text_received = data.decode("utf8")  # Decode raw bytes to UTF-8
                    success = True
                    break
            except ConnectionResetError:
                print('recv_text: Connection Reset for relay')
            except asyncio.TimeoutError:
                print('recv_text: Timeout while receiving data from relay')
                self.close_connection()
                timeout = -1
        else:
            timeout = -1

        return success, timeout, text_received
    
    async def receive_from_node(self, conn_socket):
        success, timeout, text = await self.recv_text(self.timeout, conn_socket)
        return text
    
    def receive_from_server(self):
        msg = self.conn_socket.recv(1024).decode()
        print('Received ', msg)
        return msg

    def send_to_server(self, msg):
        self.conn_socket.send(msg.encode('utf8'))
        print('Sent ', msg)
        return msg
    
    def connect_to_server(self):
        self.conn_socket = socket(AF_INET, SOCK_STREAM)
        self.conn_socket.connect((self.server_host, self.server_port))
        
    def end_client(self):
        self.conn_socket.close()

    def send_task(self):
        
        #self.receive_from_server()
        arr = [1, 1, 6]
        msg = str(arr)
        while True:
            self.send_to_server(str(len(msg)) + '_' + msg)
            time.sleep(10)

    def recv_task(self):
        
        #self.receive_from_server()
        arr = [1, 1, 6]
        msg = str(arr)
        while True:
            self.receive_from_server()
    
    async def receive_from_relay_node(self):
        # print('recv from relay node')
        # print(conn_socket_num)
        msg = await self.receive_from_node(self.conn_socket)
        print('recvd ', msg)

    def receive_from_relay_node_task(self):
        while True:
            try:
                asyncio.run(self.receive_from_relay_node())
            except Exception as e:
                print(e)
                break
            except:
                break

relay_node = RelayNode()
relay_node.connect_to_server()

processes = []
process_receive = Process(target=relay_node.send_task, args=(), daemon=True)
processes.append(process_receive)
process_receive.start()

process_send = Process(target=relay_node.receive_from_relay_node_task, args=(), daemon=True)
processes.append(process_send)
process_send.start()

for p in processes:
    p.join()

    
    
