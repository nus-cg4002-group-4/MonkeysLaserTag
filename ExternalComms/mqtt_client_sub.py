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
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection.")



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
client.on_disconnect = on_disconnect

client.tls_set(certifi.where())
client.username_pw_set(username, pw)
client.connect(host=hostname, port=port)
print('START')

# Subscribe
client.subscribe('hit_miss', qos=1)
client.loop_forever()
