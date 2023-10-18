#define VEST_PKT 2
#define RHAND_PKT 1
// #define LHAND_PKT 2
#define GAMESTATE_PKT 3
#define ACK_PKT 4
#define H_PKT 5

#define INTERVAL 100 // Make sure this syncs up with the timeout/interval on Python
#define STATE_HANDSHAKE 'h'
#define STATE_HANDSHAKE_ACK 'd'
#define STATE_SEND 's'
#define STATE_ACK 'a'

#define KEEP_ALIVE 'x'
#define GAMESTATE 'g'
#define SHIELD 'k'
#define HEALTH 'l'

// Hardware's Implementation:

#include <IRremote.h>

//Define pins
#define RECV_PIN 4
#define BUZZER_PIN 5

//Define event values
#define BUL_DMG_CODE 0xC9//0x36
#define BASE_DMG 10
#define GREN_DMG 30

//Declare game event values
bool hit = false;
bool hit_10 = false;
bool skill_hit = false;
bool grenade_hit = false;
bool shield = false;

bool shield_active = false;
bool dead = false;

//Declare game state values
int health = 100;
int shields = 3;
int shield_health = 0;

unsigned long hit_time = 0;
unsigned long hit_time_10 = 0;
unsigned long grenade_hit_time = 0;

// hardware code end

//Gyro and accelerometer will have signed values
struct ackPacket {
  uint8_t id;
  uint8_t seq;
  uint64_t padding_1;
  uint64_t padding_2;
  //  uint32_t crc;
  uint16_t crc;
};

struct hPacket {
	uint8_t id;
	uint64_t padding_1;
	uint64_t padding_2;
	uint16_t padding_3;
	uint8_t padding_4;
};

struct vestDataPacket {
	uint8_t id; //B
	uint8_t seq_no; //B
	uint8_t ir_rcv; //B
  uint16_t health; // H
  uint16_t shield; // Assign it to 0 // H
	uint64_t padding_1; // Assign it to 0 // I
  uint8_t padding_2;
	uint32_t crc; // 
};

uint8_t seqNum;
unsigned long ack_timer;
char currentState;
bool sentHandshakeAck;
bool ackReceived;
bool isTimeout;
char msg;

uint16_t currentHealth;
uint16_t currentShield;

vestDataPacket prevPacket;

unsigned long send_timer;

String numericPart = "";
char gamestateType = 'x';

void setup() {
	// For actual configurations, set up pins here
  Serial.begin(115200); 
  send_timer = millis();
  Serial.begin(115200);
  IrReceiver.begin(RECV_PIN);
  pinMode(BUZZER_PIN, OUTPUT);
	resetFlags();
}

uint16_t convertGamestateInt(){
  String number = "";
  while (!Serial.available()) {
    if (Serial.peek() == STATE_HANDSHAKE) {
      Serial.read();
      resetFlags();
      setStateToHandshake();
      return 0;
    }
  };
  char num = Serial.read();
  return (num - '0') * 10;

}

void updateGamestate(char gamestateType) {

  switch (gamestateType) {
    case HEALTH:
      uint16_t prevHealth = currentHealth;
      currentHealth = convertGamestateInt();
      if (prevHealth - currentHealth == 10) {
        hit_time_10 = micros();
        hit_10 = true;
      } else if (prevHealth - currentHealth == 30) {
        grenade_hit_time = micros();
        grenade_hit = true;
      }
      break;
    case SHIELD:
      uint16_t prevShield = currentShield;
      currentShield = convertGamestateInt();
      if (prevShield - currentShield == 10) {
        hit_time_10 = micros();
        hit_10 = true;
      } else if (prevShield - currentShield == 30) {
        grenade_hit_time = micros();
        grenade_hit = true;
      }
      break;
  }
}

