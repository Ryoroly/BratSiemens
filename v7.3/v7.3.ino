//trimite 1 daca face ceva si 0 daca asteapta sa primeasca comanda
//se conecteaza la bluethoot si primeste date si le executa pentru o forma 


// COMENZILE DE LA RASBERY PY
//"T 100 200 1"
//"S 1300 500"

// Transport manual  
//100 100 1


#include <ArduinoBLE.h>
#include <Braccio.h>
#include <Servo.h>

// ===== VARIABILE DE AJUSTARE PENTRU APUCARE OPTIMIZATA =====
// Aceste valori se adauga la pozitiile M2 si M3 pentru o apucare mai buna
int m2_offset_pickup = 10;      // Offset pentru M2 (shoulder) la pickup - valori negative coboara bratul
int m3_offset_pickup = 10;      // Offset pentru M3 (elbow) la pickup - valori negative apropie cotul
int m2_offset_corners = 0;     // Offset pentru M2 in pozitiile din colturile dreptunghiului
int m3_offset_corners = 0;     // Offset pentru M3 in pozitiile din colturile dreptunghiului

// ===== OFFSET PENTRU AXA Y =====
int y_offset = 100;            // Valoarea care se adauga la Y pentru a coborî brațul
// Dacă primești Y=300, brațul va merge la Y=300+100=400 în calcule
// Pentru a merge mai sus, folosește valori negative (ex: -50)

// ===== POZITII FIXE PENTRU M5 =====
int m5_pickup_position = 30;   // M5 la pickup - pozitia fixa pentru apucare
int m5_transport_position = 130; // M5 in transport - pozitia fixa pentru transport
// ============================================================

// Definim un "Serviciu" si o "Caracteristica" unice pentru comunicarea noastra.
BLEService dataService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic dataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite, 20);

// Variabile pentru controlul delay-urilor
int delayModificabil = 10;
int delayBraccioMovement = 20;

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
ServoPosition pos_trecere = {90, 100, 165, 90, 110, 10};

// Poziții pentru obiecte predefinite (ID-uri 1-6)
ServoPosition pos_objects[7] = {
  {0, 0, 0, 0, 0, 0},              // Index 0 - nefolosit
  {180, 120, 130, 160, 60, 10},    // ID 1 - cube
  {160, 130, 120, 160, 60, 10},    // ID 2 - cylinder
  {140, 140, 120, 140, 60, 10},    // ID 3 - halfcircle
  {0, 130, 130, 160, 60, 10},      // ID 4 - arch
  {20, 140, 120, 140, 60, 10},     // ID 5 - triangle
  {40, 150, 100, 140, 60, 10}      // ID 6 - rectangle
};

struct Point2D {
  float x;
  float y;
};

// Variabile pentru coordonatele dreptunghiului - vor fi actualizate din BLE
int xul = 1290;
int yul = 572;
Point2D coord_stanga_jos = {0, 0};
Point2D coord_dreapta_jos = {xul, 0};
Point2D coord_dreapta_sus = {xul, yul}; 
Point2D coord_stanga_sus = {0, yul};

// Variabile pentru starea robotului
bool robotBusy = false;
String currentCommand = "";

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // Initializam modulul BLE
  if (!BLE.begin()) {
    Serial.println("Eroare la pornirea BLE!");
    while (1);
  }

  // Setam numele cu care va aparea Arduino la scanare
  BLE.setLocalName("BraccioRobot_BLE");
  
  // Setam serviciul pe care il va "advertisa"
  BLE.setAdvertisedService(dataService);
  
  // Adaugam caracteristica la serviciu
  dataService.addCharacteristic(dataCharacteristic);
  
  // Adaugam serviciul la BLE
  BLE.addService(dataService);
  
  // Incepem sa advertizam
  BLE.advertise();
  
  Serial.println("Arduino UNO R4 WiFi gata de conexiune BLE.");
  
  // Initializam robotul Braccio
  Braccio.begin();
  
  Serial.println("=== BRACCIO ROBOT CU CONTROL BLE SI SERIAL ===");
  Serial.print("Offset Y activ: "); Serial.println(y_offset);
  Serial.println("(Pentru Y mai jos folosește valori pozitive, pentru Y mai sus folosește valori negative)");
  Serial.println("Astept conexiune de la Raspberry Pi...");
  Serial.println("COMENZI ACCEPTATE:");
  Serial.println("BLE/Serial: S xul yul - Seteaza dimensiunile zonei");
  Serial.println("BLE/Serial: T x y id - Transporta obiectul (id: 1-6)");
  Serial.println("Serial SIMPLIFICAT: x y id - Transport direct (fara T)");
  Serial.println("   ID obiecte: 1=cube, 2=cylinder, 3=halfcircle");
  Serial.println("                4=arch, 5=triangle, 6=rectangle");
  Serial.println("===============================================");
}

