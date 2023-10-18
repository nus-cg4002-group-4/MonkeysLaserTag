from socket import *
from time import perf_counter
import asyncio

class RelayNode:
    def __init__(self):
        self.server_host = 'makerslab-fpga-37.d2.comp.nus.edu.sg'
        # self.server_host = 'localhost'
        self.server_port = 26488
        self.server_pw = None
        self.conn_socket = None
        self.connection_count = 0
        self.is_running = True
        self.timeout = 600
    
    async def recv_text(self, timeout):
        text_received   = ""
        success         = False
        if self.is_running:
            loop = asyncio.get_event_loop()
            try:
                while True:
                    # recv length followed by '_' followed by json
                    data = b''
                    while not data.endswith(b'_'):
                        start_time = perf_counter()
                        task = loop.sock_recv(self.conn_socket, 1)
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: client disconnected')
                        self.end_client()
                        break
                    data = data.decode("utf-8")
                    length = int(data[:-1])
                    data = b''
                    while len(data) < length:
                        start_time = perf_counter()
                        task = loop.sock_recv(self.conn_socket, length - len(data))
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: client disconnected')
                        self.end_client()
                        break
                    text_received = data.decode("utf8")  # Decode raw bytes to UTF-8
                    print(text_received, 'TEXEOLHWNE')
                    success = True
                    break
            except ConnectionResetError:
                print('recv_text: Connection Reset')
                self.end_client()
            except asyncio.TimeoutError:
                print('recv_text: Timeout while receiving data')
                timeout = -1
        else:
            timeout = -1

        return success, timeout, text_received
    
    async def receive_from_server(self):
        #msg = self.conn_socket.recv(2048).decode()
        success, timeout, text = await self.recv_text(self.timeout)
        print('Received ', text, timeout, success)
        return text

    def send_to_server(self, msg):
        self.conn_socket.send(msg.encode('utf8'))
        #print('Sent ', msg)
        return msg
    
    def connect_to_server(self):
        self.conn_socket = socket(AF_INET, SOCK_STREAM)
        self.conn_socket.connect((self.server_host, self.server_port))
        
    def end_client(self):
        self.is_running = False
        if self.is_running:
            self.conn_socket.close()
            print('ended client')

    def start_client(self):
        self.is_running = True
        self.connect_to_server()
        


    
    
