import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import asyncio
from helpers.EvalClient import EvalClient
from helpers.PlayerClass import Player
from helpers.GameLogic import GameLogic
import random


class EvalClientJobs:
    def __init__(self):
        self.eval_client = EvalClient()

        self.eval_client_process = None
        self.timeout = 60
        self.game_logic = GameLogic()
    
    async def eval_client_task(self, eval_client_to_server, eval_client_to_game_engine):
        last_recvd = EvalClient.get_dummy_eval_state_str()
        while True:
            try:
                to_send = eval_client_to_server.get(timeout=self.timeout)
                response = await self.eval_client.send_to_server_w_res(to_send)
                last_recvd = response
                if self.eval_client.is_running and response:
                    print('Send to eval server: ', 'to_send')
                    eval_client_to_game_engine.put(response)
            except queue.Empty:
                try:
                    print('Time out from game engine. Sending random game state')
                    p1 = Player(1)
                    p2 = Player(2)
                    prev = self.game_logic.subscribeFromEval(last_recvd, p1, p2)
                    msg = '1 ' + str(random.choice([7, 6, 3, 5, 4]))
                    hit_miss = '1 1'
                    to_send = self.game_logic.ai_logic(msg, hit_miss, p1, p2, False)
                    response = await self.eval_client.send_to_server_w_res(to_send)
                    last_recvd = response
                    print('Send to eval server: ', to_send)
                    eval_client_to_game_engine.put(response)
                except Exception as e:
                    print(e)
                    break
            except:
                self.eval_client.is_running = False
                print('Terminating Eval Client Job')
                break
        
        return True
    
    def eval_client_job(self, eval_client_to_server, eval_client_to_game_engine):

        while self.eval_client.is_running:
            try:
                asyncio.run(self.eval_client_task(eval_client_to_server, eval_client_to_game_engine))
            except Exception as e:
                print(e, 'error at eval client')
            except:
                break
            
        self.close_job()
        return True
    
    def initialize(self):
        self.eval_client.start_client()
    
    def close_job(self):
        self.eval_client.close_client()
    


