# Internal Communications

This folder contains the main logic for both the bluno beetles and relay nodes. 

## Relay Nodes

The logic for relay nodes reside in the folders of `/scripts/beetle_handler_<x>/`, where x refers to player 1 or player 2.

Inside each `/scripts/beetle_handler_<x>/` folder contains the following:

| File | Description | 
| :---- | :----------- |
| BeetleJobs.py | Contains the utility functions to send/receive data from `RelayNode.py` |
| RelayNode.py | Establish connections to the socket within the Ultra96 |
| beetle.py | Main bulk of the logic, contains the `Beetle()` class and `ReadDelegate()` class that defines the relay nodes utility functions. |
| constants.py | Supporting constants used in `beetle.py` |
| crc.py | Custom CRC function used in `beetle.py` | 
| exceptions.py | Custom exceptions used for `beetle.py` |
| internal_comms_main.py | Program that attaches `beetle.py` process to `RelayNode.py` and `BeetleJobs.py`. This is used to connect the full system together.  Hardware -> RelayNode -> External Comms | 
| main.py | Program that is used for local testing and debugging. Hardware -> RelayNode only |
| packet.py | Structs of the packets | 
| state.py | The states of RelayNode (Connect, Receive, Handshake) |
| write.py | Data collection utility functions |

## Beetles 

The logic for each relay node reside in the folder `/arduino_scripts/<component>/`

Used in evaluation: 
- `/right/` (P1)
- `/right_82/` (P2)
- `/vest/` (P1)
- `/vest_07/` (P2)

| File | Description | 
| :---- | :----------- |
| vest.ino | Main logic used for goggle. (stop-and-wait) |
| right.ino | Main logic used for gloves | 

## Running the files:

1. Wait for external comms to set up her socket server in Ultra96.
2. Ensure you are connected to SOC network
3. Run `sudo nice -20 python3 internal_comms_main.py` to get the process to be prioritised higher than the rest of the system processes.
4. If connection is refused, check the RelayNode.py's port numbers to ensure they are aligned with websocket servers. 2648x for P1 and 2659x for P2.
