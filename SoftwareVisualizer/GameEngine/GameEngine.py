import json

from enum import Enum
from PlayerClass import Player

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
        player_list = [player_1, player_2]

        # read gamestate from json
        while True:
            userInput = input("Please enter playerID, action and enemy visibility: ") 
            arguments = userInput.split()
            print("playerID: ", arguments[0])
            print("Player Action: ", arguments[1])
            print("Enemy Visible: ", arguments[2])

            if (int(arguments[0]) - 1 == 0):
                player_1.updateState(arguments[1], arguments[2])
            elif (int(arguments[1]) - 1 == 1):
                player_2.updateState(arguments[1], arguments[2])

            if player_2.gestureID == 1:
                player_2.shoot(player_1)
                pass
            elif player_2.gestureID == 2:
                player_2.grenadeThrow(player_1)
                pass
            elif player_2.gestureID > 2 or player_2.gestureID <= 7:
                player_2.skillActivate(player_1)
            elif player_2.gestureID == 8:
                player_2.shieldActivate()
            elif player_2.gestureID == 9:
                player_2.reload()
            elif player_1.gestureID == 1:
                player_1.shoot(player_2)
                pass
            elif player_1.gestureID == 2:
                player_1.grenadeThrow(player_2)
                pass
            elif player_1.gestureID > 2 or player_1.gestureID <= 7:
                player_1.skillActivate(player_2)
            elif player_1.gestureID == 8:
                player_1.shieldActivate()
            elif player_1.gestureID == 9:
                player_1.reload()
            pass
            
            player1JSONString = json.dump(player_1)
            player2JSONString = json.dump(player_2)
            print(player1JSONString)
            print(player2JSONString)
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
#     SPIDERMAN = 3
#     Spear = 4
#     Portal = 5
#     Fist = 6
#     Hammer = 7
#     Shield = 8
#     Reload = 9
#     Camera = 10
#     Logout = 11
