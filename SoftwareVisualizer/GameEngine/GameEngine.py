from enum import Enum
from PlayerClass import Player

class GameEngine:
    
    def __init__(self) -> None:
        player_1 = Player(1)
        player_2 = Player(2)

    #logic
    def run(self):
        while True:
            if self.player_2.gestureID == 1:
                self.player_2.shoot(self.player_1)
                pass
            elif self.player_2.gestureID == 2:
                self.player_2.grenadeThrow(self.player_1)
                pass
            elif self.player_2.gestureID > 2 or self.player_2.gestureID <= 7:
                self.player_2.skillActivate(self.player_1)
            elif self.player_2.gestureID == 8:
                self.player_2.shieldActivate()
            elif self.player_2.gestureID == 9:
                self.player_2.reload()
            elif self.player_1.gestureID == 1:
                self.player_1.shoot(self.player_2)
                pass
            elif self.player_1.gestureID == 2:
                self.player_1.grenadeThrow(self.player_2)
                pass
            elif self.player_1.gestureID > 2 or self.player_1.gestureID <= 7:
                self.player_1.skillActivate(self.player_2)
            elif self.player_1.gestureID == 8:
                self.player_1.shieldActivate()
            elif self.player_1.gestureID == 9:
                self.player_1.reload()
            pass
        

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
