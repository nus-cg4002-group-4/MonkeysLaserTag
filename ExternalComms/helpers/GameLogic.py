import json
from enum import Enum
from helpers.PlayerClass import Player
from helpers.PlayerClass import GestureID

class GameLogic:
    shootDMG = 10
    grenadeDMG = 30
    skillDMG = 10

    # player_1 = 0
    # player_2 = 0
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

    def subscribeFromEval(self, msgIn):
        # msg from eval
        # decode msgIn

        try:
            eval_output = msgIn
    
            if int(eval_output["player_id"]) == 1:
                currentPlayer = self.player_1
            elif int(eval_output["player_id"]) == 2:
                currentPlayer = self.player_2

            currentPlayer.action = "none"
            player1_state = eval_output["game_state"]["p1"]
            player2_state = eval_output["game_state"]["p2"]

            self.player_1.hp = player1_state["hp"]
            self.player_1.bullets = player1_state["bullets"]
            self.player_1.grenades = player1_state["grenades"]
            self.player_1.shieldHP = player1_state["shield_hp"]
            self.player_1.death = player1_state["deaths"]
            self.player_1.shieldCount = player1_state["shields"]

            self.player_2.hp = player2_state["hp"]
            self.player_2.bullets = player2_state["bullets"]
            self.player_2.grenades = player2_state["grenades"]
            self.player_2.shieldHP = player2_state["shield_hp"]
            self.player_2.death = player2_state["deaths"]
            self.player_2.shieldCount = player2_state["shields"]

        except Exception as e:
            print(e)
            pass
        except:
            pass

        return self.convert_to_json(self.player_1, self.player_2)

    

    def relay_logic(self, msgIn):
        #decode msgIn
        #msgIn: 
        # playerID, packetID, hit, health, shield
        # playerID, packetID, bullets

        msgIn_arugments = list(map(int, msgIn.split()))
        print(msgIn_arugments)
        
        if msgIn_arugments[0] == 1:
            # player 1
            currentPlayer = self.player_1
        elif msgIn_arugments[0] == 2:
            currentPlayer = self.player_2

        if msgIn_arugments[1] == 2:
            # packetID 1: hit, health, shield
            currentPlayer.reduceHP(10)
            pass      
        elif msgIn_arugments[1] == 3:
            #bullets
            currentPlayer.bullets = msgIn_arugments[2]
            currentPlayer.action = "gun"
            pass   
        return self.convert_to_json(self.player_1, self.player_2)

    def ai_logic(self, msgIn, can_see):
        # msgIn "playerId enum"
        # can_see "playerId hit/miss"
        args = list(map(int, msgIn.split()))
        can_see = list(map(int, can_see.split()))
        if args[0] == 1:
            #player 1
            currentPlayer = self.player_1
            enemyPlayer = self.player_2
            pass
        elif args[0] == 2:
            #player 2
            currentPlayer = self.player_2
            enemyPlayer = self.player_1
            pass

        if args[1] == -1: #none
            currentPlayer.action = "none"
            pass
        elif args[1] == 1: #shield
            currentPlayer.action = "shield"
            currentPlayer.shieldActivate()
            pass
        elif args[1] == 0: #grenade
            print("player " + str(currentPlayer.id) + " grenade player " + str(enemyPlayer.id))
            currentPlayer.action = "grenade"
            if currentPlayer.grenadeThrow():
                if can_see[1]:
                    enemyPlayer.reduceHP(self.grenadeDMG)
                pass
            pass
        elif args[1] == 2: #reload
            print("player " + str(currentPlayer.id) + " reload")
            currentPlayer.action = "reload"
            currentPlayer.reload()
            pass
        elif args[1] == 7: #web
            print("player 2 activate skill")
            currentPlayer.action = "web"
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            pass
        elif args[1] == 6: #portal
            currentPlayer.action = "portal"
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            pass
        elif args[1] == 6: #punch
            currentPlayer.action = "punch"
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            pass
        elif args[1] == 5: #hammer
            currentPlayer.action = "hammer"
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            pass
        elif args[1] == 4: #spear
            currentPlayer.action = "spear"
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            pass
        elif args[1] == 8: #logout
            currentPlayer.action = "logout"
            pass
        else:
            currentPlayer.action = "none"
            pass
        pass
        return self.convert_to_json(self.player_1, self.player_2)
    
    def convert_to_json(self, player1, player2):
        game_state_sent = {
            "player_id": player1.id,
            "action": player1.action,
            "game_state": {
                'p1': {
                    'hp': player1.hp,
                    'bullets': player1.bullets,
                    'grenades': player1.grenades,
                    'shield_hp': player1.shieldHP,
                    'deaths': player1.death,
                    'shields': player1.shieldCount
                },
                'p2': {
                    'hp': player2.hp,
                    'bullets': player2.bullets,
                    'grenades': player2.grenades,
                    'shield_hp': player2.shieldHP,
                    'deaths': player2.death,
                    'shields': player2.shieldCount
                },
            }
        }
        return json.dumps(game_state_sent)

# msg = "2 1 1 60 20"
# game = GameLogic()
# print(game.relay_logic(msg))
