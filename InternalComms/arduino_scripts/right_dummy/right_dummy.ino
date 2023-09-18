#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <IRremote.h>
// #include <cppQueue.h>
#define IR_PIN 3
#define SAMPLE_WINDOW 60

/* Internal Comms */
#define RHAND_PKT 1
#define H_PKT 5

#define RELOAD 'r'
#define STATE_HANDSHAKE 'h'
#define STATE_HANDSHAKE_ACK 'd'
#define STATE_SEND 's'

#define INTERVAL 50 

IRsend irsend;
Adafruit_MPU6050 mpu;

const uint8_t sCommand = 0x36;
const uint8_t sRepeats = 0;

int bullets = 30; // track remaining bullets, initialised to 30

int16_t flex = 0; //initialise flex sensor to 0
int button_prev = 0;//Declare button press to 0
int initial_action_pred = 0;//declare initial action prediction, actions will be enumerated

// //struct containing data for initial prediction
// typedef struct strRec {
//   float ax;
//   float ay;
//   float az;
//   float gx;
//   float gy;
//   float gz;
//   int flex;
// } Rec;

// Rec rec_zeropad = {0.0,0.0,0.0,0.0,0.0,0.0,0};

// cppQueue q(sizeof(Rec), SAMPLE_WINDOW, FIFO, true);//initiate queue used for initial prediction

// Internal comms

struct hPacket {
	uint8_t id;
	uint64_t padding_1;
	uint64_t padding_2;
	uint16_t padding_3;
	uint8_t padding_4;
};

struct rightHandDataPacket {
	uint8_t id; // B
	uint8_t seq; // B
	// Accelerometer
	int16_t ax; // h
	int16_t ay; // h
	int16_t az; // h
  // Gyro
	int16_t gx; // h
	int16_t gy; // h
	int16_t gz; // h
  uint16_t flex; // H
  uint8_t bullets; // B
  uint8_t padding; 

	uint16_t crc; // Assign it to 0 H
};

uint8_t seqNum;
char currentState;
bool sentHandshakeAck;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  // Uncomment this for data collecting 

  // if (!mpu.begin()) {
  //   Serial.println("Failed to find MPU6050 chip");
  //   while (1) {
  //     delay(10);
  //   }
  // }

  // mpu.setAccelerometerRange(MPU6050_RANGE_16_G);//initialise MPU6050
  // mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  // mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  
  // IrSender.begin(IR_PIN);//Initialise IR sensor pin

  // button_prev = digitalRead(2);//Initialise button_prev
  

  // for (int i = 0; i < SAMPLE_WINDOW; i++) {
  //   q.push(&rec_zeropad);
  // }

  resetFlags();

  delay(100);
}

void loop() {
  //check button read, handle firing
  int button_read = digitalRead(2);
  if(!button_read && button_prev != button_read) {
    IrSender.sendNEC(0x00, sCommand, sRepeats);// shoot if button pressed (does not shoot more than once if held)
    if (bullets > 0) {
      bullets -= 1;
    }
  }
  button_prev = button_read;

  // Uncomment for actual collection:


  /* Get new sensor events with the readings */
  // sensors_event_t a, g, temp;
  // mpu.getEvent(&a, &g, &temp);   

  //   float ax = a.acceleration.x;
  //   float ay = a.acceleration.y;
  //   float az = a.acceleration.z;
  //   float gx = g.gyro.x;
  //   float gy = g.gyro.y;
  //   float gz = g.gyro.z;
  //   flex = analogRead(A0);

  // Dummy data   
  float ax = 0.71;
  float ay = -0.98;
  float az = 10.80;
  float gx = -0.08;
  float gy = 0.01;
  float gz = 0.01;
  flex = 594;

  // Rec sample = {ax, ay, az, gx, gy, gz, flex};
  // q.push(&sample);

  // for (int j; j < SAMPLE_WINDOW; j++) {
  //   Serial.println(q.peekIdx(j));
  // }
  // Serial.println("");

/*WEIDA IMPLEMENTATION*/

  if (Serial.available()) {
    switch (Serial.peek()){
      case RELOAD:
        Serial.read();
        bullets = 30;
        break;
      case STATE_HANDSHAKE:
        currentState = Serial.read();  // Clears the serial, set handshake
        break;
      default:
        Serial.read(); // Clear serial to remove unwanted data
    }
  }

  // Send packets and handshake protocol
  if (currentState != 'x') {
    switch(currentState) {
      case STATE_SEND:
        sendRightHandPacket(ax,ay,az,gx,gy,gz);
        seqNum  = seqNum >= 255 ? 0 : seqNum += 1;
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

//poll for reload action ##WEIDA
/*WEIDA IMPLEMENTATION*/


  /* Print out the values */
  // Serial.print(ax);
  // Serial.print(",");
  // Serial.print(ay);
  // Serial.print(",");
  // Serial.print(az);
  // Serial.print(", ");
  // Serial.print(gx);
  // Serial.print(",");
  // Serial.print(gy);
  // Serial.print(",");
  // Serial.print(gz);
  // Serial.print(",");
  // Serial.print(flex);
  // Serial.print(",");
  // Serial.print(bullets);  
  // Serial.println("");  
}

// Internal Comms functions

void resetFlags() {
    seqNum = 0;
    sentHandshakeAck = false;
    currentState = 'x';
}

void setStateToSend() {
  if (sentHandshakeAck)
    currentState = STATE_SEND;
}

void sendRightHandPacket(float ax, float ay, float az, float gx, float gy, float gz) {
    rightHandDataPacket pkt;
    pkt.id = 1;
    pkt.seq = seqNum;
    pkt.ax = static_cast<int16_t>(ax * 100);
    pkt.ay = static_cast<int16_t>(ay * 100);
    pkt.az = static_cast<int16_t>(az * 100);
    pkt.gx = static_cast<int16_t>(gx * 100);
    pkt.gy = static_cast<int16_t>(gy * 100);
    pkt.gz = static_cast<int16_t>(gz * 100);
    pkt.bullets = bullets; // For actual data
    // For data collection, bullets = button for now.
    // pkt.bullets = !button_prev; // 0 when pressed, 1 when not pressed
    pkt.flex = flex;
    pkt.padding = 0;
    pkt.crc = calculateRightHandCrc16(&pkt);
    // Send packet
    Serial.write((uint8_t *)&pkt, sizeof(pkt)); 
    delay(INTERVAL);
}

// Handshake:
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
  delay(INTERVAL);
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

uint16_t calculateRightHandCrc16(rightHandDataPacket *pkt) {
  return custom_crc16(&pkt->id, 
    sizeof(pkt->id) +
    sizeof(pkt->seq) +
    sizeof(pkt->gx) +
    sizeof(pkt->gy) +
    sizeof(pkt->gz) +
    sizeof(pkt->ax) +
    sizeof(pkt->ay) +
    sizeof(pkt->az) +
    sizeof(pkt->bullets) +
    sizeof(pkt->flex)
  );
}

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

// end internal comms
