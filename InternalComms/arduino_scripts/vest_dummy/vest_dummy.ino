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

struct rightHandDataPacket {
	uint8_t id;
	uint8_t seq_no;
	uint16_t flex_sensor;
	// Gyro
	int16_t yaw;
	int16_t pitch;
	int16_t roll;
	// Accelerometer
	int16_t x;
	int16_t y;
	int16_t z;
	uint32_t padding; // Assign it to 0
};

struct leftHandDataPacket {
	uint8_t id;
	uint8_t seq_no;
	// Gyro
	int16_t yaw;
	int16_t pitch;
	int16_t roll;
	// Accelerometer
	int16_t x;
	int16_t y;
	int16_t z;
	uint32_t padding_1; // Assign it to 0
	uint16_t padding_2; // Assign it to 0
};

struct vestDataPacket {
	uint8_t id; //B
	uint8_t seq_no; //B
	uint8_t ir_rcv_1; //B
	uint8_t ir_rcv_2; //B
  uint16_t padding_0; // H
	uint64_t padding_1; // Assign it to 0 // I
	uint16_t padding_2; // Assign it to 0 // H
	uint32_t crc; // 
};

uint8_t seqNum;
unsigned long ack_timer;
char currentState;
bool sentHandshakeAck;
bool ackReceived;
char msg;

vestDataPacket prevPacket;

#define MAX_SEQ_NUM 7

unsigned long send_timer;
rightHandDataPacket packets[MAX_SEQ_NUM + 1];
bool ackReceived[MAX_SEQ_NUM + 1] = {false}; 
unsigned long ackTimers[MAX_SEQ_NUM + 1] = {0};

uint8_t baseSeqNum = 0;
uint8_t nextSeqNum = 0;

void setup() {
	// For actual configurations, set up pins here
  Serial.begin(115200); 
  send_timer = millis();
	resetFlags();
}

void loop() {

  // if (sentHandshakeAck && millis() - send_timer > 1000) {
  //   send_timer = millis();
  //   setStateToHandshake();
  // }

  if (Serial.available()) {
    switch (Serial.peek()){
      case GAMESTATE:
        Serial.read();
        // TODO: Handle gamestate
        break;
      case STATE_HANDSHAKE:
        currentState = Serial.read();  // Clears the serial, set handshake
        break;
      default:
        // int ackNum = Serial.read();
        // // int difference = baseSeqNum - ackNum < 0 ? baseSeqNum + MAX_SEQ_NUM - ackNum : (baseSeqNum - ackNum) % (MAX_SEQ_NUM + 1);
        // int i = (baseSeqNum - ackNum) % MAX_SEQ_NUM + 1;
        // while (i >= 0 && i <= WINDOW_SIZE) { 
        //   ackReceived[baseSeqNum] = true;
        //   baseSeqNum = (baseSeqNum + 1) % (MAX_SEQ_NUM + 1);
        //   i -= 1;
        // }
        break;
      // case KEEP_ALIVE:
      //   Serial.read();
      // default: // Default should be ack messages

      //   Serial.read();
        // uint8_t ackNum = Serial.parseInt();

        // if (ackNum == seqNum) {
        //   ackReceived = true;
        //   seqNum = seqNum >= 7 ? 0 : seqNum + 1;
        // }
        // break;
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
        setStateToSend();
        break;
      case STATE_ACK:
        waitForAck();
        setStateToSend();
        break;
      default:
        resetFlags();
        break;
    }
  }
  if (sentHandshakeAck && !ackReceived) waitForAck();
}


void resetFlags() {
  currentState = 'x';
  sentHandshakeAck = false;
  ackReceived = false;
  seqNum = 0;
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
  while (!Serial.available());

  if (Serial.peek() == STATE_HANDSHAKE) {
    Serial.read();
    resetFlags();
    return;
  }

  uint8_t ack_seq_no = Serial.parseInt();

  if (ack_seq_no == seqNum) {
    ackReceived = true;
    seqNum += 1;
  }
}

void sendDummyVestDataPacket(){
  if (sentHandshakeAck && !ackReceived && seqNum > 0) {
    Serial.write((uint8_t *)&prevPacket, sizeof(prevPacket));
    return;
  }
  vestDataPacket pkt;
  pkt.id = VEST_PKT;
  pkt.seq_no = seqNum;
  pkt.ir_rcv_1 = randomint(0, 1);
  pkt.ir_rcv_2 = randomint(0, 1);
  pkt.padding_0 = 0;
  pkt.padding_1 = 0;
  pkt.padding_2 = 0;
  pkt.crc = calculateGvCrc32(&pkt);
  // pkt.crc = 0;
  ackReceived = false;
  Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
  // delay(100);
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
  unsigned long prevMillis = 0;
  unsigned long interval = 5000;
  bool isTimeout = false;
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
    sizeof(pkt->ir_rcv_2)
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