void loop() {

    // Joonsiong's code
  if (dead == false) {
    if (hit) {
      if (shield == 0) 
        health -= 10;
      else 
        shield -= 10;
    }
  }

  if (Serial.available()) {

    // Do not Serial.read() here as it could be an acknowledgement

    switch (Serial.peek()){
      case GAMESTATE:
        Serial.read(); // Read g
        while (!Serial.available()) {
          if (Serial.peek() == STATE_HANDSHAKE) {
            Serial.read();
            resetFlags();
            setStateToHandshake();
            break;
          }
        };
        gamestateType = Serial.read(); // Read and update gamestate type
        updateGamestate(gamestateType); // Read and update gamestate type
        break;
      case STATE_HANDSHAKE:
        currentState = Serial.read();  // Clears the serial, set handshake
        break;
      default:
        Serial.read();
        break;
    }
  }

  if (currentState != 'x') {
    switch(currentState) {
      case STATE_SEND:
        sendDummyVestDataPacket();
        // setStateToAck();
        break;
      case STATE_HANDSHAKE:
        resetFlags();
        sendHandshakeAck();
        waitForHandshakeAck();
        setStateToSend();
        break;
      // case STATE_ACK:
      //   waitForAck();
      //   if (ackReceived || isTimeout) {
      //     setStateToSend();
      //     isTimeout = false;
      //   }
      //   break;
      default:
        resetFlags();
        break;
    }
  }

  dmg_10_beeper();
  grenade_dmg_beeper();
  // Handles IR Receiver
  receiver_handler();
}

void resetFlags() {
  currentState = 'x';
  sentHandshakeAck = false;
  ackReceived = false;
  seqNum = 0;
  prevPacket.id = NULL;
  prevPacket.seq_no = NULL;
  prevPacket.ir_rcv = NULL;
  isTimeout = false;
  currentHealth = 100;
  currentShield = 0;
  delay(50);
}

void setStateToHandshake() {
  currentState = STATE_HANDSHAKE;
  sentHandshakeAck = false;
}

void setStateToSend() {
  if (sentHandshakeAck)
    currentState = STATE_SEND;
}

void setStateToAck() {
  if (sentHandshakeAck)
    currentState = STATE_ACK;
}

void waitForAck() {
  unsigned long current_time = millis();
  unsigned long timeout_interval = 500;

  while (!Serial.available()) {
    if (millis() - current_time >= timeout_interval) {
      isTimeout = true;
      return; // Break out of the bloop and resend prev packet
    }
  };

  if (Serial.peek() == STATE_HANDSHAKE) {
    Serial.read();
    resetFlags();
    return;
  }

  char ackNum = Serial.read();

  if (ackNum - '0' == seqNum) {
    ackReceived = true;
    seqNum = (seqNum + 1) % 8;
  }
}

void sendDummyVestDataPacket(){
  // if ((isTimeout) && (sentHandshakeAck && prevPacket.id != NULL)) {
  //   Serial.write((uint8_t *)&prevPacket, sizeof(prevPacket));
  //   delay(50);
  // } else {
    vestDataPacket pkt;
    pkt.id = VEST_PKT;
    pkt.seq_no = seqNum++;
    pkt.ir_rcv = hit;
    pkt.health = currentHealth;
    pkt.shield = currentShield;
    pkt.padding_1 = 0;
    pkt.padding_2 = 0;
    pkt.crc = calculateGvCrc32(&pkt);
    prevPacket = pkt;
    ackReceived = false;
    Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
    delay(50);
  // }
}

int randomint(int min, int max) {
  return rand() % (max - min + 1) + min;
}


//================ Handshake =================

void sendHandshakeAck() {
  if (sentHandshakeAck) return;
  hPacket h;
  h.id = H_PKT;
  h.padding_1 = 0;
  h.padding_2 = 0;
  h.padding_3 = 0;
  h.padding_4 = 0;
  Serial.write((uint8_t *)&h, sizeof(h));
  sentHandshakeAck = true;
}

void waitForHandshakeAck(){
  char ack_msg;

  while (!Serial.available());

  ack_msg = Serial.read();

  if (ack_msg != 'd') {
    resetFlags();
    return;
  }
}

//=======================================================

//========================Calculate CRC======================


uint16_t calculateAckCrc16(ackPacket *pkt) {
  return custom_crc16(&pkt->id, sizeof(pkt->id) + sizeof(pkt->seq));
}

uint32_t calculateGvCrc32(vestDataPacket *pkt) {
  return custom_crc32(&pkt->id, 
    sizeof(pkt->id) +
    sizeof(pkt->seq_no) +
    sizeof(pkt->ir_rcv) +
    sizeof(pkt->health) +
    sizeof(pkt->shield)
  );
}

//===========================================================

//====================Custom CRC Library======================

