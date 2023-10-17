from socket import *
import json
from time import perf_counter
import asyncio

class ClientDisconnectException(Exception):
    "Raised when client has disconnected from relay server"
    pass

class RelayServer:
    def __init__(self):
        self.server_name = ''
        self.port1 = 26498
        self.port2 = 26590
        self.connection_count = 0
        self.is_running = True
        self.timeout = 60
        self.conn_sockets = []
        self.listen_sockets = []
        self.is_conncted = [False, False]
    
    async def recv_text(self, timeout, conn_socket_num):
        conn_socket = self.conn_sockets[conn_socket_num]
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
                        raise ClientDisconnectException
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
                        raise ClientDisconnectException
                        break
                    text_received = data.decode("utf8")  # Decode raw bytes to UTF-8
                    success = True
                    break
            except ConnectionResetError:
                print('recv_text: Connection Reset for relay')
                raise ClientDisconnectException
            except asyncio.TimeoutError:
                print('recv_text: Timeout while receiving data from relay')
                self.close_connection()
                timeout = -1
        else:
            timeout = -1

        return success, timeout, text_received
    
    async def receive_from_node(self, conn_socket_num):
        success, timeout, text = await self.recv_text(self.timeout, conn_socket_num)
        return text

    def send_to_node(self, msg, conn_socket_num):
        # Msg has been encoded from parser
        if self.is_conncted[conn_socket_num]:
            self.conn_sockets[conn_socket_num].send(msg)
        return msg
    
    def close_socket(self, conn_socket):
        conn_socket.close()
    
    def start_connection(self, conn_num):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((self.server_name, self.port1 if conn_num == 0 else self.port2))
        server_socket.listen()
        self.listen_sockets.append(server_socket)
        self.is_running = True

        conn_socket, client_addr2 = server_socket.accept()
        self.conn_sockets.append(conn_socket)
        self.is_conncted[conn_num] = True
        print('\naccep 1')
        self.connection_count += 1
        return conn_socket
        
    
    def re_accept_connection(self, socket_num):
        self.is_conncted[socket_num] = False
        print(self.is_conncted, 'reaccept')
        server_socket = self.listen_sockets[socket_num]
        print('Attempt reconnection')
        conn_socket, client_addr2 = server_socket.accept()
        self.conn_sockets[socket_num] = conn_socket
        self.is_conncted[socket_num] = True
        print('reconnected')
        return conn_socket
    
    def close_connection(self):
        if self.is_running:
            self.is_running = False
            for s in self.conn_sockets:
                if s:
                    s.shutdown(SHUT_RDWR)
                    s.close()
            for s in self.listen_sockets:
                if s: s.close()
        print('Closed sockets for relay server')
    
# server = RelayServer()
# server.start_server()
# server.close_server()
    
    
