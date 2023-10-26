from socket import *
import json
import base64
import time


class RelayNode:
    def __init__(self):
        #self.server_host = 'makerslab-fpga-16.d2.comp.nus.edu.sg'
        self.server_host = 'localhost'
        self.server_port = 26581
        self.server_pw = None
        self.conn_socket = None
        self.connection_count = 0
    
    def receive_from_server(self):
        msg = self.conn_socket.recv(2048).decode()
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

    def start_client(self):
        self.connect_to_server()
        arr = [1, 1, 5]
        msg = str(arr)
        while True:
            self.send_to_server(str(len(msg)) + '_' + msg)
            time.sleep(10)


relay_node = RelayNode()
relay_node.start_client()
relay_node.end_client()

    
    
