import time
from multiprocessing import Lock, Process, Queue, current_process, Manager
import queue
import json
from helpers.EvalClient import EvalClient
from helpers.GameLogic import GameLogic
from multiprocessing.managers import BaseManager
from helpers.PlayerClass import Player
import random

class MyManager(BaseManager): pass

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
    
    def receive_from_eval_task(self, eval_to_engine, engine_to_vis, server_to_node, p1, p2):
        while True:
            try:
                msg = eval_to_engine.get()
                updated_game_state = self.gameLogic.subscribeFromEval(msg, p1, p2)
                server_to_node.put(updated_game_state)
                if p1.get_action() == 'gun':
                    time.sleep(2)
                    engine_to_vis.put(updated_game_state)
            except Exception as e:
                print(e)
                break
            except:
                break
            else:
                print('Received from eval server ', msg)
    
    
    def gen_action_task_player(self, action_to_engine, engine_to_vis_gamestate, engine_to_eval, vis_to_engine, server_to_node, p1, p2, conn_num):
        delete = False
        while True:
            
            try:
                # game engine
                signal, msg = action_to_engine.get()
                print('game engine ', msg)
                hit_miss = '1 1'
                if signal == 2:
                    # goggle then bullet
                    is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2)
                    try:
                        recv_signal, recv_msg = action_to_engine.get(timeout=0.5)
                        is_shoot, updated_game_state = self.gameLogic.relay_logic(recv_msg, p1, p2)
                    except queue.Empty:
                        print('bullet timeout, regard as shot')
                        delete = True
                        is_shoot, updated_game_state = self.gameLogic.relay_logic(f'{conn_num + 1} 3 6', p1, p2)

                elif signal == 3:
                    # bullet then goggle
                    is_shoot, updated_game_state = self.gameLogic.relay_logic(msg, p1, p2)
                    engine_to_vis_gamestate.put(updated_game_state)
                    recv_signal = 0
                    if is_shoot:
                        try:
                            recv_signal, recv_msg = action_to_engine.get(timeout=0.5)
                        except queue.Empty:
                            delete = True
                            print('goggle timeout, regard as no shot')
                    if recv_signal == 2:
                        is_shoot, updated_game_state = self.gameLogic.relay_logic(recv_msg, p1, p2)
                elif signal == 1:
                    # ai nodes
                    #dummy ai input
                    #get message input from AI function format:: "player_id enum"
                    id = int(msg[2])
                    print('id was ', id)
                    if id == 2: #reload
                        updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2, False)
                        engine_to_vis_gamestate.put(updated_game_state)
                        print('udpated game state ', updated_game_state)
                        updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2, True)
                        engine_to_eval.put(updated_game_state)
                        server_to_node.put(updated_game_state)
                        continue
                    if  id >= 3 and id <= 7 or id == 0: #grenades, and all skill
                        
                        print('i sent vis request')
                        engine_to_vis_gamestate.put('r ' + str(conn_num + 1))
                        try:
                            hit_miss = vis_to_engine.get(timeout=1.3)
                            print('recv from viz ', hit_miss)
                        except queue.Empty:
                            hit_miss = '1 1'
                            print('timeout for viz hit_miss')
                        print(hit_miss)

                    updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2, False)  
                
                print('udpated game state ', updated_game_state)
                engine_to_eval.put(updated_game_state)
                engine_to_vis_gamestate.put(updated_game_state)
                server_to_node.put(updated_game_state)

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
    
    
    def game_engine_job(self, eval_to_engine, engine_to_eval, engine_to_vis_gamestate, vis_to_engine_p1, action_to_engine_p1, server_to_node, vis_to_engine_p2, action_to_engine_p2):
        
        try:
            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(eval_to_engine, engine_to_vis_gamestate, server_to_node, self.player1, self.player2), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action_p1 = Process(target=self.gen_action_task_player, args=(action_to_engine_p1, engine_to_vis_gamestate, engine_to_eval, vis_to_engine_p1, server_to_node, self.player1, self.player2, 0), daemon=True)
            self.processes.append(process_gen_action_p1)
            process_gen_action_p1.start()

            process_gen_action_p2 = Process(target=self.gen_action_task_player, args=(action_to_engine_p2, engine_to_vis_gamestate, engine_to_eval, vis_to_engine_p2, server_to_node, self.player1, self.player2, 1), daemon=True)
            self.processes.append(process_gen_action_p2)
            process_gen_action_p2.start()
            
            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        except Exception as e:
            print(e)
        
        return True

    


        
    
    
    
