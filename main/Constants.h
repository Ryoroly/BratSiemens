// Constants.h
#ifndef CONSTANTS_H
#define CONSTANTS_H

#include <Arduino.h>

// ===== VARIABILE DE AJUSTARE PENTRU APUCARE OPTIMIZATA =====
// Aceste valori se adaugă la pozițiile M2 și M3 pentru o apucare mai bună
const int M2_OFFSET_PICKUP = 10;     // Offset pentru M2 (shoulder) la pickup - valori negative coboară brațul
const int M3_OFFSET_PICKUP = 10;     // Offset pentru M3 (elbow) la pickup - valori negative apropie cotul
const int M2_OFFSET_CORNERS = 0;    // Offset pentru M2 în pozițiile din colțurile dreptunghiului
const int M3_OFFSET_CORNERS = 0;    // Offset pentru M3 în pozițiile din colțurile dreptunghiului


const int Y_OFFSET = -110;          // Valoarea care se adaugă la Y pentru a coborî brațul
const int X_OFFSET = 0;  

const int M5_PICKUP_POSITION = 30;   // M5 la pickup - poziția fixă pentru apucare
const int M5_TRANSPORT_POSITION = 130; // M5 în transport - poziția fixă pentru transport

// Variabile pentru controlul delay-urilor
const int DELAY_MODIFICABIL = 10; //intre operatii
const int DELAY_BRACCIO_MOVEMENT = 15; //pentru brat

// Structuri de date
struct ServoPosition {
  int m1_base;
  int m2_shoulder;
  int m3_elbow;
  int m4_wrist_vert;
  int m5_wrist_rot;
  int m6_gripper;
};

struct Point2D {
  float x;
  float y;
};

// Poziții pentru colțurile dreptunghiului
extern ServoPosition pos_stanga_jos;
extern ServoPosition pos_dreapta_jos;
extern ServoPosition pos_dreapta_sus;
extern ServoPosition pos_stanga_sus;

// Poziție de trecere pentru toate mișcările
extern ServoPosition pos_trecere;

// Poziții pentru obiecte predefinite (ID-uri 1-6)
extern ServoPosition pos_objects[7];

// Variabile pentru coordonatele dreptunghiului - vor fi actualizate din BLE
extern int xul;
extern int yul;
extern Point2D coord_stanga_jos;
extern Point2D coord_dreapta_jos;
extern Point2D coord_dreapta_sus;
extern Point2D coord_stanga_sus;

// Variabile pentru starea robotului
extern bool robotBusy;
extern String currentCommand;



void initializeServoPositions(int pozitiefinalam1);
//pozitie pe care o ia dupa ce face o miscare pentru m1


#endif // CONSTANTS_H