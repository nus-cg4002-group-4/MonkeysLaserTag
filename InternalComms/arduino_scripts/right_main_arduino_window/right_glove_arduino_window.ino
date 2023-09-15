#define GV_PKT 0
#define RHAND_PKT 1
#define LHAND_PKT 2
#define GAMESTATE_PKT 3
#define ACK_PKT 4
#define H_PKT 5

#define INTERVAL 10 // Make sure this syncs up with the timeout/interval on Python
#define STATE_HANDSHAKE 'h'
#define STATE_HANDSHAKE_ACK 'd'
#define STATE_ACK 'a'
#define STATE_GAMESTATE 'g'
#define STATE_SEND 's'

#define WINDOW_SIZE 4
#define MAX_SEQ_NUM 7
#define TIMEOUT 1000

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
	uint8_t id; // B
	uint8_t seq_no; // B
  uint8_t ir_trm; // B
  uint8_t button; // B
	uint16_t flex_sensor; // H
	// Gyro
	int16_t yaw; // H
	int16_t pitch; // H
	int16_t roll; // H
	// Accelerometer
	int16_t x; // H
	int16_t y; // H
	int16_t z; // H
	uint16_t crc; // Assign it to 0
};

uint8_t seq_no;
char currentState;
bool sentHandshakeAck;

uint8_t baseSeqNum = 0;
uint8_t nextSeqNum = 0;
rightHandDataPacket packets[MAX_SEQ_NUM + 1];
bool ackReceived[MAX_SEQ_NUM + 1] = {false}; 
unsigned long ackTimers[MAX_SEQ_NUM + 1] = {0};

void setup() {
	// For actual configurations, set up pins here
	// MPU6050 library if im not wrong
	Serial.begin(115200); 
	resetFlags();
}

void loop() {

  if (Serial.available()) {
    if (Serial.peek() == STATE_GAMESTATE) {
        currentState = Serial.peek(); // Takes the first byte as its state
      } else if (Serial.peek() == STATE_HANDSHAKE) {
        currentState = Serial.read();  // Clears the serial
      } else {
        // Wait for acknowledgements
        while (Serial.available()) {
          int ackNum = Serial.read();
          // int difference = baseSeqNum - ackNum < 0 ? baseSeqNum + MAX_SEQ_NUM - ackNum : (baseSeqNum - ackNum) % (MAX_SEQ_NUM + 1);
          int i = (baseSeqNum - ackNum) % MAX_SEQ_NUM + 1;
          while (i >= 0 && i <= WINDOW_SIZE) { 
            ackReceived[baseSeqNum] = true;
            baseSeqNum = (baseSeqNum + 1) % (MAX_SEQ_NUM + 1);
            i -= 1;
          }
        }
      }
  }

  // Send packets and handshake protocol
  if (currentState != 'x') {
    switch(currentState) {
      case STATE_SEND:
        if (nextSeqNum < (baseSeqNum + WINDOW_SIZE) % (MAX_SEQ_NUM + 1)) {
            sendRightHandPacket(nextSeqNum);
            nextSeqNum = (nextSeqNum + 1) % (MAX_SEQ_NUM + 1);
        }
        break;
      case STATE_HANDSHAKE:
        resetFlags();
        sendHandshakeAck();
        waitForHandshakeAck();
        setStateToSend();
        break;
      default:
        resetFlags();
        break;
    }
  }

  // Check for base timeout
  // if (isAckTimedOut(baseSeqNum)) {
  //     // Send packet again and reset timer
  //     Serial.write((uint8_t *) &packets[baseSeqNum], sizeof(rightHandDataPacket));
  //     startTimer(baseSeqNum);
  // }

}

void resetFlags() {
    currentState = 'x';
    sentHandshakeAck = false;
    seq_no = 0;
    baseSeqNum = 0;
    nextSeqNum = 0;
    for (int i = 0; i < MAX_SEQ_NUM + 1; i++) {
        packets[i].id = 1;
        packets[i].seq_no = 0;
        packets[i].ir_trm = 0;
        packets[i].button = 0;
        packets[i].flex_sensor = 0;
        packets[i].yaw = 0;
        packets[i].pitch = 0;
        packets[i].roll = 0;
        packets[i].x = 0;
        packets[i].y = 0;
        packets[i].z = 0;
        packets[i].crc = 0;

        ackReceived[i] = false; 
        ackTimers[i] = 0;
    }

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

void setStateToGamestate(){
  if (sentHandshakeAck)
    currentState = STATE_GAMESTATE;
}

void startTimer(uint8_t seqNum) {
    ackTimers[seqNum] = millis();
}

// Returns true if base sequence number is timed out
bool isAckTimedOut(uint8_t seqNum) {
    return ackTimers[seqNum] + TIMEOUT >= millis();
}

void sendRightHandPacket(uint8_t seqNum) {
    rightHandDataPacket pkt;
    pkt.id = 1;
    pkt.seq_no = seqNum;
    pkt.ir_trm = 1;
    pkt.button = 0;
    pkt.flex_sensor = 0;
    pkt.yaw = 2;
    pkt.pitch = 2;
    pkt.roll = 2;
    pkt.x = 1;
    pkt.y = 1;
    pkt.z = 1;
    pkt.crc = calculateRightHandCrc16(&pkt);
    // Send packet
    Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
    // Store packet in buffer:
    packets[seqNum] = pkt;
    // Initialize ackReceived[seqNum] back to false:
    ackReceived[seqNum] = false;
    delay(20);
}

// void waitForAck() {
//   while (!Serial.available());

//   if (Serial.peek() == STATE_HANDSHAKE) {
//     Serial.read();
//     resetFlags();
//     return;
//   }

//   uint8_t ack_seq_no = Serial.parseInt();

//   if (ack_seq_no == seq_no) {
//     // ackReceived = true; 
//     //Reset before 64 so that seq number is not recognized by the ASCII states
//     seq_no = (seq_no >= 63) ? 0 : seq_no++;
//   }
// }

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
  return custom_crc16(&pkt->id,
   sizeof(pkt->id) + 
   sizeof(pkt->seq));
}

uint16_t calculateRightHandCrc16(rightHandDataPacket *pkt) {
  return custom_crc16(&pkt->id, 
    sizeof(pkt->id) +
    sizeof(pkt->seq_no) +
    sizeof(pkt->ir_trm) + 
    sizeof(pkt->button) +
    sizeof(pkt->flex_sensor) +
    sizeof(pkt->yaw) +
    sizeof(pkt->pitch) +
    sizeof(pkt->roll) +
    sizeof(pkt->x) +
    sizeof(pkt->y) +
    sizeof(pkt->z)
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
