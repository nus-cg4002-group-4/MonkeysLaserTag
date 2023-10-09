from socket import *
import json
from time import perf_counter
import asyncio

class Parser:
    def __init__(self):
        self.server_name = ''
    
    def convert_to_arr(self, packet):
        return list(map(int,packet[1:-1].split(', ')))
        
    def decide_dest(self, msg_arr):
        pass
    