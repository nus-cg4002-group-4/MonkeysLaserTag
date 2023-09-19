from socket import *
import json
import base64
import random

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class EvalClient:
    def __init__(self):
        self.hostname = None
        self.port = None
        self.secret_key = None
        self.client_socket = None
    
    def encrypt_and_format(self, msg):
        padded = pad(msg.encode(), AES.block_size)
        secret_key = bytes(self.secret_key, encoding="utf8")
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(secret_key,AES.MODE_CBC,iv)
        
        encoded = base64.b64encode(iv + cipher.encrypt(padded))
        formatted = str(len(encoded)) + '_' + encoded.decode()
        return formatted.encode('utf8')
    
    def send_to_server(self, msg):
        to_send = self.encrypt_and_format(msg)
        self.client_socket.send(to_send)
    
    def send_to_server_w_res(self, msg):
        to_send = self.encrypt_and_format(msg)
        self.client_socket.send(to_send)
        rcvd = self.client_socket.recv(2048).decode('utf8')
        return rcvd
    
    def initialize(self):
        # Read connection details
        f = open('info.json')
        data = json.load(f)
        self.hostname = data['eval']['hostname']
        self.secret_key = data['eval']['password']
        f.close()

    def connect_to_server(self):
        self.port = int(input("Enter port number: "))
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((self.hostname, self.port))
        self.send_to_server('hello')
    
    def start_client(self):
        self.initialize()
        self.connect_to_server()
        
    def close_client(self):
        self.client_socket.close()
        print('Closed socket for Eval Server')

    def get_dummy_eval_state_str():
        state = EvalClient.get_dummy_eval_state_json()
        return json.dumps(state)

    def get_dummy_eval_state_json():
        state = {
            'player_id': 1,
            'action': random.choice(['grenade', ]),
            'game_state': {
                'p1': EvalClient.get_dummy_game_state_json(),
                'p2': EvalClient.get_dummy_game_state_json()
            }
        }   
        return state
    
    def get_dummy_game_state_json():
        state = {
                    'hp': random.choice(range(101)),
                    'bullets': random.choice(range(7)),
                    'grenades': 2,
                    'shield_hp': random.choice(range(31)),
                    'deaths': 0,
                    'shields': random.choice(range(4))
                }
        return state

EvalClient.get_dummy_eval_state_str = staticmethod(EvalClient.get_dummy_eval_state_str)    
EvalClient.get_dummy_eval_state_json = staticmethod(EvalClient.get_dummy_eval_state_json)
EvalClient.get_dummy_game_state_json = staticmethod(EvalClient.get_dummy_game_state_json)