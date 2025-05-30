#include "WebControl.h"

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  Serial.println("🤖 Arduino Braccio Web Control Starting...");
  setupWebServer();
}

void loop() {
  handleWebControl();
  delay(10); // Small delay to prevent overwhelming the system
}
