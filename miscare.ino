#include <Braccio.h>
#include <Servo.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_ver;
Servo wrist_rot;
Servo gripper;

// Poziții cunoscute ale brațului (în grade pentru servomotoare)
struct ServoPosition {
  int m1_base;
  int m2_shoulder;
  int m3_elbow;
  int m4_wrist_vert;
  int m5_wrist_rot;
  int m6_gripper;
};

// Poziții de referință
ServoPosition pos_stanga_jos = {80, 120, 130, 180, 110, 50};
ServoPosition pos_dreapta_jos = {110, 135, 120, 170, 110, 50};
ServoPosition pos_dreapta_sus = {100, 165, 80, 160, 110, 50};
ServoPosition pos_stanga_sus = {80, 165, 70, 170, 110, 50};

// Coordonate corespunzătoare în sistemul de coordonate X,Y
struct Point2D {
  float x;
  float y;
};

Point2D coord_stanga_jos = {958.79, 673.24};
Point2D coord_dreapta_jos = {425.7, 576.1};
Point2D coord_dreapta_sus = {366.9, 950.8}; // Am corectat Y=950.8 (presupun că era o greșeală de scriere)
Point2D coord_stanga_sus = {1059, 1105.3};

void setup() {
  Serial.begin(9600);
  
  // Inițializare Braccio
  Braccio.begin();
  
  Serial.println("Braccio Robot - Interpolation System");
  Serial.println("Introduceti coordonatele X si Y separate prin spatiu:");
  Serial.println("Exemplu: 700 800");
}

void loop() {
  if (Serial.available() > 0) {
    // Citire coordonate X și Y de la utilizator
    float target_x = Serial.parseFloat();
    float target_y = Serial.parseFloat();
    
    if (target_x != 0 || target_y != 0) {
      Serial.print("Coordonate țintă: X=");
      Serial.print(target_x);
      Serial.print(", Y=");
      Serial.println(target_y);
      
      // Calculare poziții servo prin interpolarea bilineară
      ServoPosition target_pos = calculateInterpolatedPosition(target_x, target_y);
      
      // Afișare poziții calculate
      Serial.println("Poziții servo calculate:");
      Serial.print("M1 (Base): "); Serial.println(target_pos.m1_base);
      Serial.print("M2 (Shoulder): "); Serial.println(target_pos.m2_shoulder);
      Serial.print("M3 (Elbow): "); Serial.println(target_pos.m3_elbow);
      Serial.print("M4 (Wrist Vert): "); Serial.println(target_pos.m4_wrist_vert);
      Serial.print("M5 (Wrist Rot): "); Serial.println(target_pos.m5_wrist_rot);
      Serial.print("M6 (Gripper): "); Serial.println(target_pos.m6_gripper);
      
      // Executare mișcare
      moveToPosition(target_pos);
      
      Serial.println("Mișcare completă!");
      Serial.println("Introduceti următoarele coordonate:");
    }
  }
}

ServoPosition calculateInterpolatedPosition(float x, float y) {
  ServoPosition result;
  
  // Calculare factori de interpolată normalizați
  // Găsim poziția relativă în dreptunghi (0-1 pentru fiecare axă)
  
  float min_x = min(min(coord_stanga_jos.x, coord_dreapta_jos.x), 
                    min(coord_dreapta_sus.x, coord_stanga_sus.x));
  float max_x = max(max(coord_stanga_jos.x, coord_dreapta_jos.x), 
                    max(coord_dreapta_sus.x, coord_stanga_sus.x));
  
  float min_y = min(min(coord_stanga_jos.y, coord_dreapta_jos.y), 
                    min(coord_dreapta_sus.y, coord_stanga_sus.y));
  float max_y = max(max(coord_stanga_jos.y, coord_dreapta_jos.y), 
                    max(coord_dreapta_sus.y, coord_stanga_sus.y));
  
  // Normalizare coordonate (0-1)
  float norm_x = (x - min_x) / (max_x - min_x);
  float norm_y = (y - min_y) / (max_y - min_y);
  
  // Limitare la intervalul [0,1]
  norm_x = constrain(norm_x, 0.0, 1.0);
  norm_y = constrain(norm_y, 0.0, 1.0);
  
  // Interpolarea bilineară pentru fiecare servo
  result.m1_base = interpolateBilinear(
    pos_stanga_jos.m1_base, pos_dreapta_jos.m1_base,
    pos_stanga_sus.m1_base, pos_dreapta_sus.m1_base,
    norm_x, norm_y
  );
  
  result.m2_shoulder = interpolateBilinear(
    pos_stanga_jos.m2_shoulder, pos_dreapta_jos.m2_shoulder,
    pos_stanga_sus.m2_shoulder, pos_dreapta_sus.m2_shoulder,
    norm_x, norm_y
  );
  
  result.m3_elbow = interpolateBilinear(
    pos_stanga_jos.m3_elbow, pos_dreapta_jos.m3_elbow,
    pos_stanga_sus.m3_elbow, pos_dreapta_sus.m3_elbow,
    norm_x, norm_y
  );
  
  result.m4_wrist_vert = interpolateBilinear(
    pos_stanga_jos.m4_wrist_vert, pos_dreapta_jos.m4_wrist_vert,
    pos_stanga_sus.m4_wrist_vert, pos_dreapta_sus.m4_wrist_vert,
    norm_x, norm_y
  );
  
  result.m5_wrist_rot = interpolateBilinear(
    pos_stanga_jos.m5_wrist_rot, pos_dreapta_jos.m5_wrist_rot,
    pos_stanga_sus.m5_wrist_rot, pos_dreapta_sus.m5_wrist_rot,
    norm_x, norm_y
  );
  
  result.m6_gripper = interpolateBilinear(
    pos_stanga_jos.m6_gripper, pos_dreapta_jos.m6_gripper,
    pos_stanga_sus.m6_gripper, pos_dreapta_sus.m6_gripper,
    norm_x, norm_y
  );
  
  return result;
}

int interpolateBilinear(int bottom_left, int bottom_right, int top_left, int top_right, float x, float y) {
  // Interpolarea bilineară
  // Primul pas: interpolarea pe axa X pentru partea de jos și de sus
  float bottom_interp = bottom_left + (bottom_right - bottom_left) * x;
  float top_interp = top_left + (top_right - top_left) * x;
  
  // Al doilea pas: interpolarea pe axa Y
  float result = bottom_interp + (top_interp - bottom_interp) * y;
  
  return (int)round(result);
}

void moveToPosition(ServoPosition pos) {
  // Folosește comanda Braccio specifică cu viteza de 100 (poți ajusta viteza)
  Braccio.ServoMovement(100, 
                        pos.m1_base,
                        pos.m2_shoulder,
                        pos.m3_elbow,
                        pos.m4_wrist_vert,
                        pos.m5_wrist_rot,
                        pos.m6_gripper);
}

// Funcție pentru testare rapidă cu poziții cunoscute
void testKnownPositions() {
  Serial.println("Test poziții cunoscute:");
  
  Serial.println("Mergem la stânga jos...");
  moveToPosition(pos_stanga_jos);
  delay(2000);
  
  Serial.println("Mergem la dreapta jos...");
  moveToPosition(pos_dreapta_jos);
  delay(2000);
  
  Serial.println("Mergem la dreapta sus...");
  moveToPosition(pos_dreapta_sus);
  delay(2000);
  
  Serial.println("Mergem la stânga sus...");
  moveToPosition(pos_stanga_sus);
  delay(2000);
}