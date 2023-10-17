import time
from multiprocessing import Lock, Process, Queue, current_process, Manager
import queue
import json
from helpers.EvalClient import EvalClient
from helpers.GameLogic import GameLogic
from multiprocessing.managers import BaseManager
from helpers.PlayerClass import Player

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
                engine_to_vis.put(updated_game_state)
                server_to_node.put(updated_game_state)
            except Exception as e:
                print(e)
                break
            except:
                break
            else:
                print('Received from eval server ', msg)
    
    

    def gen_action_task(self, action_to_engine, engine_to_vis_gamestate, engine_to_vis_hit, engine_to_eval, vis_to_engine, server_to_node, p1, p2):
        while True:
            
            try:
                # game engine
                signal, msg = action_to_engine.get()
                hit_miss = '1 1'
                if signal == 2:
                    # goggle

                    updated_game_state = self.gameLogic.relay_logic(msg, p1, p2)
                elif signal == 3:
                    # bullet

                    updated_game_state = self.gameLogic.relay_logic(msg, p1, p2)
                elif signal == 1:
                    # ai nodes
                    #dummy ai input
                    #get message input from AI function format:: "player_id enum"
                    id = int(msg[2])
                    print('id was ', id)
                    if  id >= 3 and id <= 7 or id == 0: #grenades, and all skill
                        print('i sent vis request')
                        engine_to_vis_gamestate.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )
                        #hit_miss = vis_to_engine.get()
                        #hit_miss = hit_miss[2:-1]
                        #print(hit_miss)

                    updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2)  
                    print('udpated game state ', updated_game_state)
                engine_to_eval.put(updated_game_state)
                engine_to_vis_gamestate.put(updated_game_state)
                server_to_node.put(updated_game_state)
                time.sleep(10)
            except Exception as e:
                print(e)
                break
            except:
                break

            # grab msg queues
            # if is relay node
            # run game_engine.relay_logic(msg)
            # sent gamestate json
            # else if is PMA (AI Gesture)
            # run game_engine.ai_logic(msg)
            # sent gamestate json

            # dummy inputs
            # signal = relay_to_engine.get()
            # state = EvalClient.get_dummy_eval_state_json()
            # state_str = json.dumps(state)
            # engine_to_eval.put(state_str)
            # engine_to_vis_gamestate.put(state_str)
            # if state['action'] == 'grenade':
            #     engine_to_vis_hit.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )

    
    
    def game_engine_job(self, eval_to_engine, engine_to_eval, engine_to_vis_gamestate, engine_to_vis_hit, vis_to_engine, action_to_engine, server_to_node):
        
        try:
            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(eval_to_engine, engine_to_vis_gamestate, server_to_node, self.player1, self.player2), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action = Process(target=self.gen_action_task, args=(action_to_engine, engine_to_vis_gamestate, engine_to_vis_hit, engine_to_eval, vis_to_engine, server_to_node, self.player1, self.player2), daemon=True)
            self.processes.append(process_gen_action)
            process_gen_action.start()
            

            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        except Exception as e:
            print(e)
        
        return True

    


        
    
    
    
