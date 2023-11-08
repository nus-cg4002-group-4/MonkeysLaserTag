import time
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
    
    async def eval_client_task(self, eval_client_to_server, eval_client_to_game_engine, player_id, is_node_connected_p1, is_node_connected_p2, eval_track_p1, eval_track_p2):
        last_recvd = EvalClient.get_dummy_eval_state_str()
        while True:
            try:
                to_send = eval_client_to_server.get(timeout=self.timeout)
                if player_id == 1:
                    if eval_track_p1.value:
                        self.print(f'player {player_id} received twice for eval, discarding...', player_id)
                        continue
                else:
                    if eval_track_p2.value:
                        self.print(f'player {player_id} received twice for eval, discarding...', player_id)
                        continue
                
                response = await self.eval_client.send_to_server_w_res(to_send)
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

                last_recvd = response
                if self.eval_client.is_running and response:
                    eval_client_to_game_engine.put(response)
                    time.sleep(1)
                    while True:
                        try:
                            eval_client_to_server.get_nowait()
                        except queue.Empty:
                            print('deleted actions in the queue for eval')
                            break
            except queue.Empty:
                try:
                    if is_node_connected_p1.value and is_node_connected_p2.value:
                        print('Time out from game engine. Sending random game state for player ', player_id)
                        if player_id == 1:
                            if eval_track_p1.value:
                                self.print(f'player {player_id} received twice for eval, discarding...', player_id)
                                continue
                        else:
                            if eval_track_p2.value:
                                self.print(f'player {player_id} received twice for eval, discarding...', player_id)
                                continue
                        p1 = Player(1)
                        p2 = Player(2)
                        prev = self.game_logic.subscribeFromEval(last_recvd, p1, p2)
                        msg = str(player_id) + ' ' + str(random.choice([7, 6, 3, 5, 4]))
                        hit_miss = str(player_id) + ' 1'
                        to_send = self.game_logic.ai_logic(msg, hit_miss, p1, p2, False)
                        response = await self.eval_client.send_to_server_w_res(to_send)

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

                        last_recvd = response
                        print('Send to eval server: ', to_send)
                        eval_client_to_game_engine.put(response)

                        time.sleep(1)
                        while True:
                            try:
                                eval_client_to_server.get_nowait()
                            except queue.Empty:
                                print('deleted actions in the queue for eval')
                                break

                    else:
                        print('Time out from game engine but beetles are still disconnected for player ', player_id)
                except EvalDisconnectException:
                    print('EVAL ERROR FOR DISCONN, RETRY')
                except Exception as e:
                    print(e)
                    print('EVAL ERROR, RETRY')
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
    
    def eval_client_job(self, eval_client_to_server, eval_client_to_game_engine, conn_num, is_node_connected_p1, is_node_connected_p2, eval_track_p1, eval_track_p2):
        while self.eval_client.is_running:
            try:
                asyncio.run(self.eval_client_task(eval_client_to_server, eval_client_to_game_engine, conn_num + 1, is_node_connected_p1, is_node_connected_p2, eval_track_p1, eval_track_p2))
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
    


