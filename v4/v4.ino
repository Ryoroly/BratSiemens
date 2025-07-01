//merge totul fara bluethoot 

//pot sa introduc o pozitie de la tastatura cum ar fi x,y,obiect si trebuie sa se duca la obiect sa il apuce sa se duca apoi la pozitia 
//obiectului si dupa sa ii dea drumul si sa se miste pe deasupra
#include <Braccio.h>
#include <Servo.h>

// Variabile pentru controlul delay-urilor - modifică aceste valori pentru a schimba viteza
int delayModificabil = 10; // Delay normal în milisecunde - poate fi modificat aici
int delayBraccioMovement = 10; // Delay pentru Braccio.ServoMovement() - poate fi modificat aici

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

// Poziție de trecere pentru toate mișcările
ServoPosition pos_trecere = {90, 100, 165, 90, 110, 10}; // M2=100, M3=165 pentru trecere

// Poziții pentru obiecte predefinite
ServoPosition pos_cube = {180, 120, 130, 160, 60, 10};
ServoPosition pos_cylinder = {160, 130, 120, 160, 60, 10};
ServoPosition pos_halfcircle = {140, 140, 120, 140, 60, 10};
ServoPosition pos_arch = {0, 130, 130, 160, 60, 10};
ServoPosition pos_triangle = {20, 140, 120, 140, 60, 10};
ServoPosition pos_rectangle = {40, 150, 100, 140, 60, 10};
ServoPosition pos_cerc = {100, 140, 110, 150, 60, 10}; // Poziție nouă pentru cerc

struct Point2D {
  float x;
  float y;
};

int xul = 1290;
int yul = 572;
Point2D coord_stanga_jos = {0,0};
Point2D coord_dreapta_jos = {xul ,0};
Point2D coord_dreapta_sus = {xul , yul}; 
Point2D coord_stanga_sus = {0 , yul};

void setup() {
  Serial.begin(9600);
  
  Braccio.begin();
  
  Serial.println("Braccio Robot - Sistem de Transport Obiecte");
  Serial.print("Delay normal configurat la: ");
  Serial.print(delayModificabil);
  Serial.println(" ms");
  Serial.print("Delay Braccio Movement configurat la: ");
  Serial.print(delayBraccioMovement);
  Serial.println(" ms");
  Serial.println("=== COMENZI DISPONIBILE ===");
  Serial.println("1. Pentru transport obiecte:");
  Serial.println("   Introduceti: X Y OBIECT");
  Serial.println("   Exemplu: 700 800 cube");
  Serial.println("   Exemplu: 500 300 cerc");
  Serial.println("   Obiecte disponibile: cube, cylinder, halfcircle, arch, triangle, rectangle, cerc");
  Serial.println("");
  Serial.println("2. Pentru interpolarea simplă în dreptunghi:");
  Serial.println("   Introduceti coordonatele X si Y separate prin spatiu");
  Serial.println("   Exemplu: 700 800");
  Serial.println("");
  Serial.println("3. Pentru poziții predefinite pentru forme:");
  Serial.println("   cube, cylinder, halfcircle, arch, triangle, rectangle, cerc");
  Serial.println("");
  Serial.println("4. Comenzi speciale:");
  Serial.println("   test - Testează toate pozițiile cunoscute");
  Serial.println("   home - Mergi la poziția home");
  Serial.println("===============================");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    input.toLowerCase();
    
    // Numărăm cuvintele din input
    int wordCount = countWords(input);
    
    // Verificare comandă de transport (3 cuvinte: X Y OBIECT)
    if (wordCount == 3) {
      handleTransportCommand(input);
    }
    // Verificare comenzi speciale pentru forme (1 cuvânt)
    else if (input == "cube" || input == "cylinder" || input == "halfcircle" || 
             input == "arch" || input == "triangle" || input == "rectangle" || input == "cerc") {
      handleShapeCommand(input);
    }
    // Comenzi speciale de test și home
    else if (input == "test") {
      testKnownPositions();
    }
    else if (input == "home") {
      goHomeSafe();
    }
    // Verificare dacă inputul conține doar coordonate X Y (2 cuvinte)
    else if (wordCount == 2 && input.indexOf(' ') > 0) {
      handleCoordinateCommand(input);
    }
    else {
      Serial.println("Comandă necunoscută!");
      Serial.println("Folosiți:");
      Serial.println("- X Y OBIECT (pentru transport)");
      Serial.println("- X Y (pentru poziție simplă)");
      Serial.println("- nume formă (cube, cylinder, etc.)");
      Serial.println("- 'test' sau 'home'");
    }
  }
}

