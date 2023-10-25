import time
from multiprocessing import Lock, Process, Queue, current_process, Manager

from helpers.MqttClient import MqttClient


class MqttClientJobs:
    def __init__(self):
        self.mqtt_client1 = MqttClient()
        self.mqtt_client2 = MqttClient()
        self.mqtt_client3 = MqttClient()
        self.processes = []

    # def receive_from_vis_task(self, vis_to_engine):
        
    #     while True:
    #         try:
    #             msg = vis_to_engine.get()
    #             print('Received from hit_miss: ', msg)
    #         except:
    #             break
    
    def send_to_vis_gamestate_p1_task(self, engine_to_vis):
        try:
            time.sleep(3)
            self.mqtt_client2.publish_to_topic(self.mqtt_client2.game_state_p1_topic, 'test')
            time.sleep(1)
            self.mqtt_client2.publish_to_topic(self.mqtt_client2.game_state_p1_topic, 'tt')

            print('Attempt mqtt test. Check on viz')
        except Exception as e:
            print(e, 'mqtt test fail')
            
        while True:
            try:
                msg = engine_to_vis.get()
                print('Sent gamestate to Visualizer: ')
                self.mqtt_client2.publish_to_topic(self.mqtt_client2.game_state_p1_topic, msg)
                time.sleep(0.4)
            except Exception as e:
                print(e)
                print('Attempt Mqtt re-publish')
                try:
                    self.mqtt_client2.close_client()
                except:
                    print('Failed to close. Starting new without closing.')
                self.mqtt_client2 = MqttClient()
                self.mqtt_client2.start_client()
                time.sleep(5)
            except:
                break
            
        try:
            self.mqtt_client2.close_client()
        except:
            pass
        print('Closed Mqtt Publish')
    
    def send_to_vis_gamestate_p2_task(self, engine_to_vis):
            
        while True:
            try:
                msg = engine_to_vis.get()
                print('Sent gamestate to Visualizer: ')
                self.mqtt_client3.publish_to_topic(self.mqtt_client3.game_state_p2_topic, msg)
                time.sleep(0.3)
            except Exception as e:
                print(e)
                print('Attempt Mqtt re-publish')
                try:
                    self.mqtt_client3.close_client()
                except:
                    print('Failed to close. Starting new without closing.')
                self.mqtt_client3 = MqttClient()
                self.mqtt_client3.start_client()
                time.sleep(5)
            except:
                break
            
        try:
            self.mqtt_client2.close_client()
        except:
            pass
        print('Closed Mqtt Publish')
        
    
    def recv_from_hit_miss_task(self, vis_to_engine_p1, vis_to_engine_p2):
        def on_message_hit_miss(client, userdata, msg):
            print(str(msg.payload), 'recv from viz')
            hit_miss = str(msg.payload)[2:-1]
            if hit_miss[0] == '1':
                vis_to_engine_p1.put(hit_miss)
            else:
                vis_to_engine_p2.put(hit_miss)

        while True:
            try:
                self.mqtt_client1.subscribe_to_topic(self.mqtt_client1.hit_miss_topic)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
                print('Attempt Mqtt re-subscribe')
                try:
                    self.mqtt_client1.close_client()
                except:
                    print('Failed to close. Starting new without closing.')
                self.mqtt_client1 = MqttClient()
                self.mqtt_client1.start_client(on_message_hit_miss)
                time.sleep(5)
            except:
                break
            
        try:
            self.mqtt_client1.close_client()
        except:
            pass
        print('Closed Mqtt Subscribe')
    
    def mqtt_client_job(self, engine_to_vis_gamestate_p1, engine_to_vis_gamestate_p2, vis_to_engine_p1, vis_to_engine_p2):
        def on_message_hit_miss(client, userdata, msg):
            print(str(msg.payload), 'recv from viz')
            hit_miss = str(msg.payload)[2:-1]
            if hit_miss[0] == '1':
                vis_to_engine_p1.put(hit_miss)
            else:
                vis_to_engine_p2.put(hit_miss)

        try:
            self.mqtt_client1.start_client(on_message_hit_miss)
            self.mqtt_client2.start_client()
            self.mqtt_client3.start_client()
            # self.mqtt_client3.start_client()

            # Thread for subscription
            process_recv_hit_miss = Process(target=self.recv_from_hit_miss_task, args=(vis_to_engine_p1, vis_to_engine_p2), daemon=True)
            self.processes.append(process_recv_hit_miss)
            process_recv_hit_miss.start()

            
            process_send_gamestate_p1 = Process(target=self.send_to_vis_gamestate_p1_task, args=(engine_to_vis_gamestate_p1,), daemon=True)
            self.processes.append(process_send_gamestate_p1)
            process_send_gamestate_p1.start()

            process_send_gamestate_p2 = Process(target=self.send_to_vis_gamestate_p2_task, args=(engine_to_vis_gamestate_p2,), daemon=True)
            self.processes.append(process_send_gamestate_p2)
            process_send_gamestate_p2.start()

            # process_send_request = Process(target=self.send_to_vis_hit_task, args=(engine_to_vis_hit,), daemon=True)
            # self.processes.append(process_send_request)
            # process_send_request.start()

            for p in self.processes:
                p.join()
        except Exception as e:
            print(e, 'at mqtt')
            

        except KeyboardInterrupt:
            print('Terminating Mqtt Client Job')
        
        #self.close_job()
        return True
    
    def close_job(self):
        self.mqtt_client1.close_client()
        self.mqtt_client2.close_client()
        # self.mqtt_client3.close_client()
        print('Closed Mqtt Connection')
