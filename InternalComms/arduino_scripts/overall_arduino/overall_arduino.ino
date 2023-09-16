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

uint8_t seq_no;
unsigned long ack_timer;
char currentState;
bool sentHandshakeAck;
bool ackReceived;
char msg;

void setup() {
	// For actual configurations, set up pins here
	// MPU6050 library if im not wrong
	// Serial.begin(115200); 
	resetFlags();
}

void loop() {

	if (Serial.available()) {
	  if (Serial.peek() == STATE_GAMESTATE) 
	    currentState = Serial.peek(); // Takes the first byte as its state
	  if (Serial.peek() == STATE_HANDSHAKE) 
	    currentState = Serial.read(); // Clears the serial
    
	}

  if (currentState != 'x') {
    switch(currentState) {
      case STATE_SEND:
        sendDummyGvDataPacket();
        setStateToAck();
        break;
      case STATE_ACK:
        waitForAck();
        setStateToSend();
        break;
      case STATE_GAMESTATE:
        // setStateToSend();
        Serial.print("state g");
        break;
      case 'h':
        // resetFlags();
        sendHandshakeAck();
        waitForHandshakeAck();
        setStateToSend();
        break;
      default:
        resetFlags();
        break;
    }
    
  }
}

void resetFlags() {
  Serial.begin(115200); 
  currentState = 'x';
  sentHandshakeAck = false;
  ackReceived = false;
  seq_no = 0;
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

void setStateToGamestate(){
  if (sentHandshakeAck)
    currentState = STATE_GAMESTATE;
}

void sendDummyAck() {
  ackPacket pkt;
  pkt.id = 4;
  pkt.seq = 1;
  pkt.padding_1 = 0;
  pkt.padding_2 = 0;
  pkt.crc = calculateAckCrc16(&pkt);
  Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
  delay(INTERVAL);
}

void sendDummyGvDataPacket(){
  vestDataPacket pkt;
  pkt.id = 0;
  pkt.seq_no = seq_no;
  pkt.ir_rcv_1 = 0;
  pkt.ir_rcv_2 = 0;
  pkt.padding_0 = 0;
  pkt.padding_1 = 0;
  pkt.padding_2 = 0;
  pkt.crc = calculateGvCrc32(&pkt);
  Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
  delay(INTERVAL);
}

void waitForAck() {
  while (!Serial.available());

  if (Serial.peek() == STATE_HANDSHAKE) {
    Serial.read();
    resetFlags();
    return;
  }

  uint8_t ack_seq_no = Serial.parseInt();

  if (ack_seq_no == seq_no) {
    // ackReceived = true;
    seq_no++;
  }
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