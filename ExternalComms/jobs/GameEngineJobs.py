import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import json
from helpers.EvalClient import EvalClient
from helpers.GameLogic import GameLogic

class GameEngineJobs:

    # Attributes
    processes: list
    gameLogic: GameLogic

    def __init__(self, game_logic: GameLogic):
        self.processes = []
        self.gameLogic = game_logic
    
    def receive_from_eval_task(self, eval_to_engine):
        while True:
            try:
                msg = eval_to_engine.get()
                self.gameLogic.subscribeFromEval(msg)
            except:
                break
            else:
                print('Received from eval server ', msg)
    
    def receive_from_ai_task(self, action_to_engine):
        while True:
            try:
                action_to_engine.put((1, '1 3'))
                time.sleep(5)
                print('put')
            
            except Exception as e:
                print(e)
                break
            except e:
                break


    def gen_action_task(self, action_to_engine, engine_to_vis_gamestate, engine_to_vis_hit, engine_to_eval, vis_to_engine, server_to_node):
        while True:
            
            # game engine
            msg, signal = action_to_engine.get()
            print(msg, 'game engine')
            if msg == 2:
                # relay nodes
                #engine_to_vis_hit.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )
                #hit_miss = vis_to_engine.get()

                updated_game_state = self.gameLogic.relay_logic(signal)
            elif msg == 3:
                # relay nodes
                #engine_to_vis_hit.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )
                #hit_miss = vis_to_engine.get()

                updated_game_state = self.gameLogic.relay_logic(signal)
            elif msg == 1:
                # ai nodes
                #dummy ai input
                msgIn = "1 3" #get message input from AI function format:: "player_id enum"
                id = int(msgIn[2])
                if  id >= 4 and id <= 8 or id == 2: #grenades, and all skill
                    engine_to_vis_hit.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )
                    hit_miss = vis_to_engine.get()
                updated_game_state = self.gameLogic.ai_logic(msgIn, msg)     
            # game_state_str = json.dumps(updated_game_state)
            engine_to_eval.put(updated_game_state)
            engine_to_vis_gamestate.put(updated_game_state)
            server_to_node.put(updated_game_state)

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
            process_rcv_from_ai = Process(target=self.receive_from_ai_task, args=(action_to_engine,), daemon=True)
            self.processes.append(process_rcv_from_ai)
            process_rcv_from_ai.start()

            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(eval_to_engine,), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action = Process(target=self.gen_action_task, args=(action_to_engine, engine_to_vis_gamestate, engine_to_vis_hit, engine_to_eval, vis_to_engine, server_to_node), daemon=True)
            self.processes.append(process_gen_action)
            process_gen_action.start()
            

            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        except Exception as e:
            print(e)
        
        return True

    


        
    
    
    