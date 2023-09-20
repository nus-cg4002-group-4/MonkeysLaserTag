import time
from multiprocessing import Lock, Process, Queue, current_process
import queue
import json
from helpers.EvalClient import EvalClient

class GameEngineJobs:
    def __init__(self):\
        self.processes = []
    
    def receive_from_mqtt_task(self, vis_to_engine):
        while True:
            try:
                msg = vis_to_engine.get()
                print('Received from hit_miss: ', msg)
            except:
                break
    
    # def send_to_mqtt_task(self, engine_to_vis):
    #     while True:
    #         try:
    #             engine_to_vis.put('Hi visualizer')
    #             time.sleep(8)
    #         except:
    #             break
    
    def receive_from_eval_task(self, eval_to_engine):
        while True:
            try:
                msg = eval_to_engine.get()
            except:
                break
            else:
                print('Received from eval server ', msg)
    
    def gen_action_task(self, relay_to_engine, engine_to_vis, engine_to_eval):
        while True:
            try:
                signal = relay_to_engine.get()
                state = EvalClient.get_dummy_eval_state_json()
                engine_to_eval.put(json.dumps(state))
                if state['action'] == 'grenade':
                    engine_to_vis.put('request ' + time.strftime("%H:%M:%S", time.localtime()) )
            except:
                break
    
    # def send_to_eval_task(self, engine_to_eval):
    #     while True:
    #         try:
    #             engine_to_eval.put(EvalClient.get_dummy_eval_state())
    #             time.sleep(10)
    #         except:
    #             break
                
    
    def game_engine_job(self, eval_to_engine, engine_to_eval, engine_to_vis, vis_to_engine, relay_to_engine):
        
        try:
            process_rcv_from_mqtt = Process(target=self.receive_from_mqtt_task, args=(vis_to_engine,), daemon=True)
            self.processes.append(process_rcv_from_mqtt)
            process_rcv_from_mqtt.start()

            # process_send_to_mqtt = Process(target=self.send_to_mqtt_task, args=(engine_to_vis,), daemon=True)
            # self.processes.append(process_send_to_mqtt)
            # process_send_to_mqtt.start()

            process_rcv_from_eval = Process(target=self.receive_from_eval_task, args=(eval_to_engine,), daemon=True)
            self.processes.append(process_rcv_from_eval)
            process_rcv_from_eval.start()

            process_gen_action = Process(target=self.gen_action_task, args=(relay_to_engine, engine_to_vis, engine_to_eval), daemon=True)
            self.processes.append(process_gen_action)
            process_gen_action.start()
            
            # process_send_to_eval = Process(target=self.send_to_eval_task, args=(engine_to_eval,), daemon=True)
            # self.processes.append(process_send_to_eval)
            # process_send_to_eval.start()

            for p in self.processes:
                p.join()

        except KeyboardInterrupt:
            print('Terminating Game Engine Job')
        
        return True
    


        
    
    
    