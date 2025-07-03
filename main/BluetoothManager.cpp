// BluetoothManager.cpp
#include "BluetoothManager.h"
#include <Arduino.h> 

// Definim un "Serviciu" si o "Caracteristica" unice pentru comunicarea noastra.
BLEService dataService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic dataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite, 20);
BLECharacteristic statusCharacteristic("19B10002-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 1);

void setupBluetooth() {
  if (!BLE.begin()) {
    Serial.println("Eroare la pornirea BLE!");
    while (1);
  }

  BLE.setLocalName("BraccioRobot_BLE");
  BLE.setAdvertisedService(dataService);

  dataService.addCharacteristic(dataCharacteristic);
  dataService.addCharacteristic(statusCharacteristic);//trimite 1 sau 0

  BLE.addService(dataService);
  BLE.advertise();

  updateBLEStatus(0);

  Serial.println("Arduino UNO R4 WiFi gata de conexiune BLE.");
}

String readBluetoothData() {
  String receivedData = "";
  for (int i = 0; i < dataCharacteristic.valueLength(); i++) {
    receivedData += (char)dataCharacteristic.value()[i];
  }
  return receivedData;
}


//se trimite 1 si 0
void sendStatusToBLE(int status) {
  updateBLEStatus(status);
  Serial.print(">>> Status BLE trimis: ");
  Serial.println(status);
}

void updateBLEStatus(int status) {
  // Convertim int-ul la byte pentru a-l trimite
  byte statusByte = (byte)status;
  statusCharacteristic.writeValue(statusByte);
}