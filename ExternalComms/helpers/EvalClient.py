from socket import *
import json
import base64
import random
from time import perf_counter
import asyncio

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class EvalClient:
    def __init__(self):
        self.hostname = None
        self.port = None
        self.secret_key = None
        self.client_socket = None
        self.timeout = 60
        self.is_running = True
    
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
                        task = loop.sock_recv(self.client_socket, 1)
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: Eval server disconnected')
                        self.close_client()
                        self.is_running = False
                        break
                    data = data.decode("utf-8")
                    length = int(data[:-1])
                    data = b''
                    while len(data) < length:
                        start_time = perf_counter()
                        task = loop.sock_recv(self.client_socket, length - len(data))
                        _d = await asyncio.wait_for(task, timeout=timeout)
                        timeout -= (perf_counter() - start_time)
                        if not _d:
                            data = b''
                            break
                        data += _d
                    if len(data) == 0:
                        print('recv_text: Eval server disconnected')
                        self.close_client()
                        break
                    text_received = data.decode("utf8")  # Decode raw bytes to UTF-8
                    success = True
                    break
            except ConnectionResetError:
                print('recv_text: Connection Reset for Eval Server')
                self.close_client()
            except asyncio.TimeoutError:
                print('recv_text: Timeout while receiving data from Eval Server')
                timeout = -1
        else:
            timeout = -1

        return success, timeout, text_received
    
    async def send_to_server_w_res(self, msg):
        to_send = self.encrypt_and_format(msg)
        self.client_socket.send(to_send)
        success, timeout, text = await self.recv_text(self.timeout)
        # if not success:
        #     print('Timeout from receiving data from eval server. Generating randoma action')
        #     return self.get_dummy_response_from_eval_str()

        return text
    
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
        self.is_running = False
        if self.client_socket:
            self.client_socket.close()
            print('Closed socket for Eval Server')

    def get_dummy_eval_state_str():
        state = EvalClient.get_dummy_eval_state_json()
        return json.dumps(state)

    def get_dummy_eval_state_json():
        state = {
            'player_id': 1,
            'action': random.choice(['grenade', 'punch', 'spear', 'web', 'hammer', 'portal', 'shield']),
            'game_state': {
                'p1': EvalClient.get_dummy_game_state_json(),
                'p2': EvalClient.get_dummy_game_state_json()
            }
        }   
        return state
    
    def get_dummy_response_from_eval_str():
        state = {
            'p1': EvalClient.get_dummy_game_state_json(),
            'p2': EvalClient.get_dummy_game_state_json()
        }
        return json.dumps(state)

    
    def get_dummy_game_state_json():
        # state = {
        #             'hp': random.choice(range(101)),
        #             'bullets': random.choice(range(7)),
        #             'grenades': 2,
        #             'shield_hp': random.choice(range(31)),
        #             'deaths': 0,
        #             'shields': random.choice(range(4))
        #         }
        state = {
                    'hp':100,
                    'bullets': 6,
                    'grenades': 2,
                    'shield_hp': 0,
                    'deaths': 0,
                    'shields': random.choice(range(4))
                }
        return state

EvalClient.get_dummy_eval_state_str = staticmethod(EvalClient.get_dummy_eval_state_str)    
EvalClient.get_dummy_eval_state_json = staticmethod(EvalClient.get_dummy_eval_state_json)
EvalClient.get_dummy_game_state_json = staticmethod(EvalClient.get_dummy_game_state_json)
EvalClient.get_dummy_response_from_eval_str = staticmethod(EvalClient.get_dummy_response_from_eval_str)