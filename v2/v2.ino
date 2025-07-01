//se ridica la 90 de grade de la o pozitie la alta ,  cand se muta in home se duce tot la 90 de grade cupla 2 si 1 se duce la 0 grade
#include <Braccio.h>
#include <Servo.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_ver;
Servo wrist_rot;
Servo gripper;

struct ServoPosition {
  int m1_base;
  int m2_shoulder;
  int m3_elbow;
  int m4_wrist_vert;
  int m5_wrist_rot;
  int m6_gripper;
};

// Poziții pentru colțurile dreptunghiului
ServoPosition pos_stanga_jos = {60, 120, 140, 160, 10, 10};
ServoPosition pos_dreapta_jos = {110, 120, 140, 160, 50, 10};
ServoPosition pos_dreapta_sus = {110, 150, 100, 160, 20, 10};
ServoPosition pos_stanga_sus = {70, 150, 100, 160, 20, 10};

// Poziție de ridicare (cupla 2 la 90 grade pentru a evita coliziunile)
ServoPosition pos_ridicare = {90, 90, 90, 90, 90, 10}; // Poziție înaltă de siguranță

struct Point2D {
  float x;
  float y;
};

int xul = 1290;
int yul = 572;
Point2D coord_stanga_jos = {0,0};
Point2D coord_dreapta_jos = {xul ,0};
Point2D coord_dreapta_sus = {xul , yul}; 
Point2D coord_stanga_sus = {0 , yul}; // Corectare: era "y" în loc de "yul"

void setup() {
  Serial.begin(9600);
  
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
    input.trim();
    input.toLowerCase();
    
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
      goHomeSafe();
    }
    // Verificare dacă inputul conține coordonate X Y
    else if (input.indexOf(' ') > 0) {
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
        
        // Executare mișcare sigură
        moveToPositionSafe(target_pos);
        
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
  float bottom_interp = bottom_left + (bottom_right - bottom_left) * x;
  float top_interp = top_left + (top_right - top_left) * x;
  float result = bottom_interp + (top_interp - bottom_interp) * y;
  
  return (int)round(result);
}

// Funcție pentru mișcare sigură cu poziție intermediară de ridicare
void moveToPositionSafe(ServoPosition pos) {
  Serial.println("Ridicare la poziția de siguranță...");
  // Primul pas: ridicăm robotul la poziția de siguranță
  Braccio.ServoMovement(100, 
                        pos_ridicare.m1_base,
                        pos_ridicare.m2_shoulder,
                        pos_ridicare.m3_elbow,
                        pos_ridicare.m4_wrist_vert,
                        pos_ridicare.m5_wrist_rot,
                        pos_ridicare.m6_gripper);
  
  delay(1000); // Așteptăm să se termine mișcarea
  
  Serial.println("Mișcare către poziția țintă...");
  // Al doilea pas: mergem la poziția țintă
  Braccio.ServoMovement(100, 
                        pos.m1_base,
                        pos.m2_shoulder,
                        pos.m3_elbow,
                        pos.m4_wrist_vert,
                        pos.m5_wrist_rot,
                        pos.m6_gripper);
}

// Funcție pentru mișcare simplă (fără ridicare intermediară)
void moveToPosition(ServoPosition pos) {
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
  
  // Ridicăm întâi robotul pentru siguranță
  Serial.println("Ridicare la poziția de siguranță...");
  moveToPosition(pos_ridicare);
  delay(1000);
  
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

// Funcție pentru poziția home cu secvență de siguranță
void goHomeSafe() {
  Serial.println("Secvența HOME - Pasul 1: Cupla 1 la 0 grade...");
  // Primul pas: cupla 1 (base) la 0 grade, cupla 2 (shoulder) la 90 grade
  Braccio.ServoMovement(100, 0, 90, 90, 90, 90, 10);
  delay(1500); // Așteptăm să se termine mișcarea
  
  Serial.println("Secvența HOME - Pasul 2: Poziția HOME finală...");
  // Al doilea pas: mergem la poziția HOME normală
  Braccio.ServoMovement(100, 90, 90, 90, 90, 90, 10);
  
  Serial.println("Poziția HOME - executată cu succes!");
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru poziția home simplă (cea originală)
void goHome() {
  Serial.println("Mergem la poziția HOME...");
  Braccio.ServoMovement(100, 90, 90, 90, 90, 90, 10);
  Serial.println("Poziția HOME - executată!");
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru testare rapidă cu poziții cunoscute
void testKnownPositions() {
  Serial.println("Test poziții cunoscute:");
  
  Serial.println("Mergem la stânga jos...");
  moveToPositionSafe(pos_stanga_jos);
  delay(2000);
  
  Serial.println("Mergem la dreapta jos...");
  moveToPositionSafe(pos_dreapta_jos);
  delay(2000);
  
  Serial.println("Mergem la dreapta sus...");
  moveToPositionSafe(pos_dreapta_sus);
  delay(2000);
  
  Serial.println("Mergem la stânga sus...");
  moveToPositionSafe(pos_stanga_sus);
  delay(2000);
  
  Serial.println("Test complet!");
}