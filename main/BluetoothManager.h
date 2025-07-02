// BluetoothManager.h
#ifndef BLUETOOTH_MANAGER_H
#define BLUETOOTH_MANAGER_H

#include <ArduinoBLE.h>

extern BLEService dataService;
extern BLECharacteristic dataCharacteristic;

void setupBluetooth();
String readBluetoothData();

#endif // BLUETOOTH_MANAGER_H