from socket import *
import json
from time import perf_counter
import asyncio

class RelayServer:
    def __init__(self):
        self.server_name = ''
        self.port1 = 26490
        self.port2 = 26590
        self.conn_socket1 = None
        self.conn_socket2 = None
        self.connection_count = 0
        self.is_running = True
        self.timeout = 60
        self.listen_sockets = []
    
    async def recv_text(self, timeout, conn_socket):
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
                        task = loop.sock_recv(conn_socket, 1)
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: relay client disconnected')
                        self.close_connection()
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
                        self.close_connection()
                        break
                    text_received = data.decode("utf8")  # Decode raw bytes to UTF-8
                    success = True
                    break
            except ConnectionResetError:
                print('recv_text: Connection Reset for relay')
                self.close_connection()
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

    def send_to_node(self, msg, conn_socket):
        # Msg has been encoded from parser
        conn_socket.send(msg)
        return msg
    
    def close_socket(self, conn_socket):
        conn_socket.close()
    
    def start_connection(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((self.server_name, self.port1 if self.connection_count == 0 else self.port2))
        server_socket.listen()
        self.listen_sockets.append(server_socket)
        self.is_running = True

        if self.connection_count == 0:
            self.conn_socket1, client_addr2 = server_socket.accept()
            print('accep 1')
            self.connection_count += 1
            return self.conn_socket1
        else:
            self.conn_socket2, client_addr2 = server_socket.accept()
            print('accep 2')
            return self.conn_socket2
    
    def close_connection(self):
        if self.is_running:
            self.is_running = False
            if self.conn_socket1:
                self.conn_socket1.shutdown(SHUT_RDWR)
                self.conn_socket1.close()
            if self.conn_socket2:
                self.conn_socket2.shutdown(SHUT_RDWR)
                self.conn_socket2.close()
            for s in self.listen_sockets:
                if s: s.close()
        print('Closed sockets for relay server')
    
# server = RelayServer()
# server.start_server()
# server.close_server()
    
    