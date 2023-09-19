import time
from multiprocessing import Lock, Process, Queue, current_process
import queue

from helpers.EvalClient import EvalClient


class EvalClientJobs:
    def __init__(self):
        self.eval_client = EvalClient()

        self.eval_client_process = None
    
    def eval_client_job(self, eval_client_to_server, eval_client_to_game_engine):
        while True:
            try:
                to_send = eval_client_to_server.get()
                response = self.eval_client.send_to_server_w_res(to_send)

                print('Send to eval server: ', 'to_send')
                eval_client_to_game_engine.put(response)
                time.sleep(3)
            except:
                print('Terminating Eval Client Job')
                break
        
        self.close_job()
        return True
    
    def initialize(self):
        self.eval_client.start_client()
    
    def close_job(self):
        self.eval_client.close_client()
    


