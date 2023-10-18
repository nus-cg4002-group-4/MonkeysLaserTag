import paho.mqtt.client as paho
from multiprocessing import Queue
import time
import certifi
import json

class MqttClient:
    def __init__(self):
        self.hit_miss_topic = 'hit_miss'
        self.game_state_topic = 'gamestate'
        self.request_topic = 'hit_miss_request'
        self.hostname = None
        self.port = None
        self.username = None
        self.pw = None
        self.client = None
        self.is_subscribed = False
    
    def on_connect(self, client, userdata, flags, rc):
        print('\nCONNACK received with code %d.' % (rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))
        self.is_subscribed = True

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected MQTT disconnection.")

    def on_message(self, client, userdata, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    
    def start_client(self, on_message_custom=None):
        # Read connection details
        f = open('./info.json')
        data = json.load(f)
        self.hostname, self.port = data['mqtt']['hostname'], data['mqtt']['port']
        self.username, self.pw = data['mqtt']['username'], data['mqtt']['password']
        f.close()

        # Connect
        self.client = paho.Client()
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = on_message_custom if on_message_custom else self.on_message

        self.client.tls_set(certifi.where())
        self.client.username_pw_set(self.username, self.pw)
        self.client.connect(host=self.hostname, port=self.port)
    
    def subscribe_to_topic(self, topic):
        self.client.subscribe(topic, qos=0)
        self.client.loop_forever()

    def publish_to_topic(self, topic, msg):
        self.client.publish(topic, msg, qos=0)

    def close_client(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.is_subscribed = False
