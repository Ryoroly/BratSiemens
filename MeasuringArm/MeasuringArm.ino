#include <Braccio.h>
#include <Servo.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;

// Ultrasonic sensor pins
const int trigPin = 8;
const int echoPin = 7;

// Geometry: Updated with actual measurements
const float baseToSensorLength = 13.0;  // 13cm from base rotation to sensor mount
const float sensorWidth = 7.0;          // 7cm width to receiver
const float receiverToTransmitter = 4.0; // 4cm from length end to transmitter
const float sensorSeparation = 3.0;     // 3cm between receiver and transmitter

// Calculate effective measurement point (center between transmitter and receiver)
//const float effectiveRadius = baseToSensorLength + (receiverToTransmitter - sensorSeparation/2.0);

// Geometry: distance from base rotation axis to sensor [cm]
const float baseRadius = 12.8;
const float effectiveRadius = 15.5; // Actual measurement point: 13 + (4 - 1.5) = 15.5 cm

// Baseline configuration - ADD THESE MISSING CONSTANTS
float MANUAL_BASELINE = 15.0; // Your measured baseline in cm
bool USE_MANUAL_BASELINE = false; // Set to true to use manual baseline

// Improved measurement parameters - ADD THESE MISSING CONSTANTS
const float DETECTION_THRESHOLD = 1.0; // Reduced threshold for better detection
const float END_THRESHOLD = 0.8; // Threshold for detecting object end

// Sweep parameters
const int startAngle = 10;   // Starting base angle (°)
const int endAngle   = 150;  // Ending base angle (°)
const int stepDelay  = 800;   // Delay for servo movement

// Anti-wobble parameters
const int measurementDelay = 600;  // Extra delay for stabilization
const int stepSize = 2;            // Larger steps to reduce movements

// Debug mode flag
bool debugMode = false;
bool autoMeasure = false;
bool debugMeasure = false;

// Current servo positions
int currentM1 = 30;  // Base (0-180°)
int currentM2 = 100;  // Shoulder (15-165°)
int currentM3 = 165;  // Elbow (0-180°)
int currentM4 = 90;  // Wrist vertical (0-180°)
int currentM5 = 110;  // Wrist rotation (0-180°)
int currentM6 = 50;  // Gripper (10-73°)

// Measurement servo positions
//int measure_M1 = 30;  // Base (0-180°)
int measure_M2 = 100;// Shoulder (15-165°)
int measure_M3 = 165; // Elbow (0-180°)
int measure_M4 = 90; // Wrist vertical (0-180°)
int measure_M5 = 110; // Wrist rotation (0-180°)
int measure_M6 = 50; // Gripper (10-73°)

void setup() {
  Serial.begin(9600);
  Braccio.begin();
  
  // Set up ultrasonic sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  // Move to initial scanning position: arm extended, sensor facing down
  //                    (step, M1,  M2,  M3,  M4,  M5,  M6)
  Braccio.ServoMovement(20, currentM1, currentM2, currentM3, currentM4, currentM5, currentM6);
  delay(1000);
  
  Serial.println("=== Braccio Measuring Arm Ready! ===");
  Serial.println("Commands:");
  Serial.println("  'debug' - Enter debug mode for manual control");
  Serial.println("  'start_measure' - Start automatic measuring");
  Serial.println("  'debug_measure' - Start debug measurement (raw data)");
  Serial.println("  'stop' - Stop current operation");
  Serial.println("  'baseline_manual' - Use manual baseline (15cm)");
  Serial.println("  'baseline_auto' - Use automatic baseline detection");
  Serial.println("  'baseline=XX.X' - Set manual baseline to XX.X cm");
  Serial.println();
  Serial.println("Debug mode commands:");
  Serial.println("  M1=xx (Base: 0-180°)");
  Serial.println("  M2=xx (Shoulder: 15-165°)");
  Serial.println("  M3=xx (Elbow: 0-180°)");
  Serial.println("  M4=xx (Wrist Vert: 0-180°)");
  Serial.println("  M5=xx (Wrist Rot: 0-180°)");
  Serial.println("  M6=xx (Gripper: 10-73°)");
  Serial.println("=====================================");
}
// Improved ultrasonic reading with median filtering
float readUltrasonicCM() {
  const int numReadings = 5;
  float readings[numReadings];
  int validCount = 0;
  
  // Take multiple readings
  for(int i = 0; i < numReadings; i++) {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    
    long duration = pulseIn(echoPin, HIGH, 30000);
    
    if (duration > 0) {
      float distance = (duration * 0.0343) / 2.0;
      if (distance >= 2.0 && distance <= 400.0) {
        readings[validCount] = distance;
        validCount++;
      }
    }
    delay(10); // Small delay between readings
  }
  
  if (validCount == 0) {
    return -1.0;
  }
  
  // Sort readings for median
  for(int i = 0; i < validCount-1; i++) {
    for(int j = i+1; j < validCount; j++) {
      if(readings[i] > readings[j]) {
        float temp = readings[i];
        readings[i] = readings[j];
        readings[j] = temp;
      }
    }
  }
  
  // Return median value
  return readings[validCount/2];
}


