

void setup() {
  Serial.begin(115200);  //initial the Serial
}

void loop() {

  if(Serial.available()) {
    Serial.print(Serial.readString()); 
  };
}
