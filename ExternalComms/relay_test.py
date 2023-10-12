import time
from multiprocessing import Lock, Process, Queue, current_process
import json
import asyncio
import random
from helpers.RelayServer import RelayServer, ClientDisconnectException
from jobs.RelayServerJobs import RelayServerJobs
from helpers.Parser import Parser

class RelayTest:
    def __init__(self):
        self.relay_server = RelayServer()
        self.parser = Parser()
        
        self.relay_server_process = None
        self.parser_process = None
        
        self.relay_server_to_engine = Queue()
        self.relay_server_to_node = Queue()

        self.is_client_connected = [False, False]

        self.relay_node_to_parser = Queue()
    def send_from_parser(self, node_to_parser, relay_server_to_engine):
        while True:
            try:
                data = node_to_parser.get()
                data_arr = self.parser.convert_to_arr(data)
                pkt_id, msg = self.parser.decide_dest(data_arr)
                if pkt_id == 1:
                    # hand
                    # send to ai
                    continue
                elif pkt_id == 2:
                    # goggle
                    relay_server_to_engine.put(msg)
                elif pkt_id == 3:
                    # bullet
                    relay_server_to_engine.put(msg)
            
                print('data arr', data_arr)
            except Exception as e:
                print(e, 'a')
                break
            except:
                break
    

    async def receive_from_relay_node(self, conn_socket_num, node_to_parser):
        print('recv from relay node')
        print(conn_socket_num)
        try:
            msg = await self.relay_server.receive_from_node(conn_socket_num)
            if self.relay_server.is_running:
                node_to_parser.put(msg)
                print('Received from relay node: ', msg)

        except Exception as e:
            print(e)
            
    def receive_from_relay_node_task(self, conn_socket_num, relay_node_to_parser):
        print(conn_socket_num)
        while self.relay_server.is_running:
            try:
                asyncio.run(self.receive_from_relay_node(conn_socket_num, relay_node_to_parser))
            except Exception as e:
                print(e)
                break
            except:
                break
        print('not running')
    
    def get_dummy_eval_state_json(self):
        state = {
            'player_id': 1,
            'action': random.choice(['grenade', 'portal', 'shield']),
            'game_state': {
                'p1': {
                    'health': 100
                }
            }
        }   
        return state

    def get_dummy_packet(self):
        packet = self.get_dummy_eval_state_json()

        p = json.dumps(packet).encode()
        return str(len(p)) + '_' + p.decode()
    
    def send_to_relay_node_task(self, conn_socket_num, relay_server_to_node):
        print('start sending')
        while True:
            try:
                # Send dummy message to relay node every 10 s
                
                #msg = relay_server_to_node.get()
                msg = self.get_dummy_packet()
                print('Sent to relay node: ', msg)
                self.relay_server.send_to_node(msg.encode(), conn_socket_num)
                time.sleep(5)
            except Exception as e:
                print(e, 'got errrr')
                break
            except:
                break
    # def relay_server_client1_job(self, relay_server_to_engine, relay_server_to_node):
    #     conn_count = 0
    #     processes = []
    #     try:
                
    #             print(f'Relay node {conn_count + 1} connect')

    #             process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_count, relay_server_to_engine), daemon=True)
    #             processes.append(process_receive)
    #             process_receive.start()

    #             process_send = Process(target=self.send_to_relay_node_task, args=(conn_count, relay_server_to_node), daemon=True)
    #             processes.append(process_send)
    #             process_send.start()

    #             print('start')
    #             try:
    #                 for p in processes:
    #                     p.join()
    #             except ClientDisconnectException:
    #                 print('client disconnected')

    #             except KeyboardInterrupt: 
    #                 print('Terminating Relay Server Job')

    #     except Exception as e:
    #         print(e, 'err')
    #         break
    #     except:
    #         break
    #     else:
    #         conn_count += 1
    #         time.sleep(.5)

    #     self.close_job()
    #     return True
        
    def relay_server_job(self, relay_server_to_engine, relay_server_to_node):
        conn_count = 0
        processes = []
        process_parse = Process(target=self.send_from_parser, args=(self.relay_node_to_parser, relay_server_to_engine), daemon=True)
        processes.append(process_parse)
        process_parse.start()

        while conn_count < 2:
            try:
                conn_socket = self.relay_server.start_connection(conn_count)
                print(f'Relay node {conn_count + 1} connect')

                process_receive = Process(target=self.receive_from_relay_node_task, args=(conn_count, self.relay_node_to_parser), daemon=True)
                processes.append(process_receive)
                process_receive.start()

                process_send = Process(target=self.send_to_relay_node_task, args=(conn_count, relay_server_to_node), daemon=True)
                processes.append(process_send)
                process_send.start()
                print('started')

                print('start')
            except Exception as e:
                print(e, 'err')
                break
            except:
                break
            else:
                conn_count += 1
                time.sleep(.5)
        
        try:
            for p in processes:
                p.join()

        except KeyboardInterrupt: 
            print('Terminating Relay Server Job')

        self.close_job()
        return True
    
    def close_job(self):
        self.relay_server.close_connection()
    
    def start_processes(self):
        relay_server_jobs = RelayTest()
        relay_server_process = Process(target=relay_server_jobs.relay_server_job, 
                                                args=(self.relay_server_to_engine, self.relay_server_to_node))
        relay_server_process.start()

        try:
            relay_server_process.join()
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