// Process serial commands
void processSerialCommand() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toLowerCase();
    
    if (command == "debug") {
      debugMode = true;
      autoMeasure = false;
      debugMeasure = false;
      Serial.println("DEBUG MODE ACTIVATED");
      Serial.println("Enter servo commands (e.g., M1=90) or 'stop' to exit");
      printCurrentPositions();
    }
    else if (command == "start_measure") {
      debugMode = false;
      autoMeasure = true;
      debugMeasure = false;
      Serial.println("STARTING AUTOMATIC MEASUREMENT");
    }
    else if (command == "debug_measure") {
      debugMode = false;
      autoMeasure = false;
      debugMeasure = true;
      Serial.println("STARTING DEBUG MEASUREMENT - RAW DATA MODE");
    }
    else if (command == "stop") {
      debugMode = false;
      autoMeasure = false;
      debugMeasure = false;
      Serial.println("STOPPED - Ready for new commands");
    }
    else if (debugMode && command.startsWith("m")) {
      processServoCommand(command);
    }
    else if (command != "") {
      Serial.println("Unknown command. Use 'debug', 'start_measure', 'debug_measure', or 'stop'");
    }
    else if (command == "baseline_auto") {
      USE_MANUAL_BASELINE = false;
      Serial.println("Switched to automatic baseline detection");
    }
    else if (command == "baseline_manual") {
      USE_MANUAL_BASELINE = true;
      Serial.print("Switched to manual baseline: ");
      Serial.print(MANUAL_BASELINE);
      Serial.println(" cm");
    }
    else if (command.startsWith("baseline=")) {
      float newBaseline = command.substring(9).toFloat();
      if (newBaseline > 5.0 && newBaseline < 50.0) {
        MANUAL_BASELINE = newBaseline;
        USE_MANUAL_BASELINE = true;
        Serial.print("Manual baseline set to: ");
        Serial.print(MANUAL_BASELINE);
        Serial.println(" cm");
      } else {
        Serial.println("Invalid baseline. Use range 5-50 cm");
      }
    }
  }
}

