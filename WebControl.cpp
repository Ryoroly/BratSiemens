#include "WebControl.h"
#include <WiFiS3.h>
#include <Servo.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;



const char* ssid = "GEORGE";
const char* password = "12345678a";

WiFiServer server(80);



void setupWebServer() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  int status = WL_IDLE_STATUS;
  while (status != WL_CONNECTED) {
    Serial.print(".");
    status = WiFi.begin(ssid, password);
    delay(1000);
  }

  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\n❌ Failed to connect to WiFi.");
    return;
  }

  Serial.println("\n✅ Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.begin();

  // Inițializare Braccio
  Braccio.begin();
  Braccio.ServoMovement(100, baseAngle, 45, 45, 45, 45, 50);
}
int baseAngle = 90;          // pentru M1
const int baseStep = 5;

int gripperAngle = 10;       // pentru M6
const int gripperStep = 5;

void handleWebControl() {
  WiFiClient client = server.available();
  if (client) {
    String request = "";
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        request += c;
        if (c == '\n') {
          if (request.indexOf("GET /up") != -1) {
            Serial.println("⬆️ UP - open gripper");
            gripperAngle -= gripperStep;
            if (gripperAngle < 10) gripperAngle = 10;
            Braccio.ServoMovement(100, baseAngle, 45, 45, 45, 45, gripperAngle);
          }
          else if (request.indexOf("GET /down") != -1) {
            Serial.println("⬇️ DOWN - close gripper");
            gripperAngle += gripperStep;
            if (gripperAngle > 73) gripperAngle = 73;
            Braccio.ServoMovement(100, baseAngle, 45, 45, 45, 45, gripperAngle);
          }
          else if (request.indexOf("GET /left") != -1) {
            Serial.println("⬅️ LEFT - decrease base angle");
            baseAngle -= baseStep;
            if (baseAngle < 0) baseAngle = 0;
            Braccio.ServoMovement(100, baseAngle, 45, 45, 45, 45, gripperAngle);
          }
          else if (request.indexOf("GET /right") != -1) {
            Serial.println("➡️ RIGHT - increase base angle");
            baseAngle += baseStep;
            if (baseAngle > 180) baseAngle = 180;
            Braccio.ServoMovement(100, baseAngle, 45, 45, 45, 45, gripperAngle);
          }

          // răspuns HTTP...
          client.println("HTTP/1.1 200 OK");
          client.println("Content-type:text/html");
          client.println("Connection: close");
          client.println();
          client.println(R"rawliteral(
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <title>UNO R4 WiFi Arrow Control</title>
              <style>
                body { font-family: sans-serif; text-align: center; margin-top: 50px; }
                button { padding: 20px 30px; font-size: 20px; margin: 10px; }
              </style>
            </head>
            <body>
              <h1>UNO R4 WiFi Control</h1>
              <button onclick="sendCommand('up')">↑ Up</button><br>
              <button onclick="sendCommand('left')">← Left</button>
              <button onclick="sendCommand('right')">→ Right</button><br>
              <button onclick="sendCommand('down')">↓ Down</button>

              <script>
                function sendCommand(dir) {
                  fetch('/' + dir);
                }
                document.addEventListener("keydown", function(e) {
                  if (e.key === "ArrowUp") sendCommand('up');
                  if (e.key === "ArrowDown") sendCommand('down');
                  if (e.key === "ArrowLeft") sendCommand('left');
                  if (e.key === "ArrowRight") sendCommand('right');
                });
              </script>
            </body>
            </html>
          )rawliteral");
          break;
        }
      }
    }
    delay(1);
    client.stop();
  }
}

