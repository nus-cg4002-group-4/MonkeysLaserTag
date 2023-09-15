from socket import *
import json

class RelayServer:
    def __init__(self):
        self.server_name = 'localhost'
        self.port1 = 1200
        self.port2 = 1201
        self.conn_socket1 = None
        self.conn_socket2 = None
        self.connection_count = 0
    
    def receive_from_node(self, conn_socket):
        msg = conn_socket.recv(2048).decode()
        return msg

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
        if self.conn_socket1:
            self.conn_socket1.close()
        if self.conn_socket2:
            self.conn_socket2.close()
        print('Closed sockets for relay server')
        
        
    
# server = RelayServer()
# server.start_server()
# server.close_server()
    
    