void performDebugMeasurement() {
  Serial.println("=== ENHANCED DEBUG MEASUREMENT MODE ===");
  Serial.println("Raw data with statistics");
  Serial.println("Format: Angle,Distance,Min,Max,StdDev,Samples");
  Serial.println("Geometry: Base to sensor = 15.5cm effective radius");
  Serial.println("==========================================");
  
  // Move to start position
  Braccio.ServoMovement(25, startAngle, measure_M2, measure_M3, measure_M4, measure_M5, measure_M6);
  delay(2000); // Longer initial delay
  
  for(int ang = startAngle; ang <= endAngle && debugMeasure; ang += stepSize) {
    processSerialCommand();
    if (!debugMeasure) {
      Serial.println("Debug measurement stopped by user");
      return;
    }
    
    // Move to angle
    Braccio.ServoMovement(25, ang, measure_M2, measure_M3, measure_M4, measure_M5, measure_M6);
    delay(measurementDelay);
    
    // Take multiple readings for statistics
    const int samples = 10;
    float readings[samples];
    int validCount = 0;
    float sum = 0, sumSquares = 0;
    float minVal = 999, maxVal = 0;
    
    for(int i = 0; i < samples; i++) {
      digitalWrite(trigPin, LOW);
      delayMicroseconds(2);
      digitalWrite(trigPin, HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPin, LOW);
      
      long duration = pulseIn(echoPin, HIGH, 30000);
      
      if (duration > 0) {
        float distance = (duration * 0.0343) / 2.0;
        if (distance >= 2.0 && distance <= 400.0) {
          readings[validCount] = distance;
          sum += distance;
          sumSquares += distance * distance;
          if (distance < minVal) minVal = distance;
          if (distance > maxVal) maxVal = distance;
          validCount++;
        }
      }
      delay(20);
    }
    
    if (validCount > 0) {
      float mean = sum / validCount;
      float variance = (sumSquares / validCount) - (mean * mean);
      float stdDev = sqrt(variance);
      
      // Output: Angle, Mean, Min, Max, StdDev, Sample count
      Serial.print(ang);
      Serial.print(",");
      Serial.print(mean, 2);
      Serial.print(",");
      Serial.print(minVal, 2);
      Serial.print(",");
      Serial.print(maxVal, 2);
      Serial.print(",");
      Serial.print(stdDev, 2);
      Serial.print(",");
      Serial.println(validCount);
    } else {
      Serial.print(ang);
      Serial.println(",-1.00,-1.00,-1.00,-1.00,0");
    }
  }
  
  Serial.println("=== DEBUG MEASUREMENT COMPLETE ===");
  Braccio.ServoMovement(25, startAngle, measure_M2, measure_M3, measure_M4, measure_M5, measure_M6);
  delay(500);
  debugMeasure = false;
  Serial.println("Ready for new commands.");
}



// Process servo movement commands in debug mode
void processServoCommand(String command) {
  int equalPos = command.indexOf('=');
  if (equalPos == -1) {
    Serial.println("Invalid format. Use: M1=90");
    return;
  }
  
  String servoStr = command.substring(0, equalPos);
  int angle = command.substring(equalPos + 1).toInt();
  
  // Validate and move servo
  if (servoStr == "m1") {
    if (angle >= 0 && angle <= 180) {
      currentM1 = angle;
      Serial.print("Moving M1 (Base) to ");
      Serial.println(angle);
    } else {
      Serial.println("M1 range: 0-180°");
      return;
    }
  }
  else if (servoStr == "m2") {
    if (angle >= 15 && angle <= 165) {
      currentM2 = angle;
      Serial.print("Moving M2 (Shoulder) to ");
      Serial.println(angle);
    } else {
      Serial.println("M2 range: 15-165°");
      return;
    }
  }
  else if (servoStr == "m3") {
    if (angle >= 0 && angle <= 180) {
      currentM3 = angle;
      Serial.print("Moving M3 (Elbow) to ");
      Serial.println(angle);
    } else {
      Serial.println("M3 range: 0-180°");
      return;
    }
  }
  else if (servoStr == "m4") {
    if (angle >= 0 && angle <= 180) {
      currentM4 = angle;
      Serial.print("Moving M4 (Wrist Vert) to ");
      Serial.println(angle);
    } else {
      Serial.println("M4 range: 0-180°");
      return;
    }
  }
  else if (servoStr == "m5") {
    if (angle >= 0 && angle <= 180) {
      currentM5 = angle;
      Serial.print("Moving M5 (Wrist Rot) to ");
      Serial.println(angle);
    } else {
      Serial.println("M5 range: 0-180°");
      return;
    }
  }
  else if (servoStr == "m6") {
    if (angle >= 10 && angle <= 73) {
      currentM6 = angle;
      Serial.print("Moving M6 (Gripper) to ");
      Serial.println(angle);
    } else {
      Serial.println("M6 range: 10-73°");
      return;
    }
  }
  else {
    Serial.println("Invalid servo. Use M1-M6");
    return;
  }
  
  // Execute movement
  Braccio.ServoMovement(20, currentM1, currentM2, currentM3, currentM4, currentM5, currentM6);
  delay(500);
  
  // Show current distance reading
  float dist = readUltrasonicCM();
  Serial.print("Current distance: ");
  Serial.print(dist);
  Serial.println(" cm");
}

