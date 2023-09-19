import time
from multiprocessing import Lock, Process, Queue, current_process, Manager

from helpers.MqttClient import MqttClient


class MqttClientJobs:
    def __init__(self):
        self.mqtt_client1 = MqttClient()
        self.mqtt_client2 = MqttClient()
        self.processes = []

    # def receive_from_vis_task(self, vis_to_engine):
        
    #     while True:
    #         try:
    #             msg = vis_to_engine.get()
    #             print('Received from hit_miss: ', msg)
    #         except:
    #             break
    
    def send_to_vis_task(self, engine_to_vis):
        while True:
            try:
                msg = engine_to_vis.get()
                print('Sent to Visualizer: ', msg)
                self.mqtt_client2.publish_to_topic(self.mqtt_client2.game_state_topic, msg)
            except:
                break
    
    def mqtt_client_job(self, engine_to_vis, vis_to_engine):
        def on_message_hit_miss(client, userdata, msg):
            vis_to_engine.put(str(msg.payload))

        try:
            self.mqtt_client1.start_client(on_message_hit_miss)
            self.mqtt_client2.start_client()

            # Thread for subscription
            self.mqtt_client1.subscribe_to_topic(self.mqtt_client1.hit_miss_topic)

            process_send_to_vis = Process(target=self.send_to_vis_task, args=(engine_to_vis,), daemon=True)
            self.processes.append(process_send_to_vis)
            process_send_to_vis.start()

            for p in self.processes:
                p.join()
        except Exception as e:
            print(e)
            

        except KeyboardInterrupt:
            print('Terminating Mqtt Client Job')
        
        self.close_job()
        return True
    
    def close_job(self):
        self.mqtt_client1.close_client()
        self.mqtt_client2.close_client()
        print('Closed Mqtt Connection')