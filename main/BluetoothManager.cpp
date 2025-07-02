// BluetoothManager.cpp
#include "BluetoothManager.h"
#include <Arduino.h> // Include pentru Serial

// Definim un "Serviciu" si o "Caracteristica" unice pentru comunicarea noastra.
BLEService dataService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic dataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite, 20);

void setupBluetooth() {
  if (!BLE.begin()) {
    Serial.println("Eroare la pornirea BLE!");
    while (1);
  }

  BLE.setLocalName("BraccioRobot_BLE");
  BLE.setAdvertisedService(dataService);
  dataService.addCharacteristic(dataCharacteristic);
  BLE.addService(dataService);
  BLE.advertise();

  Serial.println("Arduino UNO R4 WiFi gata de conexiune BLE.");
}

String readBluetoothData() {
  String receivedData = "";
  for (int i = 0; i < dataCharacteristic.valueLength(); i++) {
    receivedData += (char)dataCharacteristic.value()[i];
  }
  return receivedData;
}