void loop() {
  // Verificam comenzile de la Serial Monitor
  checkSerialCommands();
  
  // Asteptam ca Raspberry Pi sa se conecteze
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("*** CONECTAT la dispozitivul: ");
    Serial.println(central.address());
    Serial.println("*** Gata sa primesc comenzi!");

    // Ramanem conectati cat timp dispozitivul este in raza
    while (central.connected()) {
      // Verificam comenzile Serial chiar si cand suntem conectati la BLE
      checkSerialCommands();
      
      // Verificam daca s-au primit date noi prin BLE
      if (dataCharacteristic.written() && !robotBusy) {
        String receivedData = "";
        
        // Citim datele primite
        for (int i = 0; i < dataCharacteristic.valueLength(); i++) {
          receivedData += (char)dataCharacteristic.value()[i];
        }
        
        Serial.print(">>> MESAJ PRIMIT (BLE): ");
        Serial.println(receivedData);
        
        // Procesam comanda primita
        processCommand(receivedData);
      }
      
      // Mic delay pentru a nu suprasolicita procesorul
      delay(10);
    }

    Serial.print("*** DECONECTAT de la: ");
    Serial.println(central.address());
    robotBusy = false; // Reset stare la deconectare
  }
}

void checkSerialCommands() {
  if (Serial.available() && !robotBusy) {
    String serialCommand = Serial.readStringUntil('\n');
    serialCommand.trim();
    
    if (serialCommand.length() > 0) {
      Serial.print(">>> COMANDA SERIAL: ");
      Serial.println(serialCommand);
      
      // Verificam daca este comanda simplificata (doar x y id)
      if (!serialCommand.startsWith("S") && !serialCommand.startsWith("T")) {
        handleSimplifiedCommand(serialCommand);
      } else {
        // Procesam ca o comanda normala
        processCommand(serialCommand);
      }
    }
  }
}

void handleSimplifiedCommand(String command) {
  Serial.println(">>> COMANDA SIMPLIFICATA DETECTATA");
  
  // Parsare: x y id
  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  
  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println(">>> EROARE: Format gresit! Folositi: x y id");
    return;
  }
  
  float pickup_x = command.substring(0, firstSpace).toFloat();
  float pickup_y = command.substring(firstSpace + 1, secondSpace).toFloat();
  int obiect_id = command.substring(secondSpace + 1).toInt();
  
  Serial.println(">>> EXECUTEZ COMANDA SIMPLIFICATA:");
  Serial.print(">>> X="); Serial.print(pickup_x);
  Serial.print(", Y="); Serial.print(pickup_y);
  Serial.print(", ID="); Serial.println(obiect_id);
  
  // Cream comanda T si o procesam
  String transportCommand = "T " + String(pickup_x) + " " + String(pickup_y) + " " + String(obiect_id);
  processCommand(transportCommand);
}

void processCommand(String command) {
  command.trim();
  Serial.print(">>> PROCESEZ COMANDA: ");
  Serial.println(command);
  
  if (command.startsWith("S")) {
    handleSetAreaCommand(command);
  }
  else if (command.startsWith("T")) {
    handleTransportCommand(command);
  }
  else {
    Serial.println(">>> COMANDA NECUNOSCUTA!");
    Serial.println(">>> Folositi: S xul yul sau T x y id sau x y id");
  }
}

