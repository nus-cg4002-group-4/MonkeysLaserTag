import time
from time import perf_counter
from multiprocessing import Lock, Process, Queue, current_process
import queue
import asyncio
from helpers.EvalClient import EvalClient, EvalDisconnectException
from helpers.PlayerClass import Player
from helpers.GameLogic import GameLogic
import random

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class EvalClientJobs:
    def __init__(self):
        self.eval_client = EvalClient()

        self.eval_client_process = None
        self.timeout = 50
        self.game_logic = GameLogic()
        
    
    def print(self, msg, player_id):
        print(f"{bcolors.WARNING if player_id == 1 else bcolors.FAIL} {msg} {bcolors.ENDC}")
    
    def get_dummy(self, last_recvd, player_id):
        p1 = Player(1)
        p2 = Player(2)
        prev = self.game_logic.subscribeFromEval(last_recvd, p1, p2)
        msg = str(player_id) + ' ' + str(random.choice([7, 6, 3, 5, 4]))
        hit_miss = str(player_id) + ' 1'
        to_send = self.game_logic.ai_logic(msg, hit_miss, p1, p2, False)
        return to_send

    async def eval_timeout_task(self, eval_client_to_game_engine, latest_to_eval_timeout, is_node_connected_p1, is_node_connected_p2, eval_track_p1, eval_track_p2, is_using):
        start_time_p1 = perf_counter()
        start_time_p2 = perf_counter()
        last_recvd = EvalClient.get_dummy_eval_state_str()
        while True:
            try:
                # get the latest game state
                try:
                    new_recvd = latest_to_eval_timeout.get_nowait()
                    last_recvd = new_recvd
                except queue.Empty:
                    pass
                
                # update start time based on conn state
                if not is_node_connected_p1.value:
                    start_time_p1 = perf_counter()
                
                if not is_node_connected_p2.value:
                    start_time_p2 = perf_counter()
                
                if perf_counter() - start_time_p1 >= self.timeout:
                    # send dummy to eval

                    start_time_p1 = perf_counter()
                    print('Time out from game engine. Sending random game state for player ', 1)
                    if eval_track_p1.value:
                        self.print(f'player 1 received twice for eval, discarding...', 1)
                        continue
                    
                    if not is_node_connected_p1.value and not is_node_connected_p2.value:
                        continue

                    to_send = self.get_dummy(last_recvd, 1)
                    while is_using.value:
                        time.sleep(0.2)

                    is_using.value = 1
                    response = await self.eval_client.send_to_server_w_res(to_send)
                    is_using.value = 0
                    last_recvd = response
                    print('Send to eval server: ', to_send)
                    eval_client_to_game_engine.put(response)

                    if eval_track_p2.value:
                        eval_track_p2.value = 0
                        eval_track_p1.value = 0
                    else:
                        eval_track_p1.value = 1
                    
                    # send
                
                if perf_counter() - start_time_p2 >= self.timeout:
                    # send dummy to eval
                    print('Time out from game engine. Sending random game state for player ', 2)
                    if eval_track_p2.value:
                        start_time_p2 = perf_counter()
                        self.print(f'player 2 received twice for eval, discarding...', 2)
                        continue

                    to_send = self.get_dummy(last_recvd, 2)
                    while is_using.value:
                        time.sleep(0.2)

                    is_using.value = 1
                    response = await self.eval_client.send_to_server_w_res(to_send)
                    is_using.value = 0
                    last_recvd = response
                    print('Send to eval server: ', to_send)
                    eval_client_to_game_engine.put(response)

                    if eval_track_p1.value:
                        eval_track_p2.value = 0
                        eval_track_p1.value = 0
                    else:
                        eval_track_p2.value = 1
                    # send
            
                time.sleep(0.1)
            
            except EvalDisconnectException:
                    print('EVAL ERROR, RETRY')
            except Exception as e:
                print(e)
                break
            except:
                self.eval_client.close_client()
                self.eval_client.is_running = False
                print('Terminating Eval Client Job')
                break
    
    def eval_timeout_job(self, eval_client_to_game_engine, latest_to_eval_timeout, is_node_connected_p1, is_node_connected_p2, eval_track_p1, eval_track_p2, is_using):
        while self.eval_client.is_running:
            try:
                asyncio.run(self.eval_timeout_task(eval_client_to_game_engine, latest_to_eval_timeout, is_node_connected_p1, is_node_connected_p2, eval_track_p1, eval_track_p2, is_using))
            except Exception as e:
                print(e, 'error at eval timeout')
                break
            except:
                break
            
        self.close_job()
        return True
    
                
    async def eval_client_task(self, eval_client_to_server, eval_client_to_game_engine, latest_to_eval_timeout, player_id, eval_track_p1, eval_track_p2, is_using):
        
        while True:
            try:
                to_send = eval_client_to_server.get()
                if player_id == 1:
                    if eval_track_p1.value:
                        self.print(f'player {player_id} received twice for eval, discarding...', player_id)
                        continue
                else:
                    if eval_track_p2.value:
                        self.print(f'player {player_id} received twice for eval, discarding...', player_id)
                        continue
                
                while is_using.value:
                    time.sleep(0.2)

                is_using.value = 1
                response = await self.eval_client.send_to_server_w_res(to_send)
                is_using.value = 0

                if player_id == 1:
                    if eval_track_p2.value:
                        eval_track_p2.value = 0
                        eval_track_p1.value = 0
                    else:
                        eval_track_p1.value = 1
                else:
                    if eval_track_p1.value:
                        eval_track_p2.value = 0
                        eval_track_p1.value = 0
                    else:
                        eval_track_p2.value = 1

                latest_to_eval_timeout.put(response)
                if self.eval_client.is_running and response:
                    eval_client_to_game_engine.put(response)
                    time.sleep(1)
                    while True:
                        try:
                            eval_client_to_server.get_nowait()
                        except queue.Empty:
                            print('deleted actions in the queue for eval')
                            break
            except EvalDisconnectException:
                    print('EVAL ERROR, RETRY')
            except Exception as e:
                print(e)
                print('EVAL ERROR, RETRY')
            except:
                self.eval_client.close_client()
                self.eval_client.is_running = False
                print('Terminating Eval Client Job')
                break
        
        return True
    
    def eval_client_job(self, eval_client_to_server, eval_client_to_game_engine, latest_to_eval_timeout, conn_num, eval_track_p1, eval_track_p2, is_using):
        while self.eval_client.is_running:
            try:
                asyncio.run(self.eval_client_task(eval_client_to_server, eval_client_to_game_engine, latest_to_eval_timeout, conn_num + 1, eval_track_p1, eval_track_p2, is_using))
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
    


