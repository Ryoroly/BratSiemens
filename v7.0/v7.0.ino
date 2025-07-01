//trimite 1 daca face ceva si 0 daca asteapta sa primeasca comanda
//se conecteaza la bluethoot si primeste date si le executa pentru o forma 
// Setează zona de lucru
//"S 1290 572"

// Transportă la cube
//"T 100 200 1"

// Transportă la triangle  
//"T 500 300 5"


#include <ArduinoBLE.h>
#include <Braccio.h>
#include <Servo.h>

// =======================================================================
// VARIABILE DE CONFIGURARE PENTRU AJUSTAREA POZIȚIILOR M2 și M3
// =======================================================================
// Offset-uri pentru M2 (shoulder) - valori negative coboară brațul, pozitive îl ridică
const int M2_OFFSET_PICKUP = -10;     // Offset pentru M2 când ridică obiectul
const int M2_OFFSET_DROPOFF = 0;      // Offset pentru M2 când lasă obiectul

// Offset-uri pentru M3 (elbow) - valori negative extind brațul, pozitive îl retrag
const int M3_OFFSET_PICKUP = -15;     // Offset pentru M3 când ridică obiectul
const int M3_OFFSET_DROPOFF = 0;      // Offset pentru M3 când lasă obiectul

// Limitele de siguranță pentru servomotoare (previne poziții invalide)
const int M2_MIN_LIMIT = 15;          // Poziția minimă pentru M2
const int M2_MAX_LIMIT = 165;         // Poziția maximă pentru M2
const int M3_MIN_LIMIT = 0;           // Poziția minimă pentru M3
const int M3_MAX_LIMIT = 180;         // Poziția maximă pentru M3
// =======================================================================

// Definim un "Serviciu" si o "Caracteristica" unice pentru comunicarea noastra.
BLEService dataService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic dataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite, 20);

// Variabile pentru controlul delay-urilor
int delayModificabil = 10;
int delayBraccioMovement = 10;

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

// Funcție pentru aplicarea offset-urilor și limitelor de siguranță
ServoPosition applyOffsetsAndLimits(ServoPosition pos, bool isPickup) {
  ServoPosition result = pos;
  
  if (isPickup) {
    result.m2_shoulder += M2_OFFSET_PICKUP;
    result.m3_elbow += M3_OFFSET_PICKUP;
  } else {
    result.m2_shoulder += M2_OFFSET_DROPOFF;
    result.m3_elbow += M3_OFFSET_DROPOFF;
  }
  
  // Aplicăm limitele de siguranță
  result.m2_shoulder = constrain(result.m2_shoulder, M2_MIN_LIMIT, M2_MAX_LIMIT);
  result.m3_elbow = constrain(result.m3_elbow, M3_MIN_LIMIT, M3_MAX_LIMIT);
  
  return result;
}

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
  
  Serial.println("=== BRACCIO ROBOT CU CONTROL BLE ===");
  Serial.println("Configurare curenta:");
  Serial.print("M2 Offset Pickup: ");
  Serial.println(M2_OFFSET_PICKUP);
  Serial.print("M2 Offset Dropoff: ");
  Serial.println(M2_OFFSET_DROPOFF);
  Serial.print("M3 Offset Pickup: ");
  Serial.println(M3_OFFSET_PICKUP);
  Serial.print("M3 Offset Dropoff: ");
  Serial.println(M3_OFFSET_DROPOFF);
  Serial.println("Astept conexiune de la Raspberry Pi...");
  Serial.println("Comenzi acceptate (format scurt):");
  Serial.println("1. S xul yul - Seteaza dimensiunile zonei");
  Serial.println("2. T x y id - Transporta obiectul (id: 1-6)");
  Serial.println("   ID obiecte: 1=cube, 2=cylinder, 3=halfcircle");
  Serial.println("                4=arch, 5=triangle, 6=rectangle");
  Serial.println("=====================================");
}