// Funcție pentru numărarea cuvintelor
int countWords(String str) {
  int count = 0;
  bool inWord = false;
  
  for (int i = 0; i < str.length(); i++) {
    if (str.charAt(i) != ' ') {
      if (!inWord) {
        count++;
        inWord = true;
      }
    } else {
      inWord = false;
    }
  }
  return count;
}

// Funcție pentru gestionarea comenzilor de transport
void handleTransportCommand(String input) {
  // Parsare X Y OBIECT
  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);
  
  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println("Format greșit! Folosiți: X Y OBIECT");
    return;
  }
  
  float pickup_x = input.substring(0, firstSpace).toFloat();
  float pickup_y = input.substring(firstSpace + 1, secondSpace).toFloat();
  String obiect = input.substring(secondSpace + 1);
  obiect.trim();
  
  // Verificăm dacă obiectul este valid
  if (!isValidObject(obiect)) {
    Serial.println("Obiect necunoscut! Folosiți: cube, cylinder, halfcircle, arch, triangle, rectangle, cerc");
    return;
  }
  
  Serial.println("=== TRANSPORT OBIECT ===");
  Serial.print("Ridicare obiect de la: X=");
  Serial.print(pickup_x);
  Serial.print(", Y=");
  Serial.println(pickup_y);
  Serial.print("Transport către: ");
  Serial.println(obiect);
  
  // PASUL 1: Mergem la poziția de ridicare cu gripper deschis
  ServoPosition pickup_pos = calculateInterpolatedPosition(pickup_x, pickup_y);
  pickup_pos.m6_gripper = 10; // Gripper deschis la început
  
  Serial.println("Pasul 1: Merg la poziția de ridicare cu gripper deschis...");
  moveToPositionThroughTransition(pickup_pos);
  Serial.println("Pasul 2*: Închid gripperul...");
  pickup_pos.m6_gripper = 10; // Închidem gripperul

  Braccio.ServoMovement(delayBraccioMovement, 
                        pickup_pos.m1_base,
                        pickup_pos.m2_shoulder,
                        pickup_pos.m3_elbow,
                        pickup_pos.m4_wrist_vert,
                        pickup_pos.m5_wrist_rot,
                        pickup_pos.m6_gripper);
  // PASUL 2: Închidem gripperul pentru a ridica obiectul
  Serial.println("Pasul 2: Închid gripperul...");
  pickup_pos.m6_gripper = 50; // Închidem gripperul

  Braccio.ServoMovement(delayBraccioMovement, 
                        pickup_pos.m1_base,
                        pickup_pos.m2_shoulder,
                        pickup_pos.m3_elbow,
                        pickup_pos.m4_wrist_vert,
                        pickup_pos.m5_wrist_rot,
                        pickup_pos.m6_gripper);

  
  
  // PASUL 3: Ridicăm la poziția de trecere cu obiectul
  Serial.println("Pasul 3: Ridic la poziția de trecere...");
  ServoPosition trecere_cu_obiect = pos_trecere;
  trecere_cu_obiect.m1_base = pickup_pos.m1_base; // Păstrăm M1 pentru rotația corectă
  trecere_cu_obiect.m6_gripper = 50; // Păstrăm gripperul închis
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_cu_obiect.m1_base,
                        trecere_cu_obiect.m2_shoulder,
                        trecere_cu_obiect.m3_elbow,
                        trecere_cu_obiect.m4_wrist_vert,
                        trecere_cu_obiect.m5_wrist_rot,
                        trecere_cu_obiect.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 4: Rotim M1 către poziția țintă
  ServoPosition target_pos = getObjectPosition(obiect);
  ServoPosition trecere_rotit = pos_trecere;
  trecere_rotit.m1_base = target_pos.m1_base; // Rotim către țintă
  trecere_rotit.m6_gripper = 50; // Păstrăm gripperul închis
  
  Serial.println("Pasul 4: Rotesc către poziția țintă...");
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_rotit.m1_base,
                        trecere_rotit.m2_shoulder,
                        trecere_rotit.m3_elbow,
                        trecere_rotit.m4_wrist_vert,
                        trecere_rotit.m5_wrist_rot,
                        trecere_rotit.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 5: Coborâm la poziția țintă
  target_pos.m6_gripper = 50; // Păstrăm gripperul închis
  Serial.println("Pasul 5: Cobor la poziția țintă...");
  Braccio.ServoMovement(delayBraccioMovement, 
                        target_pos.m1_base,
                        target_pos.m2_shoulder,
                        target_pos.m3_elbow,
                        target_pos.m4_wrist_vert,
                        target_pos.m5_wrist_rot,
                        target_pos.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 6: Deschidem gripperul pentru a lăsa obiectul
  Serial.println("Pasul 6: Deschid gripperul...");
  target_pos.m6_gripper = 10; // Deschidem gripperul
  Braccio.ServoMovement(delayBraccioMovement, 
                        target_pos.m1_base,
                        target_pos.m2_shoulder,
                        target_pos.m3_elbow,
                        target_pos.m4_wrist_vert,
                        target_pos.m5_wrist_rot,
                        target_pos.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 7: Ridicăm la poziția de trecere și așteptăm
  Serial.println("Pasul 7: Ridic la poziția de trecere...");
  ServoPosition trecere_final = pos_trecere;
  trecere_final.m1_base = target_pos.m1_base; // Păstrăm rotația
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_final.m1_base,
                        trecere_final.m2_shoulder,
                        trecere_final.m3_elbow,
                        trecere_final.m4_wrist_vert,
                        trecere_final.m5_wrist_rot,
                        trecere_final.m6_gripper);
  
  Serial.println("=== TRANSPORT COMPLET! ===");
  Serial.println("Robot în poziția de așteptare (M2=100, M3=165)");
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru verificarea dacă obiectul este valid
bool isValidObject(String obj) {
  return (obj == "cube" || obj == "cylinder" || obj == "halfcircle" || 
          obj == "arch" || obj == "triangle" || obj == "rectangle" || obj == "cerc");
}

// Funcție pentru obținerea poziției unui obiect
ServoPosition getObjectPosition(String obj) {
  if (obj == "cube") return pos_cube;
  else if (obj == "cylinder") return pos_cylinder;
  else if (obj == "halfcircle") return pos_halfcircle;
  else if (obj == "arch") return pos_arch;
  else if (obj == "triangle") return pos_triangle;
  else if (obj == "rectangle") return pos_rectangle;
  else if (obj == "cerc") return pos_cerc;
  else return pos_cube; // default
}

// Funcție pentru gestionarea comenzilor de coordonate simple
void handleCoordinateCommand(String input) {
  int spaceIndex = input.indexOf(' ');
  float target_x = input.substring(0, spaceIndex).toFloat();
  float target_y = input.substring(spaceIndex + 1).toFloat();
  
  if (target_x != 0 || target_y != 0) {
    Serial.print("Coordonate țintă: X=");
    Serial.print(target_x);
    Serial.print(", Y=");
    Serial.println(target_y);
    
    ServoPosition target_pos = calculateInterpolatedPosition(target_x, target_y);
    
    Serial.println("Poziții servo calculate:");
    Serial.print("M1 (Base): "); Serial.println(target_pos.m1_base);
    Serial.print("M2 (Shoulder): "); Serial.println(target_pos.m2_shoulder);
    Serial.print("M3 (Elbow): "); Serial.println(target_pos.m3_elbow);
    Serial.print("M4 (Wrist Vert): "); Serial.println(target_pos.m4_wrist_vert);
    Serial.print("M5 (Wrist Rot): "); Serial.println(target_pos.m5_wrist_rot);
    Serial.print("M6 (Gripper): "); Serial.println(target_pos.m6_gripper);
    
    moveToPositionThroughTransition(target_pos);
    
    Serial.println("Mișcare completă!");
    Serial.println("Robot în poziția de așteptare (M2=100, M3=165)");
    Serial.println("Introduceti următoarea comandă:");
  }
}

ServoPosition calculateInterpolatedPosition(float x, float y) {
  ServoPosition result;
  
  float min_x = min(min(coord_stanga_jos.x, coord_dreapta_jos.x), 
                    min(coord_dreapta_sus.x, coord_stanga_sus.x));
  float max_x = max(max(coord_stanga_jos.x, coord_dreapta_jos.x), 
                    max(coord_dreapta_sus.x, coord_stanga_sus.x));
  
  float min_y = min(min(coord_stanga_jos.y, coord_dreapta_jos.y), 
                    min(coord_dreapta_sus.y, coord_stanga_sus.y));
  float max_y = max(max(coord_stanga_jos.y, coord_dreapta_jos.y), 
                    max(coord_dreapta_sus.y, coord_stanga_sus.y));
  
  float norm_x = (x - min_x) / (max_x - min_x);
  float norm_y = (y - min_y) / (max_y - min_y);
  
  norm_x = constrain(norm_x, 0.0, 1.0);
  norm_y = constrain(norm_y, 0.0, 1.0);
  
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
  float bottom_interp = bottom_left + (bottom_right - bottom_left) * x;
  float top_interp = top_left + (top_right - top_left) * x;
  float result = bottom_interp + (top_interp - bottom_interp) * y;
  
  return (int)round(result);
}

// Funcție pentru mișcare prin poziția de trecere (M2=100, M3=165)
void moveToPositionThroughTransition(ServoPosition pos) {
  // Mergem mai întâi la poziția de trecere cu M1 corect
  ServoPosition trecere_pos = pos_trecere;
  trecere_pos.m1_base = pos.m1_base; // Rotim M1 către țintă
  trecere_pos.m6_gripper = pos.m6_gripper; // Păstrăm starea gripperului
  
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_pos.m1_base,
                        trecere_pos.m2_shoulder,
                        trecere_pos.m3_elbow,
                        trecere_pos.m4_wrist_vert,
                        trecere_pos.m5_wrist_rot,
                        trecere_pos.m6_gripper);
  
  delay(delayModificabil);
  
  // Apoi mergem la poziția finală
  Braccio.ServoMovement(delayBraccioMovement, 
                        pos.m1_base,
                        pos.m2_shoulder,
                        pos.m3_elbow,
                        pos.m4_wrist_vert,
                        pos.m5_wrist_rot,
                        pos.m6_gripper);
  
  // delay(delayModificabil);
  
  // La final, ridicăm din nou la poziția de trecere pentru așteptare
  // Braccio.ServoMovement(delayBraccioMovement, 
  //                       trecere_pos.m1_base,
  //                       trecere_pos.m2_shoulder,
  //                       trecere_pos.m3_elbow,
  //                       trecere_pos.m4_wrist_vert,
  //                       trecere_pos.m5_wrist_rot,
  //                       trecere_pos.m6_gripper);
}

