#ifndef WEBCONTROL_H
#define WEBCONTROL_H

#include <WiFiS3.h>
#include <Servo.h>
#include <Braccio.h>  // Add this include

// Function declarations
void setupWebServer();
void handleWebControl();
String getStatusJSON();
void moveServo(String joint, String direction);
String getWebPage();  // Add this declaration

// Global variables
extern int baseAngle;
extern int shoulderAngle;
extern int elbowAngle;
extern int wristRotAngle;
extern int wristVerAngle;
extern int gripperAngle;

#endif