uint16_t custom_crc16(const uint8_t* data, size_t len) {
  uint16_t crc = 0x0000;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int j = 0; j < 8; j++) {
      crc = (crc & 1) ? ((crc >> 1) ^ 0x8001) : (crc >> 1);
    }
  }
  return crc;
}

uint32_t custom_crc32(const uint8_t *data, size_t len) {
  uint32_t crc = 0x00000000;
  
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int j = 0; j < 8; j++) {
      crc = (crc & 1) ? ((crc >> 1) ^ 0x04C11DB7) : (crc >> 1);
    }
  }
  
  return crc;
}

// Hardware Implementation

void receiver_handler()
{
  if (IrReceiver.decode()) {
    IrReceiver.resume();
    hit = true;
    hit_time = millis();
    // hit_time_10 = micros(); // no hit time, shoot + skill hit same dmg, updated from state
  } else {
    if (millis() - hit_time > 50) hit = false;
  }
}

//Handles gun and skill (exlcuding grenade) damage event 
void dmg_10_beeper()
{
  unsigned long frequency = 5000;
  if (currentShield > 0) frequency = 300;
  unsigned long wait = 150000; // microseconds
  unsigned long timeDiff = micros() - hit_time_10;

  // Gun and skill dmg
  if (hit_10 && timeDiff < wait) {
  // if (hit && timeDiff < wait) {
    if (timeDiff/(1000000/frequency/2)%2 == 0) {
      digitalWrite(BUZZER_PIN, HIGH);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  }

  if (hit_10 && timeDiff > wait) {
  // if (hit && timeDiff > wait) {
    digitalWrite(BUZZER_PIN, LOW);
    hit_10 = false;
  }
}

// Grenade dmg - 30 dmg
void grenade_dmg_beeper() {

  unsigned long frequency = 1000;
  if (currentShield > 0) frequency = 300;
  unsigned long wait = 300000; // microseconds
  unsigned long timeDiff = micros() - hit_time_10;

  if (grenade_hit && timeDiff < wait) {
    if (timeDiff/(1000000/frequency/2)%2 == 0) {
      digitalWrite(BUZZER_PIN, HIGH);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  }

  if (grenade_hit && timeDiff > wait) {
    digitalWrite(BUZZER_PIN, LOW);
    grenade_hit = false;
  }
}

//Handles skill damage event at current cycle
int skill_dmg_handler()
{
  if(skill_hit) {
    // Serial.print("Skill hit   ");
    // dmg_beeper_handler(BASE_DMG);
    skill_hit = false;
    return BASE_DMG;
  }
  return 0;
}

//Handles grenade damage event at current cycle
int grenade_dmg_handler()
{
  if (grenade_hit) {
    // Serial.print("Grenade hit   ");
    // dmg_beeper_handler(GREN_DMG);
    grenade_hit = false;
    return GREN_DMG;
  }
  return 0;
}

//Calculates total damage at current cycle
// int dmg_handler()
// {
//   return gun_dmg_beeper() + skill_dmg_handler() + grenade_dmg_handler();
// }

//Handles shield deployment
void shield_handler()
{
  if(shield) {
    if (shields > 0) {
      shield_active = true;
      // Serial.println("shield active");
      shield_health = 30;
      shields -= 1;
      // Serial.print("shields remaining: ");
      // Serial.println(shields);
      // shield = false;
    }
  }
}

//calculate remaining health at current cycle
// void health_calc() {
//   int total_dmg = dmg_handler();
//   shield_handler();
//   if (total_dmg > 0) {
//     if (shield_active) {
//       if (shield_health > 0) {
//         shield_health -= total_dmg;
//       }
//       if (shield_health <= 0) {
//         health += shield_health;
//         shield_active = false;
//         shield_health = 0;
//       }
//     } else {
//       health -= total_dmg;
//     }
//     // Serial.println("");
//     // Serial.print("health remaining:");
//     // Serial.println(health);
//     // Serial.print("current shield health: ");
//     // Serial.println(shield_health);
//   }
// }

//Check if player is dead
void death_handler()
{
  if (health <= 0) {
    dead = true;
    Serial.println("dead");
    digitalWrite(BUZZER_PIN, HIGH);
    delay(2000);
    digitalWrite(BUZZER_PIN, LOW);
  }
}
