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
        self.action = "none"
        self.death: int = 0
    
    def print(self):
        print(f'hp: {self.hp} bullets: {self.bullets} ')

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
            return True
        return False

    def grenadeThrow(self):
        if (self.grenades > 0):
            self.grenades -= 1
            return True
        return False

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
    
    def get_player(self):
        return {
                    'hp': self.hp,
                    'bullets': self.bullets,
                    'grenades': self.grenades,
                    'shield_hp': self.shieldHP,
                    'deaths': self.death,
                    'shields': self.shieldCount
                }
    def get_id(self):
        return self.id

    def get_action(self):
        return self.action

    def set_action(self, act):
        self.action = act
    
    def set_bullets(self, bullets):
        self.bullets = bullets

    def set_state(self, state):
        self.hp = state["hp"]
        self.bullets = state["bullets"]
        self.grenades = state["grenades"]
        self.shieldHP = state["shield_hp"]
        self.death = state["deaths"]
        self.shieldCount = state["shields"]
        

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
