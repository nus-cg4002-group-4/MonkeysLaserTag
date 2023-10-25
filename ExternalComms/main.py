import time
from multiprocessing import Lock, Process, Queue, current_process
import queue

from jobs.EvalClientJobs import EvalClientJobs
from jobs.RelayServerJobs import RelayServerJobs
from jobs.GameEngineJobs import GameEngineJobs
from jobs.MqttClientJobs import MqttClientJobs
from helpers.GameLogic import GameLogic


class Brain:
    def __init__(self):
        self.processes = []

        self.eval_client_process = None
        self.game_engine_process = None
        self.relay_server_process = None
        self.mqtt_client_process = None
        self.parser_process = None
        
        self.eval_client_jobs = None
        self.relay_server_jobs = None
        self.game_engine_jobs = None
        self.mqtt_client_jobs = None

        self.eval_client_to_server = Queue()
        self.eval_client_to_game_engine = Queue()
        self.relay_server_to_engine_p1 = Queue()
        self.relay_server_to_engine_p2 = Queue()
        self.relay_server_to_ai_p1 = Queue()
        self.relay_server_to_ai_p2 = Queue()
        self.relay_server_to_node = Queue()
        self.relay_server_to_node_p2 = Queue()
        self.game_engine_to_vis_gamestate_p1 = Queue()
        self.game_engine_to_vis_gamestate_p2 = Queue()
        self.game_engine_to_vis_hit = Queue()
        self.vis_to_game_engine_p1 = Queue()
        self.vis_to_game_engine_p2 = Queue()
        self.relay_server_to_parser = Queue()

    def start_processes(self):
        try:
            # Define the game logic instance
            self.game_logic = GameLogic()

            # DEFINE JOBS
            self.relay_server_jobs = RelayServerJobs()
            self.game_engine_jobs = GameEngineJobs(self.game_logic)
            self.mqtt_client_jobs = MqttClientJobs()
            
            
            # DEFINE PROCESSES
            # Mqtt Client Process
            self.mqtt_client_process = Process(target=self.mqtt_client_jobs.mqtt_client_job, 
                                                args=(self.game_engine_to_vis_gamestate_p1, 
                                                    self.game_engine_to_vis_gamestate_p2, 
                                                    self.vis_to_game_engine_p1,
                                                    self.vis_to_game_engine_p2))
            self.processes.append(self.mqtt_client_process)
            self.mqtt_client_process.start()

            # Game Engine Process
            self.game_engine_process = Process(target=self.game_engine_jobs.game_engine_job, 
                                                args=(self.eval_client_to_game_engine,
                                                    self.eval_client_to_server,
                                                    self.game_engine_to_vis_gamestate_p1, 
                                                    self.game_engine_to_vis_gamestate_p2, 
                                                    self.vis_to_game_engine_p1,
                                                    self.relay_server_to_engine_p1,
                                                    self.relay_server_to_node,
                                                    self.vis_to_game_engine_p2,
                                                    self.relay_server_to_engine_p2,))
            self.processes.append(self.game_engine_process)
            self.game_engine_process.start()


            # Parser Process
            self.relay_server_jobs.initialize()
            process_parse = Process(target=self.relay_server_jobs.send_from_parser, args=(self.relay_server_to_parser,
                                                                                        self.relay_server_to_engine_p1, 
                                                                                        self.relay_server_to_ai_p1, 
                                                                                        self.relay_server_to_engine_p2, 
                                                                                        self.relay_server_to_ai_p2), daemon=True)
            self.processes.append(process_parse)
            process_parse.start()
            
            # Relay Server Process
            relay_server_process_p1 = Process(target=self.relay_server_jobs.relay_server_job_player, 
                                                args=(self.relay_server_to_engine_p1, 
                                                    self.relay_server_to_node,
                                                    self.relay_server_to_ai_p1,
                                                    self.relay_server_to_parser,
                                                    0))
            self.processes.append(relay_server_process_p1)
            relay_server_process_p1.start()

            relay_server_process_p2 = Process(target=self.relay_server_jobs.relay_server_job_player, 
                                                args=(self.relay_server_to_engine_p2, 
                                                    self.relay_server_to_node,
                                                    self.relay_server_to_ai_p2,
                                                    self.relay_server_to_parser,
                                                    1))
            self.processes.append(relay_server_process_p2)
            relay_server_process_p2.start()

            process_send = Process(target=self.relay_server_jobs.send_to_relay_node_task, args=(self.relay_server_to_node,), daemon=True)
            self.processes.append(process_send)
            process_send.start()


             # Eval Client Process  
            self.eval_client_jobs = EvalClientJobs()
            self.eval_client_jobs.initialize()
                 
            self.eval_client_process = Process(target=self.eval_client_jobs.eval_client_job, 
                                                args=(self.eval_client_to_server, self.eval_client_to_game_engine))
            self.processes.append(self.eval_client_process)
            self.eval_client_process.start()
        
            for p in self.processes:
                p.join()
        except KeyboardInterrupt:
            print('Terminating Main')
        
        except Exception as e:
            print(e)
        finally:
            self.relay_server_jobs.close_job()

        return True
    

if __name__ == "__main__":
    print ("running eval client")
    brain = Brain()
    try:
        brain.start_processes()
    except KeyboardInterrupt:
        print('Exiting')
