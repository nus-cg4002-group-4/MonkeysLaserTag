import threading
import time
import queue
from PlayerClass import Player

class GameEngine:
    ammoDmg = 10
    grenadeDmg = 30
    skillDmg = 10

    def __init__(self) -> None:
        self.dataInputQueue = queue.Queue()
        self.dataOutputQueue = queue.Queue()
        self.player1 = Player(1)
        self.player2 = Player(2)

    def data_input_thread(self):
        while True:
            # simulate data input
            userInput = input("Please enter playerID, action, and enemy visibility: ") 

            arguments = userInput.split()
            print("playerID: ", arguments[0])
            print("Player Action: ", arguments[1])
            print("Enemy Visible: ", arguments[2])

            self.dataInputQueue.put(userInput)
            time.sleep(1)

    def game_logic_thread(self):
        while True:
            # Perform game logic procesing
            # print("Game Logic Processing")
            
            if not self.dataInputQueue.empty():
                dataIn = self.dataInputQueue.get()
                arguments = dataIn.split()
                if int(arguments[0]) == 1:
                    currentPlayer = self.player1
                    enemy = self.player2
                else:
                    currentPlayer = self.player2
                    enemy = self.player1
                
                if int(arguments[1]) == 1:
                    if currentPlayer.isEnemyDetected(int(arguments[2])) and int(currentPlayer.bullets) > 0:
                        enemy.reduceHP(self.ammoDmg)
                    currentPlayer.shoot()
                elif int(arguments[1]) == 2:
                    if currentPlayer.isEnemyDetected(int(arguments[2])) and int(currentPlayer.grenades) > 0:
                        enemy.reduceHP(self.grenadeDmg)
                    currentPlayer.grenadeThrow()
                elif int(arguments[1]) >= 3 and int(arguments[1]) <= 7:
                    if currentPlayer.isEnemyDetected(int(arguments[2])):
                        enemy.reduceHP(self.skillDmg)
                elif int(arguments[1]) == 8:
                    currentPlayer.shieldActivate()
                elif int(arguments[1]) == 9:
                    currentPlayer.reload()
                else:
                    print("im failing")
                
                print("Player 1 states:  ")
                print("Player 1 HP: ", self.player1.hp)
                print("Player 1 ShieldHP: ", self.player1.shieldHP)
                print("Player 1 no. of Shield left: ", self.player1.shieldCount)
                print("Player 1 bullets: ", self.player1.bullets)
                print("Player 1 Grenades: ", self.player1.grenades)
                print("Player 1 kill: ", self.player1.kill)
                print("Player 1 Deaths: ", self.player1.death)
                # print("Player 1 Actions: ", self.player1.gestureID)
                print("----------------------")
                print("Player 2 states:  ")
                print("Player 2 HP: ", self.player2.hp)
                print("Player 2 ShieldHP: ", self.player2.shieldHP)
                print("Player 2 no. of Shield left: ", self.player2.shieldCount)
                print("Player 2 bullets: ", self.player2.bullets)
                print("Player 2 Grenades: ", self.player2.grenades)
                print("Player 2 kill: ", self.player2.kill)
                print("Player 2 Deaths: ", self.player2.death)
                # print("Player 2 Actions: ", self.player2.gestureID)
            time.sleep(1)

    def data_output_thread(self):
        while True:
            # Perform data output
            # print("Data Output")

            if not self.dataInputQueue.empty():
                dataOUT = self.dataOutputQueue.get()
            time.sleep(1)

if __name__ == "__main__":
    gameEngine = GameEngine()

    # create threads
    data_input_thread = threading.Thread(target=gameEngine.data_input_thread)
    game_logic_thread = threading.Thread(target=gameEngine.game_logic_thread)
    data_output_thread = threading.Thread(target=gameEngine.data_output_thread)

    # Start Threads
    data_input_thread.start()
    game_logic_thread.start()
    # data_output_thread.start()
