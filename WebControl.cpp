#include <WiFiS3.h>
#include "WebControl.h"

const char* ssid = "GEORGE";
const char* password = "12345678a"; 



// IPAddress ip(192, 168, 1, 50);
// IPAddress gateway(192, 168, 1, 1);
// IPAddress subnet(255, 255, 255, 0);




WiFiServer server(80);
String request;

void handleWebControl() {
  WiFiClient client = server.available();
  if (client) {
    //Serial.println("📡 Client connected!");
    String request = "";
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        request += c;
        if (c == '\n') {
          // Cerere HTTP terminată (linie goală după headere)
          if (request.indexOf("GET /up") != -1) Serial.println("⬆️ UP");
          else if (request.indexOf("GET /down") != -1) Serial.println("⬇️ DOWN");
          else if (request.indexOf("GET /left") != -1) Serial.println("⬅️ LEFT");
          else if (request.indexOf("GET /right") != -1) Serial.println("➡️ RIGHT");

          // Răspuns HTTP
          client.println("HTTP/1.1 200 OK");
          client.println("Content-type:text/html");
          client.println("Connection: close");
          client.println(); // linie goală obligatorie

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

          break; // ieși după trimiterea paginii
        }
      }
    }
    delay(1);
    client.stop();
    
  }
}



void setupWebServer() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  //  WiFi.begin(ssid, password);
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
  Serial.print("WiFi status: ");
Serial.println(WiFi.status());

}
// void setupWebServer() {
//   WiFi.begin(ssid, password);
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }

//   Serial.println("\nConnected to WiFi");
//   Serial.println(WiFi.localIP());
//   server.begin();
// }