void handleSetAreaCommand(String command) {
  Serial.println(">>> SETEZ ZONA DE LUCRU...");
  
  // Parsare: S xul yul
  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  
  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println(">>> EROARE: Format gresit! Folositi: S xul yul");
    return;
  }
  
  int new_xul = command.substring(firstSpace + 1, secondSpace).toInt();
  int new_yul = command.substring(secondSpace + 1).toInt();
  
  // Actualizam coordonatele
  xul = new_xul;
  yul = new_yul;
  coord_dreapta_jos = {xul, 0};
  coord_dreapta_sus = {xul, yul};
  coord_stanga_sus = {0, yul};
  
  Serial.print(">>> ZONA SETATA: XUL=");
  Serial.print(xul);
  Serial.print(", YUL=");
  Serial.println(yul);
  Serial.println(">>> GATA SA PRIMESC COMENZI DE TRANSPORT!");
}

void handleTransportCommand(String command) {
  robotBusy = true; // Marcam robotul ca ocupat
  currentCommand = command;
  
  Serial.println(">>> INCEP TRANSPORT OBIECT...");
  
  // Parsare: T x y id
  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  int thirdSpace = command.indexOf(' ', secondSpace + 1);
  
  if (firstSpace == -1 || secondSpace == -1 || thirdSpace == -1) {
    Serial.println(">>> EROARE: Format gresit! Folositi: T x y id");
    robotBusy = false;
    return;
  }
  
  float pickup_x = command.substring(firstSpace + 1, secondSpace).toFloat();
  float pickup_y = command.substring(secondSpace + 1, thirdSpace).toFloat();
  int obiect_id = command.substring(thirdSpace + 1).toInt();
  
  // APLICAM OFFSET-ul PENTRU Y
  float adjusted_pickup_y = pickup_y + y_offset;
  
  // Verificăm dacă ID-ul obiectului este valid
  if (obiect_id < 1 || obiect_id > 6) {
    Serial.println(">>> EROARE: ID obiect invalid!");
    Serial.println(">>> ID-uri valide: 1-6 (1=cube, 2=cylinder, 3=halfcircle, 4=arch, 5=triangle, 6=rectangle)");
    robotBusy = false;
    return;
  }
  
  Serial.println(">>> === EXECUTEZ TRANSPORT ===");
  Serial.print(">>> Coordonate primite: X=");
  Serial.print(pickup_x);
  Serial.print(", Y=");
  Serial.println(pickup_y);
  Serial.print(">>> Coordonate ajustate: X=");
  Serial.print(pickup_x);
  Serial.print(", Y=");
  Serial.print(adjusted_pickup_y);
  Serial.print(" (Y offset: ");
  Serial.print(y_offset);
  Serial.println(")");
  Serial.print(">>> Transport catre obiect ID: ");
  Serial.println(obiect_id);
  Serial.println(">>> Folosesc pozitii fixe pentru M5:");
  Serial.print(">>> M5 la pickup: "); Serial.println(m5_pickup_position);
  Serial.print(">>> M5 in transport: "); Serial.println(m5_transport_position);
  
  // Executam secventa de transport cu Y ajustat
  executeTransportSequence(pickup_x, adjusted_pickup_y, obiect_id);
  
  Serial.println(">>> === TRANSPORT COMPLET! ===");
  Serial.println(">>> Robot gata pentru urmatoarea comanda!");
  robotBusy = false; // Marcam robotul ca liber
}

