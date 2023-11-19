import time
from multiprocessing import Lock, Process, Queue, current_process, Manager
import queue
import json
from helpers.EvalClient import EvalClient
from helpers.GameLogic import GameLogic
from multiprocessing.managers import BaseManager
from helpers.PlayerClass import Player
import random
from datetime import datetime

class MyManager(BaseManager): pass

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

class GameEngineJobs:

    # Attributes
    processes: list
    gameLogic: GameLogic
    player1: Player
    player2: Player

    def __init__(self, game_logic: GameLogic):
        self.processes = []
        self.gameLogic = game_logic
        MyManager.register('Player', Player)
        self.manager = MyManager()
        self.manager.start()
        self.player1 = self.manager.Player(1)
        self.player2 = self.manager.Player(2)
    
    def receive_from_eval_task(self, eval_to_engine, engine_to_vis, server_to_node_p1, server_to_node_p2, p1, p2):
        while True:
            try:
                msg = eval_to_engine.get()
                updated_game_state = self.gameLogic.subscribeFromEval(msg, p1, p2)
                server_to_node_p1.put(updated_game_state)
                server_to_node_p2.put(updated_game_state)
                engine_to_vis.put(updated_game_state)
            except Exception as e:
                print(e)
                break
            except:
                break
            else:

                print(f"{bcolors.OKGREEN} Received from eval server: {msg} {bcolors.ENDC}")
                print('------------------------------------------------------------------------------------------')
    
    def is_bullet_timeout(self, prev_time):
        if not prev_time:
            return False
        time_delta = (prev_time - datetime.now()).total_seconds()
        return time_delta > 0.5
    
    def print(self, msg, player_id):
        print(f"{bcolors.OKBLUE if player_id == 1 else bcolors.OKCYAN} {msg} {bcolors.ENDC}")
    
    def match_bullet_task_player(self, bullet_to_engine, engine_to_vis_gamestate, engine_to_eval, server_to_node_p1, server_to_node_p2, p1, p2, conn_num):
        player_id = conn_num + 1
        other_player_id = 2 if player_id == 1 else 1
        delete = False
        while True:
            try:
                # game engine
                signal, msg = bullet_to_engine.get()

                print(f'bullet engine player:{player_id} msg: {msg}')
                if signal == 2:
                    # goggle then bullet
                    try:
                        recv_signal, recv_msg = bullet_to_engine.get(timeout=0.5)
                        is_shoot, updated_game_state = self.gameLogic.relay_logic(recv_msg, p1, p2)
                        engine_to_vis_gamestate.put(updated_game_state)
                        if is_shoot:
                            is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2)
                        self.print(f'player {player_id} got shot', player_id)
                    except queue.Empty:
                        self.print(f'bullet timeout, regard as shot {player_id}', player_id)
                        delete = True
                     
                        is_shoot, updated_game_state = self.gameLogic.relay_logic(f'{player_id} 3 6', p1, p2)
                        engine_to_vis_gamestate.put(updated_game_state)
                        if is_shoot:
                            is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2)

                elif signal == 3:
                    # bullet then goggle
                    is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2, False)
                    # engine_to_vis_gamestate.put(updated_game_state)
                    recv_signal = 0
                    if is_shoot:
                        try:
                            recv_signal, recv_msg = bullet_to_engine.get(timeout=0.5)
                            is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2, True)
                            engine_to_vis_gamestate.put(updated_game_state)
                            self.print(f'player {player_id} successfully sent bullet', player_id)
                        except queue.Empty:
                            delete = True
                            is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2, True)
                            engine_to_vis_gamestate.put(updated_game_state)
                            self.print(f'goggle timeout, regard as no shot {player_id}', player_id)
                            
                    if recv_signal == 2 and is_shoot:
                        is_shoot, updated_game_state = self.gameLogic.relay_logic(recv_msg, p1, p2)
                

                if signal == 8 or signal == 9:
                    engine_to_vis_gamestate.put(msg)
                    self.print(f'connection state: {msg}', player_id)
                        
                else:
                    self.print(f'updated game state: {updated_game_state}', player_id)
                    engine_to_eval.put(updated_game_state)
                    server_to_node_p1.put(updated_game_state)
                    server_to_node_p2.put(updated_game_state)
                    updated_game_state_none = self.gameLogic.convert_to_json_none(p1, p2, other_player_id)
                    engine_to_vis_gamestate.put(updated_game_state_none)
                    if delete:
                        while True:
                            try:
                                bullet_to_engine.get_nowait()
                            except queue.Empty:
                                print('deleted actions in the queue')
                                break
                    delete = False
                
            except Exception as e:
                print(e, 'at game engine')
                break
            except:
                break
    
    

        
    def gen_action_task_player(self, action_to_engine, engine_to_vis_gamestate, engine_to_eval, vis_to_engine, server_to_node_p1, server_to_node_p2, p1, p2, conn_num):
        delete = False
        player_id = conn_num + 1
        bullet_start = None

        while True:
            try:
                # game engine
                signal, msg = action_to_engine.get()
                print(f'game engine {player_id}: {msg}')
                hit_miss = f'{player_id} 1'
                if signal == 1:
                    # ai nodes
                    #dummy ai input
                    #get message input from AI function format:: "player_id enum"
                    id = int(msg[2])
                    if id == 2 or id == 1 or id == 8: #reload
                        updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2, True)

                    if  id >= 3 and id <= 7 or id == 0: #grenades, and all skill
                        engine_to_vis_gamestate.put('r ' + str(player_id))
                        try:
                            hit_miss = vis_to_engine.get(timeout=1.3)
                            print('recv from viz ', player_id, hit_miss)
                        except queue.Empty:
                            print(f'timeout for viz hit_miss {player_id}')
                        print(hit_miss)

                        updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2, False)  
                
                    self.print(f'udpated game state {updated_game_state}', player_id)
                    engine_to_eval.put(updated_game_state)
                    engine_to_vis_gamestate.put(updated_game_state)
                    server_to_node_p1.put(updated_game_state)
                    server_to_node_p2.put(updated_game_state)

                if delete:
                    while True:
                        try:
                            action_to_engine.get_nowait()
                        except queue.Empty:
                            print('deleted actions in the queue')
                            break

                delete = False
                
            except Exception as e:
                print(e, 'at game engine')
                break
            except:
                break
    
    
    def game_engine_job(self, eval_to_engine, engine_to_eval_p1, engine_to_eval_p2, engine_to_vis_gamestate, vis_to_engine_p1, action_to_engine_p1, server_to_node_p1, bullet_to_engine_p1, vis_to_engine_p2, action_to_engine_p2, server_to_node_p2, bullet_to_engine_p2):
        
        try:
            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(eval_to_engine, engine_to_vis_gamestate, server_to_node_p1, server_to_node_p2, self.player1, self.player2), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action_p1 = Process(target=self.gen_action_task_player, args=(action_to_engine_p1, engine_to_vis_gamestate, engine_to_eval_p1, vis_to_engine_p1, server_to_node_p1, server_to_node_p2, self.player1, self.player2, 0), daemon=True)
            self.processes.append(process_gen_action_p1)
            process_gen_action_p1.start()

            process_gen_action_p2 = Process(target=self.gen_action_task_player, args=(action_to_engine_p2, engine_to_vis_gamestate, engine_to_eval_p2, vis_to_engine_p2, server_to_node_p1, server_to_node_p2, self.player1, self.player2, 1), daemon=True)
            self.processes.append(process_gen_action_p2)
            process_gen_action_p2.start()

            process_match_bullet_p1 = Process(target=self.match_bullet_task_player, args=(bullet_to_engine_p1, engine_to_vis_gamestate, engine_to_eval_p1, server_to_node_p1, server_to_node_p2, self.player1, self.player2, 0), daemon=True)
            self.processes.append(process_match_bullet_p1)
            process_match_bullet_p1.start()
            
            process_match_bullet_p2 = Process(target=self.match_bullet_task_player, args=(bullet_to_engine_p2, engine_to_vis_gamestate, engine_to_eval_p2, server_to_node_p1, server_to_node_p2, self.player1, self.player2, 1), daemon=True)
            self.processes.append(process_match_bullet_p2)
            process_match_bullet_p2.start()

            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        except Exception as e:
            print(e)
        
        return True

    


        
    
    
    
