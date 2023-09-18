import json

from enum import Enum
from PlayerClass import Player
from PlayerClass import GestureID

class GameEngine:
    
    def __init__(self) -> None:
        # player_1 = Player(1)
        # player_2 = Player(2)
        # player_list = [player_1, player_2]
        pass

    #logic
    def run(self):
        player_1 = Player(1)
        player_2 = Player(2)

        # read gamestate from json
        while True:
            userInput = input("Please enter playerID, action and enemy visibility: ") 
            arguments = userInput.split()
            print("playerID: ", arguments[0])
            print("Player Action: ", arguments[1])
            print("Enemy Visible: ", arguments[2])

            if (int(arguments[0]) - 1 == 0):
                player_1.updateState(int(arguments[1]), arguments[2])
            elif (int(arguments[0]) - 1 == 1):
                player_2.updateState(int(arguments[1]), arguments[2])

            print("player GestureID: ", player_2.gestureID)
            print("player GestureID: ", int(player_2.gestureID) == GestureID.Shoot.value)

            if int(player_2.gestureID) == GestureID.Shoot.value:
                print("player 2 shoot player 1")
                player_2.shoot(player_1)
                if int(player_2.enemyDetected) == 1:
                    player_1.reduceHP(10)
                pass
            elif int(player_2.gestureID) == GestureID.Grenade.value:
                print("player 2 grenade player 1")
                player_2.grenadeThrow(player_1)
                pass
            elif int(player_2.gestureID) >= GestureID.Spiderman.value and int(player_2.gestureID) <= GestureID.Hammer.value:
                print("player 2 activate skill")
                player_2.skillActivate(player_1)
            elif int(player_2.gestureID) == GestureID.Shield.value:
                print("player 2 shield activate")
                player_2.shieldActivate()
            elif int(player_2.gestureID) == GestureID.Reload.value:
                print("Player 2 Reload")
                player_2.reload()
            elif int(player_1.gestureID) == GestureID.Shoot.value:
                print("player 1 shoot player 2")
                player_1.shoot(player_2)
                if int(player_1.enemyDetected) == 1:
                    player_2.reduceHP(10)
                pass
            elif int(player_1.gestureID) == GestureID.Grenade.value:
                print("Player 1 grenade Player 2")
                player_1.grenadeThrow(player_2)
                pass
            elif int(player_1.gestureID) >= GestureID.Spiderman.value and int(player_1.gestureID) <= GestureID.Hammer.value:
                print("Player 1 activate skill")
                player_1.skillActivate(player_2)
            elif int(player_1.gestureID) == GestureID.Shield.value:
                print("player 1 shield activate")
                player_1.shieldActivate()
            elif int(player_1.gestureID) == GestureID.Reload.value:
                print ("Player 1 reload")
                player_1.reload()
                pass
            else:
                print("im failing")
            
            print("Player 1 states:  ")
            print("Player 1 HP: ", player_1.hp)
            print("Player 1 ShieldHP: ", player_1.shieldHP)
            print("Player 1 no. of Shield left: ", player_1.shieldCount)
            print("Player 1 bullets: ", player_1.ammo)
            print("Player 1 Grenades: ", player_1.grenades)
            print("Player 1 kill: ", player_1.kill)
            print("Player 1 Deaths: ", player_1.death)
            print("Player 1 Actions: ", player_1.gestureID)
            print("----------------------")
            print("Player 2 states:  ")
            print("Player 2 HP: ", player_2.hp)
            print("Player 2 ShieldHP: ", player_2.shieldHP)
            print("Player 2 no. of Shield left: ", player_2.shieldCount)
            print("Player 2 bullets: ", player_2.ammo)
            print("Player 2 Grenades: ", player_2.grenades)
            print("Player 2 kill: ", player_2.kill)
            print("Player 2 Deaths: ", player_2.death)
            print("Player 2 Actions: ", player_2.gestureID)
            # player1JSONString = json.dump(player_1)
            # player2JSONString = json.dump(player_2)
            # print(player1JSONString)
            # print(player2JSONString)
        # save gamestate to json

game = GameEngine()
game.run()

    #userInput = Input(playerID, action) 
        

# class Player:
#     def __init__(self, id) -> None:
#         self.id = id
#         self.hp = 100
#         self.shieldHp = 30
#         self.shieldCount = 3
#         self.shieldActivate = 0
#         self.ammo = 6
#         self.grenades = 2
#         self.detected = 0
#         self.gestureID = 0
    
# class gestureID(Enum):
#     Idle = 0
#     Shoot = 1
#     Grenade = 2
#     Spiderman = 3
#     Spear = 4
#     Portal = 5
#     Fist = 6
#     Hammer = 7
#     Shield = 8
#     Reload = 9
#     Camera = 10
#     Logout = 11
