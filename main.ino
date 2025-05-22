#include "WebControl.h"

void setup() {
  Serial.begin(115200);
  while (!Serial);
  setupWebServer();
}

void loop() {
  handleWebControl();
}
