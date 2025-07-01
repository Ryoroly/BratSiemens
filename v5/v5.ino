//am adugat si bluethoot 
#include <ArduinoBLE.h>
#include <Braccio.h>
#include <Servo.h>

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

// Poziții pentru obiecte predefinite
ServoPosition pos_cube = {180, 120, 130, 160, 60, 10};
ServoPosition pos_cylinder = {160, 130, 120, 160, 60, 10};
ServoPosition pos_halfcircle = {140, 140, 120, 140, 60, 10};
ServoPosition pos_arch = {0, 130, 130, 160, 60, 10};
ServoPosition pos_triangle = {20, 140, 120, 140, 60, 10};
ServoPosition pos_rectangle = {40, 150, 100, 140, 60, 10};
ServoPosition pos_cerc = {100, 140, 110, 150, 60, 10};

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
  
  Serial.println("=== BRACCIO ROBOT CU CONTROL BLE ===");
  Serial.println("Astept conexiune de la Raspberry Pi...");
  Serial.println("Comenzi acceptate:");
  Serial.println("1. SET_AREA xul yul - Seteaza dimensiunile zonei");
  Serial.println("2. TRANSPORT x y obiect - Transporta obiectul");
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
  
  if (command.startsWith("SET_AREA")) {
    handleSetAreaCommand(command);
  }
  else if (command.startsWith("TRANSPORT")) {
    handleTransportCommand(command);
  }
  else {
    Serial.println(">>> COMANDA NECUNOSCUTA!");
    Serial.println(">>> Folositi: SET_AREA xul yul sau TRANSPORT x y obiect");
  }
}

void handleSetAreaCommand(String command) {
  Serial.println(">>> SETEZ ZONA DE LUCRU...");
  
  // Parsare: SET_AREA xul yul
  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  
  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println(">>> EROARE: Format gresit! Folositi: SET_AREA xul yul");
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
  
  // Parsare: TRANSPORT x y obiect
  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  int thirdSpace = command.indexOf(' ', secondSpace + 1);
  
  if (firstSpace == -1 || secondSpace == -1 || thirdSpace == -1) {
    Serial.println(">>> EROARE: Format gresit! Folositi: TRANSPORT x y obiect");
    robotBusy = false;
    return;
  }
  
  float pickup_x = command.substring(firstSpace + 1, secondSpace).toFloat();
  float pickup_y = command.substring(secondSpace + 1, thirdSpace).toFloat();
  String obiect = command.substring(thirdSpace + 1);
  obiect.trim();
  
  // Verificăm dacă obiectul este valid
  if (!isValidObject(obiect)) {
    Serial.println(">>> EROARE: Obiect necunoscut!");
    Serial.println(">>> Obiecte disponibile: cube, cylinder, halfcircle, arch, triangle, rectangle, cerc");
    robotBusy = false;
    return;
  }
  
  Serial.println(">>> === EXECUTEZ TRANSPORT ===");
  Serial.print(">>> Ridic obiect de la: X=");
  Serial.print(pickup_x);
  Serial.print(", Y=");
  Serial.println(pickup_y);
  Serial.print(">>> Transport catre: ");
  Serial.println(obiect);
  
  // Executam secventa de transport
  executeTransportSequence(pickup_x, pickup_y, obiect);
  
  Serial.println(">>> === TRANSPORT COMPLET! ===");
  Serial.println(">>> Robot gata pentru urmatoarea comanda!");
  robotBusy = false; // Marcam robotul ca liber
}

void executeTransportSequence(float pickup_x, float pickup_y, String obiect) {
  // PASUL 1: Mergem la poziția de ridicare cu gripper deschis
  ServoPosition pickup_pos = calculateInterpolatedPosition(pickup_x, pickup_y);
  pickup_pos.m6_gripper = 10; // Gripper deschis
  
  Serial.println(">>> Pas 1: Merg la pozitia de ridicare...");
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
  ServoPosition target_pos = getObjectPosition(obiect);
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
  Serial.println(">>> Pas 5: Cobor la pozitia tinta...");
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

bool isValidObject(String obj) {
  return (obj == "cube" || obj == "cylinder" || obj == "halfcircle" || 
          obj == "arch" || obj == "triangle" || obj == "rectangle" || obj == "cerc");
}

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