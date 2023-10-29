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

    def subscribeFromEval(self, msgIn, player_1, player_2):
        # msg from eval
        # decode msgIn

        try:
            eval_output = json.loads(msgIn)

            player_1.set_action("none")
            player_2.set_action("none")

            player1_state = eval_output["p1"]
            player2_state = eval_output["p2"]

            player_1.set_state(player1_state)
            player_2.set_state(player2_state)    

        except Exception as e:
            print(e)
            pass
        except:
            pass
        print('-----------------')

        return self.convert_to_json(player_1, player_2, 1)

    

    def relay_logic(self, msgIn, player_1, player_2):
        #decode msgIn
        #msgIn: 
        # playerID, packetID, hit, health, shield
        # playerID, packetID, bullets

        msgIn_arugments = list(map(int, msgIn.split()))
        is_shoot = False
        
        if msgIn_arugments[0] == 1:
            # player 1
            currentPlayer = player_1
            enemyPlayer = player_2
            player_id = 1
        elif msgIn_arugments[0] == 2:
            currentPlayer = player_2
            enemyPlayer = player_1
            player_id = 2

        if msgIn_arugments[1] == 2:
            # packetID 1: hit, health, shield
            currentPlayer.reduceHP(self.skillDMG)
            currentPlayer.set_action("none")
            return is_shoot, self.convert_to_json(player_1, player_2, 1 if player_id == 2 else 2)
        elif msgIn_arugments[1] == 3:
            #bullets
            is_shoot = currentPlayer.shoot()
            currentPlayer.set_action("gun")
        return is_shoot, self.convert_to_json(player_1, player_2, player_id)

    def ai_logic(self, msgIn, can_see, player_1, player_2, can_reload):
        # msgIn "playerId enum"
        # can_see "playerId hit/miss"
        args = list(map(int, msgIn.split()))
        can_see = list(map(int, can_see.split()))
        print('args', args)
        if args[0] == 1:
            #player 1
            currentPlayer = player_1
            enemyPlayer = player_2
            player_id = 1
        elif args[0] == 2:
            #player 2
            currentPlayer = player_2
            enemyPlayer = player_1
            player_id = 2
      
        if args[1] == -1: #none
            currentPlayer.set_action("none")
            
        elif args[1] == 1: #shield
            currentPlayer.set_action("shield")
            currentPlayer.shieldActivate()
            
        elif args[1] == 0: #grenade
            print("player " + str(currentPlayer.get_id()) + " grenade player " + str(enemyPlayer.get_id()))
            currentPlayer.set_action("grenade")
            if currentPlayer.grenadeThrow():
                if can_see[1]:
                    enemyPlayer.reduceHP(self.grenadeDMG)

            
        elif args[1] == 2: #reload
            print("player " + str(currentPlayer.get_id()) + " reload")
            currentPlayer.set_action("reload")
            if can_reload:
                currentPlayer.reload()
            
        elif args[1] == 7: #web
            print("player 2 activate skill")
            currentPlayer.set_action("web")
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            
        elif args[1] == 6: #portal
            currentPlayer.set_action("portal")
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            
        elif args[1] == 3: #punch
            currentPlayer.set_action("punch")
            print('enemy was')
            enemyPlayer.print()
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            
        elif args[1] == 5: #hammer
            currentPlayer.set_action("hammer")
            print('enemy was')
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
                print('enemy later')
                enemyPlayer.print()
            
        elif args[1] == 4: #spear
            currentPlayer.set_action("spear")
            if can_see[1]:
                enemyPlayer.reduceHP(self.skillDMG)
            
        elif args[1] == 8: #logout
            currentPlayer.set_action("logout")
        else:
            currentPlayer.set_action("none")
        return self.convert_to_json(player_1, player_2, player_id)
    
    def convert_to_json(self, player1, player2, player_id):
        game_state_sent = {
            "player_id": player_id,
            "action": player1.get_action() if player_id == 1 else player2.get_action(),
            "game_state": {
                'p1': player1.get_player(),
                'p2': player2.get_player(),
            }
        }
        return json.dumps(game_state_sent)

# msg = "2 1 1 60 20"
# game = GameLogic()
# print(game.relay_logic(msg))