// Funcție pentru mișcare rapidă prin poziția de trecere optimizată
void moveToPositionFast(ServoPosition pos) {
  // Mergem mai întâi la poziția de trecere optimizată
  ServoPosition trecere_pos = pos_trecere;
  trecere_pos.m6_gripper = pos.m6_gripper; // Păstrăm starea gripperului
  
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_pos.m1_base,
                        trecere_pos.m2_shoulder,
                        trecere_pos.m3_elbow,
                        trecere_pos.m4_wrist_vert,
                        trecere_pos.m5_wrist_rot,
                        trecere_pos.m6_gripper);
  
  delay(delayModificabil); // Delay configurabil pentru trecere rapidă
  
  // Apoi mergem la poziția finală
  Braccio.ServoMovement(delayBraccioMovement, 
                        pos.m1_base,
                        pos.m2_shoulder,
                        pos.m3_elbow,
                        pos.m4_wrist_vert,
                        pos.m5_wrist_rot,
                        pos.m6_gripper);
}

// Funcție pentru mișcare simplă (fără trecere intermediară)
void moveToPosition(ServoPosition pos) {
  Braccio.ServoMovement(delayBraccioMovement, 
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
  
  ServoPosition target_pos = getObjectPosition(command);
  moveToPositionThroughTransition(target_pos);
  
  Serial.print("Poziția pentru ");
  String upperCommand = command;
  upperCommand.toUpperCase(); // Fix pentru eroarea de compilare
  Serial.print(upperCommand);
  Serial.println(" - executată!");
  Serial.println("Robot în poziția de așteptare (M2=100, M3=165)");
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru poziția home cu secvență de siguranță
void goHomeSafe() {
  Serial.println("Secvența HOME - Pasul 1: Cupla 1 la 0 grade...");
  Braccio.ServoMovement(delayBraccioMovement, 0, 90, 90, 90, 90, 10);
  delay(delayModificabil * 2); // Delay mai lung pentru siguranță la home
  
  Serial.println("Secvența HOME - Pasul 2: Poziția HOME finală...");
  Braccio.ServoMovement(delayBraccioMovement, 90, 90, 90, 90, 90, 10);
  
  Serial.println("Poziția HOME - executată cu succes!");
  Serial.println("Introduceti următoarea comandă:");
}

// Funcție pentru testare rapidă cu poziții cunoscute
void testKnownPositions() {
  Serial.println("Test poziții cunoscute:");
  
  Serial.println("Mergem la stânga jos...");
  moveToPositionThroughTransition(pos_stanga_jos);
  delay(delayModificabil * 2);
  
  Serial.println("Mergem la dreapta jos...");
  moveToPositionThroughTransition(pos_dreapta_jos);
  delay(delayModificabil * 2);
  
  Serial.println("Mergem la dreapta sus...");
  moveToPositionThroughTransition(pos_dreapta_sus);
  delay(delayModificabil * 2);
  
  Serial.println("Mergem la stânga sus...");
  moveToPositionThroughTransition(pos_stanga_sus);
  delay(delayModificabil * 2);
  
  Serial.println("Test complet!");
  Serial.println("Robot în poziția de așteptare (M2=100, M3=165)");
}