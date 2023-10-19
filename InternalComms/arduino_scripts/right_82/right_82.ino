#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <IRremote.h>
#include <limits.h>
#include <cppQueue.h>
#define IR_PIN 3
#define BUZZER_PIN 4
#define SAMPLE_WINDOW 60

/* Internal Comms */
#define RHAND_PKT 1
#define H_PKT 5

#define RELOAD 'r'
#define STATE_HANDSHAKE 'h'
#define STATE_HANDSHAKE_ACK 'd'
#define STATE_SEND 's'

#define INTERVAL 20

//Initialise IR and IMU
IRsend irsend;
Adafruit_MPU6050 mpu;

//Define IR inputs
const uint8_t sCommand = 0xC9;//sensor value to be sent
const uint8_t sRepeats = 0;

//Declare game state values
int bullets = 6; // track remaining bullets, initialised to 6 according to requirement

int flex = 0; //initialise flex sensor to 0
int button_prev = 0;//Declare button press to 0
float ax = 0.0;
float ay = 0.0;
float az = 0.0;
float gx = 0.0;
float gy = 0.0;
float gz = 0.0;

int initial_action_pred = 0;//declare initial action prediction, actions will be enumerated

// //struct containing data for initial prediction
typedef struct strRec {
  float ax;
  float ay;
  float az;
  float gx;
  float gy;
  float gz;
  int flex;
} Rec;

Rec rec_zeropad = {0.0,0.0,0.0,0.0,0.0,0.0,0};

cppQueue q(sizeof(Rec), SAMPLE_WINDOW, FIFO, true);//initiate queue used for initial prediction

// Internal comms init

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
  uint8_t button_press; // B
  uint8_t padding; 

	uint16_t crc; // Assign it to 0 H
};

uint8_t seqNum;
char currentState;
bool sentHandshakeAck;

// End internal comms init

void setup() {

  Serial.begin(115200);

  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);//initialise MPU6050
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  IrSender.begin(IR_PIN);//Initialise IR sensor pin
  pinMode(BUZZER_PIN, OUTPUT);

  button_prev = digitalRead(2); // Initialise button_prev

  // Internal comms flag reset
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

  /* Get new sensor events with the readings */
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);   

  // Uncomment for actual collection:

    float ax = a.acceleration.x;
    float ay = a.acceleration.y;
    float az = a.acceleration.z;
    float gx = g.gyro.x;
    float gy = g.gyro.y;
    float gz = g.gyro.z;
    flex = analogRead(A0);

/*WEIDA IMPLEMENTATION*/

  if (Serial.available()) {
    switch (Serial.peek()){
      case RELOAD:
        Serial.read();
        bullets = 6; // Reload
        break;
      case STATE_HANDSHAKE:
        currentState = Serial.read();  // Clears the serial, set handshake
        break;
      default: // Should have an ack implementation here
        Serial.read(); // Clear serial to remove unwanted data
    }
  }

  // Send packets and handshake protocol
  if (currentState != 'x') {
    switch(currentState) {
      case STATE_SEND:
        sendRightHandPacket(ax,ay,az,gx,gy,gz);
        seqNum += 1;
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

  gun_handler();
}

// Hardware Functions

/*check button read, handle firing*/
void gun_handler() 
{
  int button_read = digitalRead(2);
  if(!button_read && button_prev != button_read) {
      IrSender.sendNEC(0x00, sCommand, sRepeats);// shoot if button pressed (does not shoot more than once if held)
      digitalWrite(BUZZER_PIN, HIGH);
      delay(10);
      digitalWrite(BUZZER_PIN, LOW);
      bullets -= 1;
  }
  button_prev = button_read;
}

/* Get new sensor events with the readings */
void IMU_handler()
{
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  ax = a.acceleration.x;
  ay = a.acceleration.y;
  az = a.acceleration.z;
  gx = g.gyro.x;
  gy = g.gyro.y;
  gz = g.gyro.z;  
}

// end hardware functions

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

    // Normalizing datasets

    float gyroDeg = getGyroDegree();
    float accelG = getAccel();

    pkt.ax = static_cast<int16_t>(ax / accelG * SHRT_MAX);
    pkt.ay = static_cast<int16_t>(ay / accelG * SHRT_MAX);
    pkt.az = static_cast<int16_t>(az / accelG * SHRT_MAX);
    pkt.gx = static_cast<int16_t>(gx / gyroDeg * SHRT_MAX);
    pkt.gy = static_cast<int16_t>(gy / gyroDeg * SHRT_MAX);
    pkt.gz = static_cast<int16_t>(gz / gyroDeg * SHRT_MAX);

    pkt.button_press = button_prev; // For actual data
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
    sizeof(pkt->button_press) +
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

float getGyroDegree() {
    switch (mpu.getGyroRange()) {
    case MPU6050_RANGE_250_DEG:
      return 250.0f;
    case MPU6050_RANGE_500_DEG:
      return 500.0f;
    case MPU6050_RANGE_1000_DEG:
      return 1000.0f;
    case MPU6050_RANGE_2000_DEG:
      return 2000.0f;
  }
}

float getAccel() {
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    return 2.0f;
  case MPU6050_RANGE_4_G:
    return 4.0f;
  case MPU6050_RANGE_8_G:
    return 8.0f;
  case MPU6050_RANGE_16_G:
    return 16.0f;
  }
}

// end internal comms
