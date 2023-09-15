import time
from multiprocessing import Lock, Process, Queue, current_process

from helpers.RelayServer import RelayServer

class RelayTest:
    def __init__(self):
        self.relay_server = RelayServer()
        
        self.relay_server_process = None
        self.parser_process = None
        
        self.relay_server_to_parser = Queue()
        self.relay_server_to_node = Queue()
    
    def receive_from_relay_node_task(self, conn_socket):
        while True:
            try:
                msg = self.relay_server.receive_from_node(conn_socket)
                if not msg:
                    print('Empty message received.')
                    break

                print('Received from relay node: ', msg)
                self.relay_server_to_parser.put(msg)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
                break
    
    def send_to_relay_node_task(self, conn_socket):
        while True:
            # Uncomment these lines to simulate sending data to relay nodes
            # time.sleep(5)
            # self.relay_server_to_node.put('Test message')
            try:
                msg = self.relay_server_to_node.get()
                print('Sent to relay node: ', msg)
                self.relay_server.send_to_node(msg, conn_socket)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
                break
        
    def relay_server_job(self):
        processes = []
        conn_count = 0
        try:

            while conn_count < 2:
                conn_socket = self.relay_server.start_connection()
                print(f'Relay node {conn_count + 1} connected')

                process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_socket,), daemon=True)
                processes.append(process_receive)
                process_receive.start()

                process_send = Process(target=self.send_to_relay_node_task, args=(conn_socket,), daemon=True)
                processes.append(process_send)
                process_send.start()
                conn_count += 1
                time.sleep(.5)
        
            for p in processes:
                p.join()
        except Exception as e:
                print(e)

        except KeyboardInterrupt: 
            print('Terminating Relay Server Job')
        
        self.relay_server.close_connection()
        return True
    
    def start_processes(self):
        self.relay_server_process = Process(target=self.relay_server_job)
        self.relay_server_process.start()

        try:
            self.relay_server_process.join()
        except KeyboardInterrupt: 
            print('Terminating Relay Test')
        
        return True
    
if __name__ == "__main__":
    print ("running relay test")
    try:
        brain = RelayTest()
        brain.start_processes()
    except KeyboardInterrupt:
        print('Exiting')
