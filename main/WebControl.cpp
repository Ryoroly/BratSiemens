#include "WebControl.h"
#include <WiFiS3.h>
#include <Servo.h>
#include <Braccio.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;

const char* ssid = "iPhone George";
const char* password = "undoitrei";

WiFiServer server(80);

// Servo positions
int baseAngle = 90;
int shoulderAngle = 45;
int elbowAngle = 45;
int wristRotAngle = 45;
int wristVerAngle = 45;
int gripperAngle = 10;

const int stepSize = 5;
unsigned long lastMoveTime = 0;
const unsigned long moveDelay = 50; // Minimum delay between moves

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
  
  // Initialize Braccio
  Braccio.begin();
  Braccio.ServoMovement(100, baseAngle, shoulderAngle, elbowAngle, wristRotAngle, wristVerAngle, gripperAngle);
}

String getStatusJSON() {
  return "{\"base\":" + String(baseAngle) + 
         ",\"shoulder\":" + String(shoulderAngle) + 
         ",\"elbow\":" + String(elbowAngle) + 
         ",\"wristRot\":" + String(wristRotAngle) + 
         ",\"wristVer\":" + String(wristVerAngle) + 
         ",\"gripper\":" + String(gripperAngle) + "}";
}

void moveServo(String joint, String direction) {
  if (millis() - lastMoveTime < moveDelay) return;
  
  bool moved = false;
  
  if (joint == "base") {
    if (direction == "left" && baseAngle > 0) {
      baseAngle -= stepSize;
      if (baseAngle < 0) baseAngle = 0;
      moved = true;
    } else if (direction == "right" && baseAngle < 180) {
      baseAngle += stepSize;
      if (baseAngle > 180) baseAngle = 180;
      moved = true;
    }
  } else if (joint == "gripper") {
    if (direction == "open" && gripperAngle > 10) {
      gripperAngle -= stepSize;
      if (gripperAngle < 10) gripperAngle = 10;
      moved = true;
    } else if (direction == "close" && gripperAngle < 73) {
      gripperAngle += stepSize;
      if (gripperAngle > 73) gripperAngle = 73;
      moved = true;
    }
  } else if (joint == "shoulder") {
    if (direction == "up" && shoulderAngle > 15) {
      shoulderAngle -= stepSize;
      if (shoulderAngle < 15) shoulderAngle = 15;
      moved = true;
    } else if (direction == "down" && shoulderAngle < 165) {
      shoulderAngle += stepSize;
      if (shoulderAngle > 165) shoulderAngle = 165;
      moved = true;
    }
  } else if (joint == "elbow") {
    if (direction == "up" && elbowAngle > 0) {
      elbowAngle -= stepSize;
      if (elbowAngle < 0) elbowAngle = 0;
      moved = true;
    } else if (direction == "down" && elbowAngle < 180) {
      elbowAngle += stepSize;
      if (elbowAngle > 180) elbowAngle = 180;
      moved = true;
    }
  }
  
  if (moved) {
    Braccio.ServoMovement(20, baseAngle, shoulderAngle, elbowAngle, wristRotAngle, wristVerAngle, gripperAngle);
    lastMoveTime = millis();
    Serial.println("Moved " + joint + " " + direction + " - " + getStatusJSON());
  }
}

void handleWebControl() {
  WiFiClient client = server.available();
  if (client) {
    String request = "";
    String currentLine = "";
    
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        currentLine += c;
        
        if (c == '\n') {
          if (currentLine.length() == 1) { // Empty line means end of headers
            
            // Handle API endpoints
            if (request.indexOf("GET /api/status") != -1) {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-type: application/json");
              client.println("Connection: close");
              client.println();
              client.println(getStatusJSON());
              break;
            }
            
            // Handle movement commands
            if (request.indexOf("GET /move/") != -1) {
              int startPos = request.indexOf("/move/") + 6;
              int endPos = request.indexOf(" HTTP");
              String command = request.substring(startPos, endPos);
              
              int slashPos = command.indexOf('/');
              if (slashPos != -1) {
                String joint = command.substring(0, slashPos);
                String direction = command.substring(slashPos + 1);
                moveServo(joint, direction);
              }
              
              client.println("HTTP/1.1 200 OK");
              client.println("Content-type: application/json");
              client.println("Connection: close");
              client.println();
              client.println(getStatusJSON());
              break;
            }
            
            // Serve main page
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type: text/html");
            client.println("Connection: close");
            client.println();
            client.println(getWebPage());
            break;
          } else {
            if (request.length() == 0) {
              request = currentLine;
            }
            currentLine = "";
          }
        }
      }
    }
    
    delay(1);
    client.stop();
  }
}

