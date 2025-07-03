// BluetoothManager.h
#ifndef BLUETOOTH_MANAGER_H
#define BLUETOOTH_MANAGER_H

#include <ArduinoBLE.h>
#include <Arduino.h>

extern BLEService dataService;
extern BLECharacteristic dataCharacteristic;
extern BLECharacteristic statusCharacteristic;

void setupBluetooth();
String readBluetoothData();


void sendStatusToBLE(int status);
void updateBLEStatus(int status);

#endif // BLUETOOTH_MANAGER_H