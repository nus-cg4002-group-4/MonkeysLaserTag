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
	uint8_t ir_rcv_1; //B
	uint8_t ir_rcv_2; //B
  uint16_t health; // H
  uint16_t shield; // Assign it to 0 // H
	uint64_t padding_1; // Assign it to 0 // I
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
	resetFlags();
}

uint16_t convertGamestateInt(){
  String number = "";
  while (Serial.available() && isDigit(Serial.peek())) {
    number += char(Serial.read());
  }
  return number.toInt();
}

void updateGamestate(char gamestate) {

  switch (gamestateType) {
    case HEALTH:
      currentHealth = convertGamestateInt();
      break;
    case SHIELD:
      currentShield = convertGamestateInt();
      break;
  }
}

void loop() {

  if (Serial.available()) {

    // Do not Serial.read() here as it could be an acknowledgement

    switch (Serial.peek()){
      case GAMESTATE:
        Serial.read(); // Read g
        gamestateType = Serial.read(); // Read and update gamestate type
        updateGamestate(gamestateType); // Read and update gamestate type
        break;
      case STATE_HANDSHAKE:
        currentState = Serial.read();  // Clears the serial, set handshake
        break;
      default:
        break;
    }
  }

  if (currentState != 'x') {
    switch(currentState) {
      case STATE_SEND:
        sendDummyVestDataPacket();
        setStateToAck();
        break;
      case STATE_HANDSHAKE:
        resetFlags();
        sendHandshakeAck();
        waitForHandshakeAck();
        setStateToSend();
        break;
      case STATE_ACK:
        waitForAck();
        if (ackReceived || isTimeout) 
          setStateToSend();
        break;
      default:
        resetFlags();
        break;
    }
  }
}

void resetFlags() {
  currentState = 'x';
  sentHandshakeAck = false;
  ackReceived = false;
  seqNum = 0;
  prevPacket.id = NULL;
  prevPacket.seq_no = NULL;
  prevPacket.ir_rcv_1 = NULL;
  prevPacket.ir_rcv_2 = NULL;
  isTimeout = false;
  currentHealth = 100;
  currentShield = 30;
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
  if (isTimeout || (!ackReceived && (sentHandshakeAck && prevPacket.id != NULL))) {
    Serial.write((uint8_t *)&prevPacket, sizeof(prevPacket));
    delay(50);
  } else {
    vestDataPacket pkt;
    pkt.id = VEST_PKT;
    pkt.seq_no = seqNum;
    pkt.ir_rcv_1 = randomint(0, 1);
    pkt.ir_rcv_2 = randomint(0, 1);
    pkt.health = currentHealth;
    pkt.shield = currentShield;
    pkt.padding_1 = 0;
    pkt.crc = calculateGvCrc32(&pkt);
    prevPacket = pkt;
    ackReceived = false;
    Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
    delay(50);
  }
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
    sizeof(pkt->ir_rcv_1) +
    sizeof(pkt->ir_rcv_2) + 
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