String getWebPage() {
  return R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arduino Braccio Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            color: white;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            max-width: 800px;
            width: 100%;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-panel {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }
        
        .status-item {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
        }
        
        .status-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .status-value {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .control-group {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
        }
        
        .control-group h3 {
            text-align: center;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .button-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
        }
        
        .button-row {
            display: flex;
            gap: 10px;
        }
        
        button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            color: white;
            padding: 15px 20px;
            font-size: 16px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.2);
            min-width: 60px;
            font-weight: bold;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px 0 rgba(31, 38, 135, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .connected {
            background: #2ecc71;
            color: white;
        }
        
        .disconnected {
            background: #e74c3c;
            color: white;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .controls {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Connected</div>
    
    <div class="container">
        <h1>🤖 Arduino Braccio Control</h1>
        
        <div class="status-panel" id="statusPanel">
            <div class="status-item">
                <div class="status-label">Base</div>
                <div class="status-value" id="baseValue">90°</div>
            </div>
            <div class="status-item">
                <div class="status-label">Shoulder</div>
                <div class="status-value" id="shoulderValue">45°</div>
            </div>
            <div class="status-item">
                <div class="status-label">Elbow</div>
                <div class="status-value" id="elbowValue">45°</div>
            </div>
            <div class="status-item">
                <div class="status-label">Gripper</div>
                <div class="status-value" id="gripperValue">10°</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <h3>🔄 Base Rotation</h3>
                <div class="button-group">
                    <button onmousedown="startMove('base', 'left')" onmouseup="stopMove()" ontouchstart="startMove('base', 'left')" ontouchend="stopMove()">⬅️ Left</button>
                    <button onmousedown="startMove('base', 'right')" onmouseup="stopMove()" ontouchstart="startMove('base', 'right')" ontouchend="stopMove()">➡️ Right</button>
                </div>
            </div>
            
            <div class="control-group">
                <h3>💪 Shoulder</h3>
                <div class="button-group">
                    <button onmousedown="startMove('shoulder', 'up')" onmouseup="stopMove()" ontouchstart="startMove('shoulder', 'up')" ontouchend="stopMove()">⬆️ Up</button>
                    <button onmousedown="startMove('shoulder', 'down')" onmouseup="stopMove()" ontouchstart="startMove('shoulder', 'down')" ontouchend="stopMove()">⬇️ Down</button>
                </div>
            </div>
            
            <div class="control-group">
                <h3>🦾 Elbow</h3>
                <div class="button-group">
                    <button onmousedown="startMove('elbow', 'up')" onmouseup="stopMove()" ontouchstart="startMove('elbow', 'up')" ontouchend="stopMove()">⬆️ Up</button>
                    <button onmousedown="startMove('elbow', 'down')" onmouseup="stopMove()" ontouchstart="startMove('elbow', 'down')" ontouchend="stopMove()">⬇️ Down</button>
                </div>
            </div>
            
            <div class="control-group">
                <h3>✋ Gripper</h3>
                <div class="button-group">
                    <button onmousedown="startMove('gripper', 'open')" onmouseup="stopMove()" ontouchstart="startMove('gripper', 'open')" ontouchend="stopMove()">🔓 Open</button>
                    <button onmousedown="startMove('gripper', 'close')" onmouseup="stopMove()" ontouchstart="startMove('gripper', 'close')" ontouchend="stopMove()">🔒 Close</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let moveInterval = null;
        let isConnected = true;
        let statusUpdateInterval = null;

        // Update connection status indicator
        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connectionStatus');
            if (connected) {
                statusEl.textContent = '🟢 Connected';
                statusEl.className = 'connection-status connected';
                isConnected = true;
            } else {
                statusEl.textContent = '🔴 Disconnected';
                statusEl.className = 'connection-status disconnected';
                isConnected = false;
            }
        }

        // Send move command to Arduino
        async function sendMoveCommand(joint, direction) {
            if (!isConnected) return;
            
            try {
                const response = await fetch(`/move/${joint}/${direction}`, {
                    method: 'GET',
                    timeout: 1000
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateStatus(data);
                    updateConnectionStatus(true);
                } else {
                    updateConnectionStatus(false);
                }
            } catch (error) {
                console.error('Move command failed:', error);
                updateConnectionStatus(false);
            }
        }

        // Update status display
        function updateStatus(data) {
            document.getElementById('baseValue').textContent = data.base + '°';
            document.getElementById('shoulderValue').textContent = data.shoulder + '°';
            document.getElementById('elbowValue').textContent = data.elbow + '°';
            document.getElementById('gripperValue').textContent = data.gripper + '°';
        }

        // Get current status from Arduino
        async function getStatus() {
            try {
                const response = await fetch('/api/status', {
                    method: 'GET',
                    timeout: 2000
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateStatus(data);
                    updateConnectionStatus(true);
                } else {
                    updateConnectionStatus(false);
                }
            } catch (error) {
                console.error('Status update failed:', error);
                updateConnectionStatus(false);
            }
        }

        // Start continuous movement
        function startMove(joint, direction) {
            if (moveInterval) return; // Prevent multiple intervals
            
            // Send immediate command
            sendMoveCommand(joint, direction);
            
            // Start continuous movement
            moveInterval = setInterval(() => {
                sendMoveCommand(joint, direction);
            }, 100); // Send command every 100ms for smooth movement
        }

        // Stop movement
        function stopMove() {
            if (moveInterval) {
                clearInterval(moveInterval);
                moveInterval = null;
            }
        }

        // Keyboard controls
        document.addEventListener('keydown', function(e) {
            if (e.repeat) return; // Ignore repeated keydown events
            
            switch(e.key) {
                case 'ArrowLeft':
                case 'a':
                case 'A':
                    e.preventDefault();
                    startMove('base', 'left');
                    break;
                case 'ArrowRight':
                case 'd':
                case 'D':
                    e.preventDefault();
                    startMove('base', 'right');
                    break;
                case 'ArrowUp':
                case 'w':
                case 'W':
                    e.preventDefault();
                    startMove('shoulder', 'up');
                    break;
                case 'ArrowDown':
                case 's':
                case 'S':
                    e.preventDefault();
                    startMove('shoulder', 'down');
                    break;
                case 'q':
                case 'Q':
                    e.preventDefault();
                    startMove('elbow', 'up');
                    break;
                case 'e':
                case 'E':
                    e.preventDefault();
                    startMove('elbow', 'down');
                    break;
                case ' ':
                    e.preventDefault();
                    startMove('gripper', 'close');
                    break;
                case 'c':
                case 'C':
                    e.preventDefault();
                    startMove('gripper', 'open');
                    break;
            }
        });

        document.addEventListener('keyup', function(e) {
            // Stop movement when key is released
            stopMove();
        });

        // Prevent context menu on long press for mobile
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Handle touch events properly
        document.addEventListener('touchstart', function(e) {
            e.preventDefault();
        }, { passive: false });

        document.addEventListener('touchend', function(e) {
            e.preventDefault();
            stopMove();
        }, { passive: false });

        // Initialize status updates
        function startStatusUpdates() {
            // Get initial status
            getStatus();
            
            // Update status every 2 seconds
            statusUpdateInterval = setInterval(getStatus, 2000);
        }

        // Stop status updates
        function stopStatusUpdates() {
            if (statusUpdateInterval) {
                clearInterval(statusUpdateInterval);
                statusUpdateInterval = null;
            }
        }

        // Handle page visibility changes
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopMove();
                stopStatusUpdates();
            } else {
                startStatusUpdates();
            }
        });

        // Handle window focus/blur
        window.addEventListener('blur', function() {
            stopMove();
        });

        // Initialize when page loads
        window.addEventListener('load', function() {
            startStatusUpdates();
            updateConnectionStatus(true);
        });

        // Handle page unload
        window.addEventListener('beforeunload', function() {
            stopMove();
            stopStatusUpdates();
        });

        // Add visual feedback for button presses
        document.querySelectorAll('button').forEach(button => {
            button.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(0) scale(0.95)';
            });
            
            button.addEventListener('mouseup', function() {
                this.style.transform = 'translateY(-2px) scale(1)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(-2px) scale(1)';
            });
        });

        // Show keyboard shortcuts on first load
        if (localStorage.getItem('keyboardHelpShown') !== 'true') {
            setTimeout(() => {
                alert('Keyboard Controls:\n\n' +
                      '🔄 Base: ← → (or A/D)\n' +
                      '💪 Shoulder: ↑ ↓ (or W/S)\n' +
                      '🦾 Elbow: Q/E\n' +
                      '✋ Gripper: Space (close) / C (open)\n\n' +
                      'Hold keys for continuous movement!');
                localStorage.setItem('keyboardHelpShown', 'true');
            }, 1000);
        }
    </script>
</body>
</html>
)rawliteral";
}
