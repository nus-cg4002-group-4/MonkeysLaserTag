# External Comms

## About
``main.py``  manages communications between Ultra96, Evaluation Server, Relay Nodes, and Visualizer Server via multi-processing. It is the main script to be run on Ultra96. 

There are 4 main processes running:
1. __Eval Client Process__, which manages communication between eval server and game engine.
2. __Game Engine Process__, which communicates with eval client, relay server, and mqtt client processes for necessary data.
3. __Mqtt Client Process__, wchich manages communication between game engine and visualizer.
4. __Relay Server Process__, which manages communication beteen relay nodes and game engine.

Each job definition is located under the jobs folder. Helper functions are located under the helpers folder/


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
$ ./load_main.sh
```
3. You will be prompted to enter a number. Enter the port number indicated from the evaluation server.



## Test Individual Components

