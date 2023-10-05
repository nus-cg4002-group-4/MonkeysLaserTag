from enum import Enum
from PlayerClass import Player
from PlayerClass import GestureID

class GameLogic:
    shootDMG = 10
    grenadeDMG = 30
    skillDMG = 10

    player_1 = 0
    player_2 = 0
    # player_1 = Player(1)
    # player_2 = Player(2)    
    
    def __init__(self) -> None:
        self.player_1 = Player(1)
        self.player_2 = Player(2)
        # player_list = [player_1, player_2]
        pass

    def actionHandler(self, dataIn):
        self.playerId = dataIn[0]
        self.playerAction = dataIn[1]
        pass

    def visualHandler(self, dataIn):
        pass

    # def subscribeFromVisualizer(self, msgIn):
    #     # hitmiss request
    #     # decode msgIn
    #     pass

    # def subscribeFromEval(self, msgIn):
    #     # msg from eval
    #     # decode msgIn
    #     pass

    def convert_to_json(self):
        pass

    def relay_logic(self, msgIn):
        pass

    def ai_logic(self, msgIn):
        pass

    #logic
    def run_game_logic(self):
        # player_1 = Player(1)
        # player_2 = Player(2)

        if int(self.player_2.gestureID) == GestureID.Shoot.value:
            print("player 2 shoot player 1")
            if (self.player_2.shoot()):
            # if int(self.player_2.enemyDetected) == 1:
                self.player_1.reduceHP(self.shootDMG)
                pass
        elif int(self.player_2.gestureID) == GestureID.Grenade.value:
            print("player 2 grenade player 1")
            if self.player_2.grenadeThrow():
                self.player_1.reduceHP(self.grenadeDMG)
                pass
        elif int(self.player_2.gestureID) >= GestureID.Spiderman.value and int(self.player_2.gestureID) <= GestureID.Hammer.value:
            print("player 2 activate skill")
            if self.player_2.skillActivate():
                pass
            # self.player_1.reduceHP(self.skillDMG)
        elif int(self.player_2.gestureID) == GestureID.Shield.value:
            print("player 2 shield activate")
            self.player_2.shieldActivate()
        elif int(self.player_2.gestureID) == GestureID.Reload.value:
            print("Player 2 Reload")
            self.player_2.reload()
        elif int(self.player_1.gestureID) == GestureID.Shoot.value:
            print("player 1 shoot player 2")
            self.player_1.shoot(self.player_2)
            # if int(self.player_1.enemyDetected) == 1:
            #     self.player_2.reduceHP(self.shootDMG)
            pass
        elif int(self.player_1.gestureID) == GestureID.Grenade.value:
            print("Player 1 grenade Player 2")
            self.player_1.grenadeThrow(self.player_2)
            # if (int(self.player_2.enemyDetected) == 1):
            #     self.player_2.reduceHP(self.grenadeDMG)
            pass
        elif int(self.player_1.gestureID) >= GestureID.Spiderman.value and int(self.player_1.gestureID) <= GestureID.Hammer.value:
            print("Player 1 activate skill")
            self.player_1.skillActivate(self.player_2)
            self.player_2.reduceHP(self.skillDMG)
        elif int(self.player_1.gestureID) == GestureID.Shield.value:
            print("player 1 shield activate")
            self.player_1.shieldActivate()
        elif int(self.player_1.gestureID) == GestureID.Reload.value:
            print ("Player 1 reload")
            self.player_1.reload()
            pass
        else:
            print("im failing")

        # sent gamestate json to visualizer

        
        print("Player 1 states:  ")
        print("Player 1 HP: ", self.player_1.hp)
        print("Player 1 ShieldHP: ", self.player_1.shieldHP)
        print("Player 1 no. of Shield left: ", self.player_1.shieldCount)
        print("Player 1 bullets: ", self.player_1.ammo)
        print("Player 1 Grenades: ", self.player_1.grenades)
        print("Player 1 kill: ", self.player_1.kill)
        print("Player 1 Deaths: ", self.player_1.death)
        print("Player 1 Actions: ", self.player_1.gestureID)
        print("----------------------")
        print("Player 2 states:  ")
        print("Player 2 HP: ", self.player_2.hp)
        print("Player 2 ShieldHP: ", self.player_2.shieldHP)
        print("Player 2 no. of Shield left: ", self.player_2.shieldCount)
        print("Player 2 bullets: ", self.player_2.ammo)
        print("Player 2 Grenades: ", self.player_2.grenades)
        print("Player 2 kill: ", self.player_2.kill)
        print("Player 2 Deaths: ", self.player_2.death)
        print("Player 2 Actions: ", self.player_2.gestureID)
        # player1JSONString = json.dump(player_1)
        # player2JSONString = json.dump(player_2)
        # print(player1JSONString)
        # print(player2JSONString)
        # save gamestate to json

# game = GameLogic()
# game.run()

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
