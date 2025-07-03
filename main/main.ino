// main.ino
#include "Constants.h"
#include "BluetoothManager.h"
#include "BraccioControl.h"
#include "Interpolation.h"
#include "Braccio.h"

#include <ArduinoBLE.h>
//#include <Braccio.h>
#include <Servo.h> 
#include <Arduino.h> 



// Define the global Servo objects
Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_ver;
Servo wrist_rot;
Servo gripper;


// Variabile globale definite aici sau extern în Constants.h
extern bool robotBusy;
extern String currentCommand;
extern int xul;
extern int yul;
extern Point2D coord_stanga_jos;
extern Point2D coord_dreapta_jos;
extern Point2D coord_dreapta_sus;
extern Point2D coord_stanga_sus;

extern Point2D coord_mijloc_jos;
extern Point2D coord_mijloc_sus;

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("=== BRACCIO ROBOT CU CONTROL BLE SI SERIAL ===");
  Serial.print("Offset Y activ: "); Serial.println(Y_OFFSET);
  Serial.println("(Pentru Y mai jos folosește valori pozitive, pentru Y mai sus folosește valori negative)");
  Serial.println("Astept conexiune de la Raspberry Pi...");
  Serial.println("COMENZI ACCEPTATE:");
  Serial.println("BLE/Serial: S xul yul - Seteaza dimensiunile zonei");
  Serial.println("BLE/Serial: T x y id - Transporta obiectul (id: 1-6)");
  Serial.println("Serial SIMPLIFICAT: x y id - Transport direct (fara T)");
  Serial.println("   ID obiecte: 1=cube, 2=cylinder, 3=halfcircle");
  Serial.println("                 4=arch, 5=triangle, 6=rectangle");
  Serial.println("===============================================");

  // Inițializează Bluetooth
  setupBluetooth();

  // Inițializează robotul Braccio
  Braccio.begin();
}

void loop() {
  // Verifică comenzile de la Serial Monitor
  checkSerialCommands();

  // Așteaptă ca Raspberry Pi să se conecteze
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("*** CONECTAT la dispozitivul: ");
    Serial.println(central.address());
    Serial.println("*** Gata să primesc comenzi!");

    while (central.connected()) {
      checkSerialCommands(); // Verifică Serial chiar și când ești conectat la BLE

      if (dataCharacteristic.written() && !robotBusy) {
        String receivedData = readBluetoothData();
        Serial.print(">>> MESAJ PRIMIT (BLE): ");
        Serial.println(receivedData);
        processCommand(receivedData);
      }
      delay(10); // Mic delay pentru a nu suprasolicita procesorul
    }

    Serial.print("*** DECONECTAT de la: ");
    Serial.println(central.address());
    robotBusy = false; // Resetează starea la deconectare
  }
}

// Implementări ale funcțiilor auxiliare
void checkSerialCommands() {
  if (Serial.available() && !robotBusy) {
    String serialCommand = Serial.readStringUntil('\n');
    serialCommand.trim();

    if (serialCommand.length() > 0) {
      Serial.print(">>> COMANDĂ SERIAL: ");
      Serial.println(serialCommand);

      if (!serialCommand.startsWith("S") && !serialCommand.startsWith("T")) {
        handleSimplifiedCommand(serialCommand);
      } else {
        processCommand(serialCommand);
      }
    }
  }
}

void handleSimplifiedCommand(String command) {
  Serial.println(">>> COMANDĂ SIMPLIFICATĂ DETECTATĂ");

  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);

  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println(">>> EROARE: Format greșit! Folosiți: x y id");
    return;
  }

  float pickup_x = command.substring(0, firstSpace).toFloat();
  float pickup_y = command.substring(firstSpace + 1, secondSpace).toFloat();
  int obiect_id = command.substring(secondSpace + 1).toInt();

  Serial.println(">>> EXECUTEZ COMANDĂ SIMPLIFICATĂ:");
  Serial.print(">>> X="); Serial.print(pickup_x);
  Serial.print(", Y="); Serial.print(pickup_y);
  Serial.print(", ID="); Serial.println(obiect_id);

  String transportCommand = "T " + String(pickup_x) + " " + String(pickup_y) + " " + String(obiect_id);
  processCommand(transportCommand);
}

void processCommand(String command) {
  command.trim();
  Serial.print(">>> PROCESEZ COMANDĂ: ");
  Serial.println(command);

  if (command.startsWith("S")) {
    handleSetAreaCommand(command);
  } else if (command.startsWith("T")) {
    handleTransportCommand(command);
  } else {
    Serial.println(">>> COMANDĂ NECUNOSCUTĂ!");
    Serial.println(">>> Folosiți: S xul yul sau T x y id sau x y id");
  }
}

void handleSetAreaCommand(String command) {
  Serial.println(">>> SETEZ ZONA DE LUCRU...");

  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);

  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println(">>> EROARE: Format greșit! Folosiți: S xul yul");
    return;
  }

  int new_xul = command.substring(firstSpace + 1, secondSpace).toInt();
  int new_yul = command.substring(secondSpace + 1).toInt();

  xul = new_xul;
  yul = new_yul;
  coord_dreapta_jos = { (float)xul, 0.0f };
  coord_dreapta_sus = { (float)xul, (float)yul };
  coord_stanga_sus = { 0.0f, (float)yul };

  Serial.print(">>> ZONĂ SETATĂ: XUL=");
  Serial.print(xul);
  Serial.print(", YUL=");
  Serial.println(yul);
  Serial.println(">>> GATA SĂ PRIMESC COMENZI DE TRANSPORT!");
}

void handleTransportCommand(String command) {
  robotBusy = true; // Marchează robotul ca ocupat
  currentCommand = command;

  Serial.println(">>> ÎNCEP TRANSPORT OBIECT...");

  int firstSpace = command.indexOf(' ');
  int secondSpace = command.indexOf(' ', firstSpace + 1);
  int thirdSpace = command.indexOf(' ', secondSpace + 1);

  if (firstSpace == -1 || secondSpace == -1 || thirdSpace == -1) {
    Serial.println(">>> EROARE: Format greșit! Folosiți: T x y id");
    robotBusy = false;
    return;
  }

  float pickup_x = command.substring(firstSpace + 1, secondSpace).toFloat();
  float pickup_y = command.substring(secondSpace + 1, thirdSpace).toFloat();
  int obiect_id = command.substring(thirdSpace + 1).toInt();

  // APLICĂM OFFSET-ul PENTRU Y
  float adjusted_pickup_y = pickup_y + Y_OFFSET;
  float adjusted_pickup_x = pickup_x + X_OFFSET;

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
  Serial.print(Y_OFFSET);
  Serial.println(")");
  Serial.print(">>> Transport către obiect ID: ");
  Serial.println(obiect_id);
  Serial.println(">>> Folosesc poziții fixe pentru M5:");
  Serial.print(">>> M5 la pickup: "); Serial.println(M5_PICKUP_POSITION);
  Serial.print(">>> M5 în transport: "); Serial.println(M5_TRANSPORT_POSITION);

  // Execută secvența de transport cu Y ajustat
  executeTransportSequence(adjusted_pickup_x, adjusted_pickup_y, obiect_id);

  Serial.println(">>> === TRANSPORT COMPLET! ===");
  Serial.println(">>> Robot gata pentru următoarea comandă!");
  robotBusy = false; // Marchează robotul ca liber
}