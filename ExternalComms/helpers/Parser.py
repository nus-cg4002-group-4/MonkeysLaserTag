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
        pkt_id = int(msg_arr[0])
        to_viz = '1 '
        if pkt_id == 1:
            # hand
            msg = 'test'
            
        elif pkt_id == 2:
            # goggle
            # TODO: Change for 2 player game
            msg = '2 ' + ' '.join(map(str, msg_arr))
            print('msg was ',  msg)
            
        elif pkt_id == 3:
            # bullet
            msg = to_viz + ' '.join(map(str, msg_arr))
            
        
        return (pkt_id, msg)
    