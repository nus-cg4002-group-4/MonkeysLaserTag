import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import asyncio
from helpers.EvalClient import EvalClient


class EvalClientJobs:
    def __init__(self):
        self.eval_client = EvalClient()

        self.eval_client_process = None
        self.timeout = 15
    
    async def eval_client_task(self, eval_client_to_server, eval_client_to_game_engine):
        while True:
            try:
                to_send = eval_client_to_server.get(timeout=self.timeout)
                response = await self.eval_client.send_to_server_w_res(to_send)
                if self.eval_client.is_running:
                    print('Send to eval server: ', 'to_send')
                    eval_client_to_game_engine.put(response)
            except queue.Empty:
                print('Time out from game engine. Sending random game state')
                to_send = EvalClient.get_dummy_eval_state_str()
                response = await self.eval_client.send_to_server_w_res(to_send)
                print('Send to eval server: ', 'to_send')
                eval_client_to_game_engine.put(response)
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
                print(e)
            except:
                break
            
        self.close_job()
        return True
    
    def initialize(self):
        self.eval_client.start_client()
    
    def close_job(self):
        self.eval_client.close_client()
    


