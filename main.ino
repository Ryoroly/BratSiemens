#include "WebControl.h"
 
void setup() {
  Serial.begin(115200);
  while (!Serial);
  setupWebServer();  // WiFi & server startup
}

void loop() {
  handleWebControl();  // Non-blocking client handler
}
