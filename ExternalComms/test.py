import time
from multiprocessing import Lock, Process, Queue, current_process, Manager
import queue
import json
from helpers.EvalClient import EvalClient
from helpers.GameLogic import GameLogic
from multiprocessing.managers import BaseManager
from helpers.PlayerClass import Player
import types

class MyManager(BaseManager): pass

class Test:
    def __init__(self):
        self.hp = 100
        self.ammo = 6
    
    def pr(self):
        print(f'HP: {self.hp} AMMO: {self.ammo}')
    
    def update(self, hp, ammo):
        self.hp = hp
        self.ammo = ammo
    
    def get(self):
        return (self.hp, self.ammo)

class Other:
    def reduceHp(self, t1):
        hp, ammo = t1.get()
        t1.update(hp - 10, ammo - 10)

other = Other()

def task1(t1):
    i, j = 1, 100
    while True:
        try:
            a, b = t1.get()
            other.reduceHp(t1)
            print('-------------- TASK 1 --------')
            t1.pr()
            time.sleep(2)
        except Exception as e:
            print(e)
            break
        except:
            break

def task2(t1):
    i, j = 1, 100
    while True:
        try:
            t1.update(i,j)
            print('-------------- TASK 2 --------')
            t1.pr()
            time.sleep(10)
        except Exception as e:
            print(e)
            break
        except:
            break
processes = []


MyManager.register('Test', Test)
manager = MyManager()
manager.start()
test = manager.Test()



try:
    p1 = Process(target=task1, args=(test,), daemon=True)
    processes.append(p1)
    p1.start()

    p2 = Process(target=task2, args=(test,), daemon=True)
    processes.append(p2)
    p2.start()
    
    for p in processes:
        p.join()

except KeyboardInterrupt:
    print('Terminating Game Engine Job')

except Exception as e:
    print(e)




    


        
    
    
    
