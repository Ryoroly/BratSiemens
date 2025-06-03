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
  
  Serial.println("Braccio Robot - Interpolation & Shape Control System");
  Serial.println("=== COMENZI DISPONIBILE ===");
  Serial.println("1. Pentru interpolarea în dreptunghi:");
  Serial.println("   Introduceti coordonatele X si Y separate prin spatiu");
  Serial.println("   Exemplu: 700 800");
  Serial.println("");
  Serial.println("2. Pentru poziții predefinite pentru forme:");
  Serial.println("   cube - Poziția pentru cub");
  Serial.println("   cylinder - Poziția pentru cilindru");
  Serial.println("   halfcircle - Poziția pentru semicerc");
  Serial.println("   arch - Poziția pentru arc/arcadă");
  Serial.println("   triangle - Poziția pentru triunghi");
  Serial.println("   rectangle - Poziția pentru dreptunghi");
  Serial.println("");
  Serial.println("3. Comenzi speciale:");
  Serial.println("   test - Testează toate pozițiile cunoscute");
  Serial.println("   home - Mergi la poziția home");
  Serial.println("===============================");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // Elimină spațiile și caracterele de linie nouă
    input.toLowerCase(); // Convertește la minuscule pentru consistență
    
    // Verificare comenzi speciale pentru forme
    if (input == "cube" || input == "cylinder" || input == "halfcircle" || 
        input == "arch" || input == "triangle" || input == "rectangle") {
      handleShapeCommand(input);
    }
    // Comenzi speciale de test și home
    else if (input == "test") {
      testKnownPositions();
    }
    else if (input == "home") {
      goHome();
    }
    // Verificare dacă inputul conține coordonate X Y
    else if (input.indexOf(' ') > 0) {
      // Parsare coordonate X și Y
      int spaceIndex = input.indexOf(' ');
      float target_x = input.substring(0, spaceIndex).toFloat();
      float target_y = input.substring(spaceIndex + 1).toFloat();
      
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
        Serial.println("Introduceti următoarea comandă:");
      }
    }
    else {
      Serial.println("Comandă necunoscută!");
      Serial.println("Folosiți: coordonate X Y, nume formă (cube, cylinder, etc.), 'test' sau 'home'");
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

// Funcție pentru gestionarea comenzilor de forme predefinite
void handleShapeCommand(String command) {
  Serial.print("Mergem la poziția pentru: ");
  Serial.println(command);
  
  // Selectăm poziția în funcție de input
  if (command == "cube") {
    Braccio.ServoMovement(100, 180, 120, 130, 160, 60, 30);
    Serial.println("Poziția pentru CUB - executată!");
  } else if (command == "cylinder") {
    Braccio.ServoMovement(100, 160, 130, 120, 160, 60, 50);
    Serial.println("Poziția pentru CILINDRU - executată!");
  } else if (command == "halfcircle") {
    Braccio.ServoMovement(100, 140, 140, 120, 140, 60, 50);
    Serial.println("Poziția pentru SEMICERC - executată!");
  } else if (command == "arch") {
    Braccio.ServoMovement(100, 0, 130, 130, 160, 60, 50);
    Serial.println("Poziția pentru ARC - executată!");
  } else if (command == "triangle") {
    Braccio.ServoMovement(100, 20, 140, 120, 140, 60, 50);
    Serial.println("Poziția pentru TRIUNGHI - executată!");
  } else if (command == "rectangle") {
    Braccio.ServoMovement(100, 40, 150, 100, 140, 60, 50);
    Serial.println("Poziția pentru DREPTUNGHI - executată!");
  } else {
    Serial.println("Formă necunoscută! Verificați comanda.");
  }
  
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru poziția home (sigură)
void goHome() {
  Serial.println("Mergem la poziția HOME...");
  Braccio.ServoMovement(100, 90, 90, 90, 90, 90, 10); // Poziție neutră
  Serial.println("Poziția HOME - executată!");
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru testare rapidă cu poziții cunoscute
void testKnownPositions() {
  Serial.println("Test poziții cunoscute:");
  
  Serial.println("Mergem la stânga jos...");
  moveToPosition(pos_stanga_jos);
  delay(200);
  
  Serial.println("Mergem la dreapta jos...");
  moveToPosition(pos_dreapta_jos);
  delay(200);
  
  Serial.println("Mergem la dreapta sus...");
  moveToPosition(pos_dreapta_sus);
  delay(200);
  
  Serial.println("Mergem la stânga sus...");
  moveToPosition(pos_stanga_sus);
  delay(200);
}