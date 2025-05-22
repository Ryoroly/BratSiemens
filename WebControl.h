#ifndef WEBCONTROL_H
#define WEBCONTROL_H

#include <Braccio.h>

void setupWebServer();
void handleWebControl();

// Variabile pentru control servo
extern int baseAngle;
extern const int step;

#endif
