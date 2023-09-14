from enum import Enum

class GameEngine:
    
    def __init__(self) -> None:
        self.player_1 = Player(1)
        self.player_2 = Player(2)

    #logic
    def run(self):
        while True:
            if self.player_2.detected:
                if self.player_2.gestrueID == 1:
                    if self.player_1.shieldActivate:
                        self.player_1.hp -= 10
                        pass
                    pass
                pass
            else:
                pass
            pass
        

class Player:
    def __init__(self, id) -> None:
        self.id = id
        self.hp = 100
        self.shieldHp = 30
        self.shieldCount = 3
        self.shieldActivate = 0
        self.ammo = 6
        self.grenades = 2
        self.detected = 0
        self.gestureID = 0
    
class gestureID(Enum):
    Idle = 0
    Shoot = 1
    Grenade = 2
    SPIDERMAN = 3
    Spear = 4
    Portal = 5
    Fist = 6
    Hammer = 7
    Shield = 8
    Reload = 9
    Camera = 10
    Logout = 11
