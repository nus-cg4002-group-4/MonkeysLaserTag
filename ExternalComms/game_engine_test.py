import time
from multiprocessing import Lock, Process, Queue, current_process, Manager
import queue
import json
from helpers.EvalClient import EvalClient
from helpers.GameLogic import GameLogic
from multiprocessing.managers import BaseManager
from helpers.PlayerClass import Player
import types

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
        # BaseManager.register('Player', Player)
        # self.manager = BaseManager()
        # self.manager.start()
        MyManager.register('Player', Player)
        self.manager = MyManager()
        self.manager.start()
        self.player1 = self.manager.Player(1)
        self.player2 = self.manager.Player(2)

    
    def receive_from_eval_task(self, p1, p2):
        while True:
            try:
                time.sleep(10)
                msg = EvalClient.get_dummy_response_from_eval_str()
                print(msg, 'msg')
                one, two, updated_game_state = self.gameLogic.subscribeFromEval(msg, p1, p2)
                print('received fom eval ', updated_game_state)
                p1.print()
                p2.print()
                one.print()
                two.print()
            except Exception as e:
                print(e)
                break
            except:
                break
            else:
                print('Received from eval server ', msg)
    
    

    def gen_action_task(self, p1, p2):
        while True:
            
            try:
                # game engine
                signal, msg = (1, '1 5')
                
                hit_miss = '1 1'
                print(signal, msg, 'game engine')
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
                        #hit_miss = vis_to_engine.get()
                    print('before update')
                    p2.print()
                    updated_game_state = self.gameLogic.ai_logic(msg, hit_miss, p1, p2)  
                    print('udpated game state ', updated_game_state)
                    print('after update')
                    p2.print()
                time.sleep(3)
            except Exception as e:
                print(e)
                break
            except:
                break
    
    
    def game_engine_job(self):
        try:
            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(self.player1, self.player2), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action = Process(target=self.gen_action_task, args=(self.player1, self.player2), daemon=True)
            self.processes.append(process_gen_action)
            process_gen_action.start()
            

            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        except Exception as e:
            print(e)
        
        return True

gl = GameLogic()
gej = GameEngineJobs(gl)
try:
    proc1 = Process(target=gej.game_engine_job)
    proc1.start()
    proc1.join()
except KeyboardInterrupt:
    print('Terminating Game Engine Job')
        
except Exception as e:
    print(e)


    


        
    
    
    
