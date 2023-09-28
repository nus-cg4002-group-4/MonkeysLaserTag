import paho.mqtt.client as paho
import time
import certifi
import json


def on_connect(client, userdata, flags, rc):
    print('CONNACK received with code %d.' % (rc))

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))


# Read connection details
f = open('info.json')
data = json.load(f)
hostname, port = data['mqtt']['hostname'], data['mqtt']['port']
username, pw = data['mqtt']['username'], data['mqtt']['password']
f.close()

# Connect
client = paho.Client()
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message

client.tls_set(certifi.where())
client.username_pw_set(username, pw)
client.connect(host=hostname, port=port)
print('START')

# Publish
while True:
    topic = 'gamestate'
    current_time = time.strftime("%H:%M:%S", time.localtime())
    (rc, mid) = client.publish(topic, current_time, qos=1)
    print(current_time)
    time.sleep(4)

