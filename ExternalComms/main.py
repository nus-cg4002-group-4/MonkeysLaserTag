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
        self.relay_server_to_engine = Queue()
        self.relay_server_to_ai = Queue()
        self.relay_server_to_node = Queue()
        self.game_engine_to_vis_gamestate = Queue()
        self.game_engine_to_vis_hit = Queue()
        self.vis_to_game_engine = Queue()

    def start_processes(self):
        try:
            # Define the game logic instance
            self.game_logic = GameLogic()

            # DEFINE JOBS
            self.relay_server_jobs = RelayServerJobs()
            self.game_engine_jobs = GameEngineJobs(self.game_logic)
            self.mqtt_client_jobs = MqttClientJobs()
            
            
            # DEFINE PROCESSES
            # Game Engine Process
            self.game_engine_process = Process(target=self.game_engine_jobs.game_engine_job, 
                                                args=(self.eval_client_to_game_engine,
                                                    self.eval_client_to_server,
                                                    self.game_engine_to_vis_gamestate, 
                                                    self.game_engine_to_vis_hit,
                                                    self.vis_to_game_engine,
                                                    self.relay_server_to_engine,
                                                    self.relay_server_to_node))
            self.processes.append(self.game_engine_process)
            self.game_engine_process.start()

            # Mqtt Client Process
            self.mqtt_client_process = Process(target=self.mqtt_client_jobs.mqtt_client_job, 
                                                args=(self.game_engine_to_vis_gamestate, 
                                                    self.vis_to_game_engine))
            self.processes.append(self.mqtt_client_process)
            self.mqtt_client_process.start()

            # Relay Server Process
            self.relay_server_process = Process(target=self.relay_server_jobs.relay_server_job, 
                                                args=(self.relay_server_to_engine, 
                                                    self.relay_server_to_node,
                                                    self.relay_server_to_ai))
            self.processes.append(self.relay_server_process)
            self.relay_server_process.start()


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

        return True
    

if __name__ == "__main__":
    print ("running eval client")
    brain = Brain()
    try:
        brain.start_processes()
    except KeyboardInterrupt:
        print('Exiting')
