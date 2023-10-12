import time
from multiprocessing import Lock, Process, Queue, current_process
import json
from helpers.Dma import Dma
import sys, os

WINDOW = 80
REMOVE = 20
cfd = f'{sys.path[0]}/../HardwareAi/HLS_CNN'
dir = os.path.join(cfd, 'old_values_for_testing')

class DmaTest:
    def __init__(self):
        self.relay_server_to_ai = Queue()
        self.dma = Dma()

    def send_to_ai_task(self):
        while True:
            try:
                for file in os.listdir(dir):
                    if file.endswith(".in"):
                        print('Testing file', file)
                        f = open(os.path.join(dir, file), 'r')
                        data = f.read().split(',')
                        self.dma.send_to_ai(data)
            
            except Exception as e:
                print(e)
                break
            except e:
                break
    
    def receive_from_ai_task(self):
        while True:
            try:
                out = self.dma.recv_from_ai()
                print('out buffer', out)
            
            except Exception as e:
                print(e)
                break
            except e:
                break

    
if __name__ == "__main__":
    print ("running relay test")
    try:
        processes = []
        dma_test = DmaTest()
        dma_test.dma.initialize()

        process_send_to_ai = Process(target=dma_test.send_to_ai_task, daemon=True)
        processes.append(process_send_to_ai)
        process_send_to_ai.start()

        process_rcv_from_ai = Process(target=dma_test.receive_from_ai_task, daemon=True)
        processes.append(process_rcv_from_ai)
        process_rcv_from_ai.start()

        for p in processes:
            p.join()

    except KeyboardInterrupt:
        print('Exiting')
    
    except Exception as e:
        print(e)
