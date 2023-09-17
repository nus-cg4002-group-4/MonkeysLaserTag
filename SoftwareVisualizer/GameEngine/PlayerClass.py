from enum import Enum

class Player:
    def __init__(self, id) -> None:
        self.id = id
        self.maxHP = 100
        self.maxShieldHP = 30
        self.maxShieldCount = 3
        self.maxAmmo = 6
        self.maxGrenades = 2
        self.ammoDmg = 10
        self.grenadesDmg = 30
        self.skillDmg = 10

        self.hp = self.maxHP
        self.shieldHP = 0
        self.shieldCount = self.maxShieldCount
        self.ammo = self.maxAmmo
        self.grenades = self.maxGrenades
        self.enemyDetected = 0
        self.gestureID = 0
        self.kill = 0
        self.death = 0

    def updateState(self, action, visibility):
        self.gestureID = action
        self.enemyDetected = visibility

    def reduceHP(self, dmg):
        if self.shieldHP > 0:
            remainingShieldHP = self.shieldHP - dmg
            if remainingShieldHP > 0:
                self.shieldHP = remainingShieldHP
            else: 
                self.shieldHP = 0
                self.hp= self.hp - abs(remainingShieldHP)
        else:
            self.hp = self.hp - dmg

    def shieldActivate(self):
        if (self.shieldHP > 0 or self.shieldCount <= 0):
            pass
        else:
            self.shieldHP = self.maxShieldHP
            self.shieldCount -= 1

    def shoot(self, enemy):
        if (self.ammo <= 0):
            pass
        else:
            self.ammo -= 1
            if (self.enemyDetected == 1):
                enemy.reduceHP(self.ammoDmg)
                if enemy.hp <= 0:
                    self.kill += 1
                    self.respawn()

    def grenadeThrow(self, enemy):
        if (self.grenades <= 0):
            pass
        else:
            self.grenades -= 1
            if (self.enemyDetected == 1):
                enemy.reduceHP(self.grenadesDmg)
                if enemy.hp <= 0:
                    self.kill += 1
                    self.respawn()
                    
    def skillActivate(self, enemy):
        if (self.enemyDetected == 1):
            enemy.reduceHP(self.skillDmg)
            if enemy.hp <= 0:
                    self.kill += 1
                    self.respawn()

    def reload(self):
        if (self.ammo <= 0):
            self.ammo = self.maxAmmo

    def respawn(self):
        if self.hp < 0:
            self.hp = self.maxHP
            self.shieldHP = 0
            self.shieldCount = self.maxShieldCount
            self.ammo = self.maxAmmo
            self.grenades = self.maxGrenades
            self.death += 1
        

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