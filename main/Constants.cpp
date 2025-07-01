// Constants.cpp
#include "Constants.h"

// Inițializarea variabilelor globale
ServoPosition pos_stanga_jos = {60, 120, 140, 160, 10, 10};
ServoPosition pos_dreapta_jos = {110, 120, 140, 160, 50, 10};
ServoPosition pos_dreapta_sus = {110, 150, 100, 160, 20, 10};
ServoPosition pos_stanga_sus = {70, 150, 100, 160, 20, 10};

ServoPosition pos_trecere = {90, 100, 165, 90, 110, 10};

ServoPosition pos_objects[7] = {
  {0, 0, 0, 0, 0, 0},         // Index 0 - nefolosit
  {180, 120, 130, 160, 60, 10},    // ID 1 - cube
  {160, 130, 120, 160, 60, 10},    // ID 2 - cylinder
  {140, 140, 120, 140, 60, 10},    // ID 3 - halfcircle
  {0, 130, 130, 160, 60, 10},      // ID 4 - arch
  {20, 140, 120, 140, 60, 10},     // ID 5 - triangle
  {40, 150, 100, 140, 60, 10}      // ID 6 - rectangle
};

int xul = 1290;
int yul = 572;
Point2D coord_stanga_jos = {0, 0};
Point2D coord_dreapta_jos = {xul, 0};
Point2D coord_dreapta_sus = {xul, yul};
Point2D coord_stanga_sus = {0, yul};

bool robotBusy = false;
String currentCommand = "";