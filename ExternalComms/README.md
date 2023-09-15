# External Comms

## About
``main.py``  manages communications between Ultra96, Evaluation Server, Relay Nodes, and Visualizer Server via multi-processing. It is the main script to be run on Ultra96. 

There are 4 main processes running:
1. __Eval Client Process__, which manages communication between eval server and game engine.
2. __Game Engine Process__, which communicates with eval client, relay server, and mqtt client processes for necessary data.
3. __Mqtt Client Process__, wchich manages communication between game engine and visualizer.
4. __Relay Server Process__, which manages communication beteen relay nodes and game engine.


## Pre-requisites
1. Ensure that __pycrypto__, __pyscrptodome__, and __paho-mqtt__ python packages are installed. If not, install like this:
```
$ pip3 install pycrypto
```
2. Fill up connection details at ``info.json``.

## Get Started
1. Ensure that Evaluation Server is running, and you have logged in via the client (index.html). Record the password at ``info.json`` under __eval.password__.
2. Run:
```
$ python3 main.py
```
3. You will be prompted to enter a number. Enter the port number indicated from the evaluation server.
4. To simulate communication with visualizer or relay nodes, run:
```
$ python3 mqtt_client_publisher.py
$ python3 mqtt_client_subscriber.py

$ python3 relay_node1.py
$ python3 relay_node2.py
```


## Test Individual Components


### Relay Communication
To simulate relay server, run:
```
$ python3 relay_test.py
```
This will run a relay server which accepts up to 2 relay node connections and receives messages. Modify indicated lines if you want to send dummy data to relay nodes.

To simulate relay nodes, run in order:
```
$ python3 relay_node1.py
$ python3 relay_node2.py
```
This will run relay nodes which connects to relay server and sends different messages to the server. Ensure that port configuration matches with the relay serve port configuration.

### Visualizer Communication
To simulate Mqtt client which publishes message to `hit_miss` topic, run:
```
$ python3 mqtt_client_publisher.py
```

To simulate Mqtt client which subscribes to `gamestate` topic, run:
```
$ python3 mqtt_client_subscriber.py
```
Modify the scripts to change topic name, etc.