void loop() {
  // Asteptam ca Raspberry Pi sa se conecteze
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("*** CONECTAT la dispozitivul: ");
    Serial.println(central.address());
    Serial.println("*** Gata sa primesc comenzi!");

    // Ramanem conectati cat timp dispozitivul este in raza
    while (central.connected()) {
      // Verificam daca s-au primit date noi
      if (dataCharacteristic.written() && !robotBusy) {
        String receivedData = "";
        
        // Citim datele primite
        for (int i = 0; i < dataCharacteristic.valueLength(); i++) {
          receivedData += (char)dataCharacteristic.value()[i];
        }
        
        Serial.print(">>> MESAJ PRIMIT: ");
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
    Serial.println(">>> Folositi: S xul yul sau T x y id");
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
  
  // Verificăm dacă ID-ul obiectului este valid
  if (obiect_id < 1 || obiect_id > 6) {
    Serial.println(">>> EROARE: ID obiect invalid!");
    Serial.println(">>> ID-uri valide: 1-6 (1=cube, 2=cylinder, 3=halfcircle, 4=arch, 5=triangle, 6=rectangle)");
    robotBusy = false;
    return;
  }
  
  Serial.println(">>> === EXECUTEZ TRANSPORT ===");
  Serial.print(">>> Ridic obiect de la: X=");
  Serial.print(pickup_x);
  Serial.print(", Y=");
  Serial.println(pickup_y);
  Serial.print(">>> Transport catre obiect ID: ");
  Serial.println(obiect_id);
  
  // Executam secventa de transport
  executeTransportSequence(pickup_x, pickup_y, obiect_id);
  
  Serial.println(">>> === TRANSPORT COMPLET! ===");
  Serial.println(">>> Robot gata pentru urmatoarea comanda!");
  robotBusy = false; // Marcam robotul ca liber
}

void executeTransportSequence(float pickup_x, float pickup_y, int obiect_id) {
  // PASUL 1: Mergem la poziția de ridicare cu gripper deschis
  ServoPosition pickup_pos = calculateInterpolatedPosition(pickup_x, pickup_y);
  pickup_pos.m6_gripper = 10; // Gripper deschis
  
  // Aplicăm offset-urile pentru pickup
  pickup_pos = applyOffsetsAndLimits(pickup_pos, true);
  
  Serial.println(">>> Pas 1: Merg la pozitia de ridicare...");
  Serial.print(">>> Pozitii ajustate: M2=");
  Serial.print(pickup_pos.m2_shoulder);
  Serial.print(", M3=");
  Serial.println(pickup_pos.m3_elbow);
  
  moveToPositionThroughTransition(pickup_pos);
  
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
  
  // PASUL 3: Ridicăm la poziția de trecere cu obiectul
  Serial.println(">>> Pas 3: Ridic la pozitia de trecere...");
  ServoPosition trecere_cu_obiect = pos_trecere;
  trecere_cu_obiect.m1_base = pickup_pos.m1_base;
  trecere_cu_obiect.m6_gripper = 50;
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_cu_obiect.m1_base,
                        trecere_cu_obiect.m2_shoulder,
                        trecere_cu_obiect.m3_elbow,
                        trecere_cu_obiect.m4_wrist_vert,
                        trecere_cu_obiect.m5_wrist_rot,
                        trecere_cu_obiect.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 4: Rotim M1 către poziția țintă
  ServoPosition target_pos = pos_objects[obiect_id];
  ServoPosition trecere_rotit = pos_trecere;
  trecere_rotit.m1_base = target_pos.m1_base;
  trecere_rotit.m6_gripper = 50;
  
  Serial.println(">>> Pas 4: Rotesc catre pozitia tinta...");
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_rotit.m1_base,
                        trecere_rotit.m2_shoulder,
                        trecere_rotit.m3_elbow,
                        trecere_rotit.m4_wrist_vert,
                        trecere_rotit.m5_wrist_rot,
                        trecere_rotit.m6_gripper);
  delay(delayModificabil);
  
  // PASUL 5: Coborâm la poziția țintă
  target_pos.m6_gripper = 50;
  
  // Aplicăm offset-urile pentru dropoff
  target_pos = applyOffsetsAndLimits(target_pos, false);
  
  Serial.println(">>> Pas 5: Cobor la pozitia tinta...");
  Serial.print(">>> Pozitii ajustate pentru dropoff: M2=");
  Serial.print(target_pos.m2_shoulder);
  Serial.print(", M3=");
  Serial.println(target_pos.m3_elbow);
  
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
  
  // PASUL 7: Ridicăm la poziția de trecere și așteptăm
  Serial.println(">>> Pas 7: Ridic la pozitia de asteptare...");
  ServoPosition trecere_final = pos_trecere;
  trecere_final.m1_base = target_pos.m1_base;
  Braccio.ServoMovement(delayBraccioMovement, 
                        trecere_final.m1_base,
                        trecere_final.m2_shoulder,
                        trecere_final.m3_elbow,
                        trecere_final.m4_wrist_vert,
                        trecere_final.m5_wrist_rot,
                        trecere_final.m6_gripper);
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

void moveToPositionThroughTransition(ServoPosition pos) {
  // Mergem mai întâi la poziția de trecere cu M1 corect
  ServoPosition trecere_pos = pos_trecere;
  trecere_pos.m1_base = pos.m1_base;
  trecere_pos.m6_gripper = pos.m6_gripper;
  
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
}