// Print current servo positions
void printCurrentPositions() {
  Serial.println("Current positions:");
  Serial.print("M1 (Base): "); Serial.println(currentM1);
  Serial.print("M2 (Shoulder): "); Serial.println(currentM2);
  Serial.print("M3 (Elbow): "); Serial.println(currentM3);
  Serial.print("M4 (Wrist Vert): "); Serial.println(currentM4);
  Serial.print("M5 (Wrist Rot): "); Serial.println(currentM5);
  Serial.print("M6 (Gripper): "); Serial.println(currentM6);
}

// Automatic measuring function
// Enhanced automatic measuring function
// Enhanced automatic measuring function with manual baseline
void performMeasurement() {
  Serial.println("Starting enhanced measurement...");
  Serial.print("Using effective radius: ");
  Serial.print(effectiveRadius);
  Serial.println(" cm");
  
  // Move to start position
  Braccio.ServoMovement(25, startAngle, measure_M2, measure_M3, measure_M4, measure_M5, measure_M6);
  delay(2000);
  
  float baseline;
  
  if (USE_MANUAL_BASELINE) {
    baseline = MANUAL_BASELINE;
    Serial.print("Using manual baseline: ");
    Serial.print(baseline, 2);
    Serial.println(" cm");
  } else {
    // Automatic baseline measurement (your existing code)
    Serial.println("Measuring baseline automatically...");
    float baselineSum = 0;
    int validBaseline = 0;
    
    for(int i = 0; i < 15; i++) {
      float reading = readUltrasonicCM();
      if (reading > 0) {
        baselineSum += reading;
        validBaseline++;
      }
      delay(100);
    }
    
    if (validBaseline < 5) {
      Serial.println("ERROR: Insufficient baseline readings!");
      autoMeasure = false;
      return;
    }
    
    baseline = baselineSum / validBaseline;
    Serial.print("Automatic baseline: ");
    Serial.print(baseline, 2);
    Serial.print(" cm (from ");
    Serial.print(validBaseline);
    Serial.println(" readings)");
  }
  
  // Object detection variables
  bool objectFound = false;
  float minDist = baseline;
  int angleObjectStart = startAngle;
  int angleObjectEnd = endAngle;
  
  // Store all measurements for better analysis
  struct Measurement {
    int angle;
    float distance;
    float difference;
  };
  
  const int maxMeasurements = 100;
  Measurement measurements[maxMeasurements];
  int measurementCount = 0;
  
  Serial.println("Starting sweep...");
  
  // Sweep and collect data
  for(int ang = startAngle; ang <= endAngle && autoMeasure && measurementCount < maxMeasurements; ang += stepSize) {
    processSerialCommand();
    if (!autoMeasure) return;
    
    Braccio.ServoMovement(25, ang, measure_M2, measure_M3, measure_M4, measure_M5, measure_M6);
    delay(measurementDelay);
    
    float dist = readUltrasonicCM();
    
    if (dist > 0) {
      float difference = baseline - dist;
      
      // Store measurement
      measurements[measurementCount].angle = ang;
      measurements[measurementCount].distance = dist;
      measurements[measurementCount].difference = difference;
      measurementCount++;
      
      // Track minimum distance
      if (dist < minDist) {
        minDist = dist;
      }
      
      // Object detection logic
      if (!objectFound && difference > DETECTION_THRESHOLD) {
        objectFound = true;
        angleObjectStart = ang;
        Serial.print("Object detected at ");
        Serial.print(ang);
        Serial.print("° (diff: ");
        Serial.print(difference, 2);
        Serial.println(" cm)");
      }
      
      if (objectFound && difference < END_THRESHOLD) {
        angleObjectEnd = ang;
        Serial.print("Object end at ");
        Serial.print(ang);
        Serial.println("°");
        break;
      }
      
      Serial.print("Angle: ");
      Serial.print(ang);
      Serial.print("°, Distance: ");
      Serial.print(dist, 2);
      Serial.print(" cm, Diff: ");
      Serial.print(difference, 2);
      Serial.println(" cm");
    }
  }
  
  // Enhanced analysis of measurements
  if (objectFound && measurementCount > 0) {
    // Find the actual object boundaries by analyzing the data
    int actualStart = angleObjectStart;
    int actualEnd = angleObjectEnd;
    float maxHeight = 0;
    
    // Find maximum height and refine boundaries
    for (int i = 0; i < measurementCount; i++) {
      if (measurements[i].difference > DETECTION_THRESHOLD) {
        if (measurements[i].difference > maxHeight) {
          maxHeight = measurements[i].difference;
        }
        // Update actual boundaries
        if (measurements[i].angle < actualStart || actualStart == angleObjectStart) {
          actualStart = measurements[i].angle;
        }
        if (measurements[i].angle > actualEnd) {
          actualEnd = measurements[i].angle;
        }
      }
    }
    
    // Calculate measurements with refined boundaries
    float angleDeg = actualEnd - actualStart;
    float angleRad = angleDeg * PI / 180.0;
    float objectLength = effectiveRadius * angleRad;
    float objectHeight = maxHeight;
    
    // Calculate volume approximation (assuming rectangular cross-section)
    float estimatedWidth = 5.0; // Estimate or add width measurement
    float volume = objectLength * objectHeight * estimatedWidth;
    
    Serial.println("=== ENHANCED OBJECT MEASUREMENTS ===");
    Serial.print("Object length: ");
    Serial.print(objectLength, 2);
    Serial.println(" cm");
    Serial.print("Object height: ");
    Serial.print(objectHeight, 2);
    Serial.println(" cm");
    Serial.print("Estimated volume: ");
    Serial.print(volume, 1);
    Serial.println(" cm³");
    Serial.print("Angular span: ");
    Serial.print(angleDeg, 1);
    Serial.println("°");
    Serial.print("Refined boundaries: ");
    Serial.print(actualStart);
    Serial.print("° to ");
    Serial.print(actualEnd);
    Serial.println("°");
    Serial.print("Baseline used: ");
    Serial.print(baseline, 2);
    Serial.println(" cm");
    Serial.print("Effective radius: ");
    Serial.print(effectiveRadius, 1);
    Serial.println(" cm");
    Serial.println("====================================");
    
    // Output measurement summary for analysis
    Serial.println("=== MEASUREMENT SUMMARY ===");
    for (int i = 0; i < measurementCount; i++) {
      if (measurements[i].difference > DETECTION_THRESHOLD) {
        Serial.print("Angle ");
        Serial.print(measurements[i].angle);
        Serial.print("°: ");
        Serial.print(measurements[i].distance, 2);
        Serial.print(" cm (height: ");
        Serial.print(measurements[i].difference, 2);
        Serial.println(" cm)");
      }
    }
    Serial.println("===========================");
    
  } else {
    Serial.println("No object detected in sweep range.");
    if (measurementCount > 0) {
      Serial.println("Raw measurements taken:");
      for (int i = 0; i < min(10, measurementCount); i++) {
        Serial.print("Angle ");
        Serial.print(measurements[i].angle);
        Serial.print("°: ");
        Serial.print(measurements[i].distance, 2);
        Serial.print(" cm (diff: ");
        Serial.print(measurements[i].difference, 2);
        Serial.println(" cm)");
      }
    }
  }
  
  Braccio.ServoMovement(25, startAngle, measure_M2, measure_M3, measure_M4, measure_M5, measure_M6);
  delay(500);
  autoMeasure = false;
  Serial.println("Measurement complete.");
}





void loop() {
  processSerialCommand();
  
  if (autoMeasure) {
    performMeasurement();
  }
  
  if (debugMeasure) {
    performDebugMeasurement();
  }
  
  delay(100);
}