void executeTransportSequence(float pickup_x, float pickup_y, int obiect_id) {
  // PASUL 1: Mergem la poziția de ridicare cu gripper deschis și M5 FIXAT LA 30
  ServoPosition pickup_pos = calculateInterpolatedPosition(pickup_x, pickup_y);
  pickup_pos.m6_gripper = 10; // Gripper deschis
  
  // Aplicam offseturile pentru apucare mai buna
  pickup_pos.m2_shoulder = constrain(pickup_pos.m2_shoulder + m2_offset_pickup, 15, 165);
  pickup_pos.m3_elbow = constrain(pickup_pos.m3_elbow + m3_offset_pickup, 0, 180);
  
  // IMPORTANT: Setam M5 la pozitia FIXA de pickup (30 grade)!
  pickup_pos.m5_wrist_rot = m5_pickup_position;
  
  Serial.println(">>> Pas 1: Merg la pozitia de ridicare cu M5 FIXAT la 30 grade...");
  Serial.print(">>> Pozitie ajustata: M2="); Serial.print(pickup_pos.m2_shoulder);
  Serial.print(", M3="); Serial.print(pickup_pos.m3_elbow);
  Serial.print(", M5="); Serial.print(pickup_pos.m5_wrist_rot);
  Serial.println(" (M5 FIXAT la pozitia de pickup!)");
  
  moveToPositionThroughTransitionWithFixedM5(pickup_pos);
  
  // PASUL 2: Închidem gripperul pentru a ridica obiectul
  Serial.println(">>> Pas 2: Inchid gripperul...");
  pickup_pos.m6_gripper = 50; // Închidem gripperul
  Braccio.ServoMovement(delayBraccioMovement, 
                        pickup_pos.m1_base,
                        pickup_pos.m2_shoulder,
                        pickup_pos.m3_elbow,
                        pickup_pos.m4_wrist_vert,
                        pickup_pos.m5_wrist_rot,
                        pickup_pos.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 3: Ridicăm la poziția de trecere cu obiectul și M5 la 130
  Serial.println(">>> Pas 3: Ridic la pozitia de trecere si rotesc M5 la 130...");
  ServoPosition trecere_cu_obiect = pos_trecere;
  trecere_cu_obiect.m1_base = pickup_pos.m1_base;
  trecere_cu_obiect.m6_gripper = 50;
  trecere_cu_obiect.m5_wrist_rot = m5_transport_position; // M5 la pozitia de transport (130)
  
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_cu_obiect.m1_base,
                        trecere_cu_obiect.m2_shoulder,
                        trecere_cu_obiect.m3_elbow,
                        trecere_cu_obiect.m4_wrist_vert,
                        trecere_cu_obiect.m5_wrist_rot,
                        trecere_cu_obiect.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 4: Rotim M1 către poziția țintă (M5 rămâne la 130!)
  ServoPosition target_pos = pos_objects[obiect_id];
  ServoPosition trecere_rotit = pos_trecere;
  trecere_rotit.m1_base = target_pos.m1_base;
  trecere_rotit.m6_gripper = 50;
  trecere_rotit.m5_wrist_rot = m5_transport_position; // M5 rămâne la poziția de transport
  
  Serial.println(">>> Pas 4: Rotesc M1 catre pozitia tinta (M5 ramane la 130!)...");
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_rotit.m1_base,
                        trecere_rotit.m2_shoulder,
                        trecere_rotit.m3_elbow,
                        trecere_rotit.m4_wrist_vert,
                        trecere_rotit.m5_wrist_rot,
                        trecere_rotit.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 5: Coborâm la poziția țintă (M5 rămâne la 130)
  target_pos.m6_gripper = 50;
  target_pos.m5_wrist_rot = m5_transport_position; // M5 rămâne la poziția de transport
  Serial.println(">>> Pas 5: Cobor la pozitia tinta cu M5 la 130...");
  Braccio.ServoMovement(delayBraccioMovement, 
                        target_pos.m1_base,
                        target_pos.m2_shoulder,
                        target_pos.m3_elbow,
                        target_pos.m4_wrist_vert,
                        target_pos.m5_wrist_rot,
                        target_pos.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 6: Deschidem gripperul pentru a lăsa obiectul
  Serial.println(">>> Pas 6: Deschid gripperul...");
  target_pos.m6_gripper = 10;
  Braccio.ServoMovement(delayBraccioMovement, 
                        target_pos.m1_base,
                        target_pos.m2_shoulder,
                        target_pos.m3_elbow,
                        target_pos.m4_wrist_vert,
                        target_pos.m5_wrist_rot,
                        target_pos.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 7: Ridicăm la poziția de trecere
  Serial.println(">>> Pas 7: Ridic la pozitia de trecere...");
  ServoPosition trecere_final = pos_trecere;
  trecere_final.m1_base = target_pos.m1_base;
  trecere_final.m5_wrist_rot = m5_transport_position; // Păstrăm M5 la 130
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_final.m1_base,
                        trecere_final.m2_shoulder,  
                        trecere_final.m3_elbow,
                        trecere_final.m4_wrist_vert,
                        trecere_final.m5_wrist_rot,
                        trecere_final.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 8: Resetăm progresiv M5 pentru următoarea comandă
  Serial.println(">>> Pas 8: Resetez progresiv M5 pentru urmatoarea comanda...");
  smoothRotateM5(trecere_final, pos_trecere.m5_wrist_rot, 3); // Înapoi la poziția standard
}

// Funcție nouă pentru rotirea progresivă a M5
void smoothRotateM5(ServoPosition base_pos, int target_m5, int steps) {
  int current_m5 = base_pos.m5_wrist_rot;
  int step_size = (target_m5 - current_m5) / steps;
  
  Serial.print(">>> Rotesc M5 de la "); Serial.print(current_m5);
  Serial.print(" la "); Serial.print(target_m5);
  Serial.print(" in "); Serial.print(steps); Serial.println(" pasi");
  
  for (int i = 1; i <= steps; i++) {
    int intermediate_m5;
    if (i == steps) {
      intermediate_m5 = target_m5; // Ultimul pas - pozitia exacta
    } else {
      intermediate_m5 = current_m5 + (step_size * i);
    }
    
    Serial.print(">>> Pas M5 "); Serial.print(i);
    Serial.print("/"); Serial.print(steps);
    Serial.print(": M5="); Serial.println(intermediate_m5);
    
    Braccio.ServoMovement(delayBraccioMovement,
                          base_pos.m1_base,
                          base_pos.m2_shoulder,
                          base_pos.m3_elbow,
                          base_pos.m4_wrist_vert,
                          intermediate_m5,
                          base_pos.m6_gripper);
    delay(delayModificabil);
  }
  
  // Actualizăm poziția de bază cu noua valoare M5
  base_pos.m5_wrist_rot = target_m5;
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
  
  // Aplicam offseturile pentru pozitiile din colturi
  int base_m2 = interpolateBilinear(
    pos_stanga_jos.m2_shoulder, pos_dreapta_jos.m2_shoulder,
    pos_stanga_sus.m2_shoulder, pos_dreapta_sus.m2_shoulder,
    norm_x, norm_y
  );
  result.m2_shoulder = constrain(base_m2 + m2_offset_corners, 15, 165);
  
  int base_m3 = interpolateBilinear(
    pos_stanga_jos.m3_elbow, pos_dreapta_jos.m3_elbow,
    pos_stanga_sus.m3_elbow, pos_dreapta_sus.m3_elbow,
    norm_x, norm_y
  );
  result.m3_elbow = constrain(base_m3 + m3_offset_corners, 0, 180);
  
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

void moveToPositionThroughTransitionWithFixedM5(ServoPosition pos) {
  // Mergem mai întâi la poziția de trecere cu M1 corect și M5 la poziția standard
  ServoPosition trecere_pos = pos_trecere;
  trecere_pos.m1_base = pos.m1_base;
  trecere_pos.m6_gripper = pos.m6_gripper;
  // M5 rămâne la poziția standard din pos_trecere
  
  Serial.println(">>> Merg la pozitia de trecere cu M5 standard...");
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_pos.m1_base,
                        trecere_pos.m2_shoulder,
                        trecere_pos.m3_elbow,
                        trecere_pos.m4_wrist_vert,
                        trecere_pos.m5_wrist_rot,
                        trecere_pos.m6_gripper);
  delay(delayModificabil);
  
  // Acum rotim progresiv M5 la poziția de pickup (30)
  Serial.println(">>> Rotesc progresiv M5 pe drum catre pickup la 30 grade...");
  smoothRotateM5(trecere_pos, m5_pickup_position, 3); // Rotim M5 la 30
  
  // În final, mergem la poziția de pickup cu M5 la 30
  Serial.println(">>> Ajung la pozitia de pickup cu M5 la 30 grade...");
  pos.m5_wrist_rot = m5_pickup_position; // Asigurăm că M5 este la 30
  Braccio.ServoMovement(delayBraccioMovement, 
                        pos.m1_base,
                        pos.m2_shoulder,
                        pos.m3_elbow,
                        pos.m4_wrist_vert,
                        pos.m5_wrist_rot,
                        pos.m6_gripper);
}