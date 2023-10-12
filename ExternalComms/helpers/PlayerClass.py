from enum import Enum

class Player:
    def __init__(self, id) -> None:
        self.id: int = id
        self.maxHP: int = 100
        self.maxShieldHP: int = 30
        self.maxShieldCount: int = 3
        self.maxbullets: int = 6
        self.maxGrenades: int = 2
        self.bulletsDmg: int = 10
        self.grenadesDmg: int = 30
        self.skillDmg: int = 10

        self.hp: int = self.maxHP
        self.shieldHP: int = 0
        self.shieldCount: int = self.maxShieldCount
        self.bullets: int = self.maxbullets
        self.grenades: int = self.maxGrenades
        self.enemyDetected: int = 0
        self.action: int = 0
        self.death: int = 0
        self.kill = 0

    def updateState(self, action, visibility):
        self.action = action
        self.enemyDetected = visibility
        print("actionID: ", self.action)
        print("isEnemyVisible: ", self.enemyDetected)

    def isEnemyDetected(self, detected):
        return detected == 1

    def reduceHP(self, dmg):
        if self.shieldHP > 0:
            remainingShieldHP = self.shieldHP - dmg
            if remainingShieldHP > 0:
                self.shieldHP = remainingShieldHP
            else: 
                self.shieldHP = 0
                self.hp = self.hp - abs(remainingShieldHP)
        else:
            self.hp = self.hp - dmg

        if self.hp <= 0:
            print("respawn")
            self.respawn()

    def shieldActivate(self):
        if (self.shieldHP > 0 or self.shieldCount <= 0):
            pass
        else:
            self.shieldHP = self.maxShieldHP
            self.shieldCount -= 1

    def shoot(self):
        if (self.bullets > 0):
            self.bullets -= 1

    def grenadeThrow(self):
        if (self.grenades > 0):
            self.grenades -= 1
                    
    # def skillActivate(self):
    #     if (self.enemyDetected == 1):
    #         enemy.reduceHP(self.skillDmg)
    #         if enemy.hp <= 0:
    #                 self.kill += 1
    #                 self.respawn()

    def reload(self):
        if (self.bullets <= 0):
            self.bullets = self.maxbullets

    def respawn(self):
        if self.hp <= 0:
            self.hp = self.maxHP
            self.shieldHP = 0
            self.shieldCount = self.maxShieldCount
            self.bullets = self.maxbullets
            self.grenades = self.maxGrenades
            self.death += 1
        

class GestureID(Enum):
    Idle = 0
    Shoot = 1
    Grenade = 2
    Spiderman = 3
    Spear = 4
    Portal = 5
    Fist = 6
    Hammer = 7
    Shield = 8
    Reload = 9
    Camera = 10
    Logout = 11