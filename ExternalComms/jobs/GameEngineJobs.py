import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import json
from helpers.EvalClient import EvalClient
from SoftwareVisualizer.GameEngine.GameLogic import GameLogic

class GameEngineJobs:

    # Attributes
    processes: list
    gameLogic: GameLogic

    def __init__(self, game_logic: GameLogic):
        self.processes = []
        self.gameLogic = game_logic
    
    def receive_from_mqtt_task(self, vis_to_engine):
        while True:
            try:
                #dummy ai input
                msgIn = "1 2" #get message input from AI function
                
                can_see = vis_to_engine.get()
                # self.gameLogic.subscribeFromVisualizer(can_see);
                print('Received from hit_miss: ', msgIn, can_see)
            except:
                break
    
    def receive_from_eval_task(self, eval_to_engine):
        while True:
            try:
                msg = eval_to_engine.get()
                self.gameLogic.subscribeFromEval(msg);
            except:
                break
            else:
                print('Received from eval server ', msg)
    
    def gen_action_task(self, relay_to_engine, engine_to_vis_gamestate, engine_to_vis_hit, engine_to_eval, vis_to_engine):
        while True:
            try:
                # game engine
                msg = 0 # message queue coming from relay_node and dma
                signal = relay_to_engine.get()
                if msg == 0:
                    # relay nodes
                    updated_game_state = self.gameLogic.relay_logic(signal)
                elif msg == 1:
                    # ai nodes
                    #dummy ai input
                    msgIn = "1 2" #get message input from AI function format:: "player_id enum"
                    if msgIn[1] >= 4 and msgIn[1] <= 8 or msgIn[1] == 2: #grenades, and all skill
                        engine_to_vis_hit.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )
                    hit_miss = vis_to_engine.get()
                    updated_game_state = self.gameLogic.ai_logic(msgIn, hit_miss)     

                # game_state_str = json.dumps(updated_game_state)
                engine_to_eval.put(updated_game_state)
                engine_to_vis_gamestate.put(updated_game_state)
               
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
            except:
                break
    
    
    def game_engine_job(self, eval_to_engine, engine_to_eval, engine_to_vis_gamestate, engine_to_vis_hit, vis_to_engine, relay_to_engine):
        
        try:
            process_rcv_from_mqtt = Process(target=self.receive_from_mqtt_task, args=(vis_to_engine,), daemon=True)
            self.processes.append(process_rcv_from_mqtt)
            process_rcv_from_mqtt.start()

            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(eval_to_engine,), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action = Process(target=self.gen_action_task, args=(relay_to_engine, engine_to_vis_gamestate, engine_to_vis_hit, engine_to_eval), daemon=True)
            self.processes.append(process_gen_action)
            process_gen_action.start()
            

            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        return True

    


        
    
    
    