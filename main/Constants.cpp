// Constants.cpp
#include "Constants.h"

// Inițializarea variabilelor globale
//pentru partea dreapta sus ok
int m1dinstanga = 110;
int m1dindreapta = 105; //bun

//pentru partea dreapta jos ok
int m1dinstangajos = 120;//bun
int m1dindreaptajos = 110;//bun


//pentru stanga sus
int m1dinstangasus = 72;//pentru stanga sus //bun
int m1dindreaptasus = 68;//pentru stanga sus //bun


//pentru stanga jos
int m1dinstangastjos = 65;//pentru stanga sus //bun
int m1dindreaptastjos = 60;//pentru stanga sus //bun


//int pozitiefinalam1;

ServoPosition pos_stanga_jos;
ServoPosition pos_dreapta_jos;
ServoPosition pos_dreapta_sus;
ServoPosition pos_stanga_sus;


void initializeServoPositions(int pozitiefinalam1) {
    if(pozitiefinalam1 < 90) { //cand pleca din stanga in dreapta 
        pos_stanga_jos = {m1dinstangastjos, 120, 140, 160, 10, 10};
        pos_dreapta_jos = {m1dinstangajos, 120, 140, 160, 50, 10};
        pos_dreapta_sus = {m1dinstanga, 150, 100, 160, 20, 10};
        pos_stanga_sus = {m1dinstangasus, 150, 100, 160, 20, 10};
    }
    else { //cand pleaca din dreapta in stanga
        pos_stanga_jos = {m1dindreaptastjos, 120, 140, 160, 10, 10};
        pos_dreapta_jos = {m1dindreaptajos, 120, 140, 160, 50, 10};
        pos_dreapta_sus = {m1dindreapta, 150, 100, 160, 20, 10};
        pos_stanga_sus = {m1dindreaptasus, 150, 100, 160, 20, 10};
    }
}




ServoPosition pos_trecere = {90, 100, 165, 90, 110, 10};

ServoPosition pos_objects[7] = {
  {0, 0, 0, 0, 0, 0},         // Index 0 - nefolosit
  {180, 120, 130, 160, 60, 10},    // ID 1 - cube --4
  {160, 130, 120, 160, 60, 10},    // ID 2 - cylinder
  {140, 140, 120, 140, 60, 10},    // ID 3 - halfcircle
  {0, 130, 130, 160, 60, 10},      // ID 4 - arch --3
  {20, 140, 120, 140, 60, 10},     // ID 5 - triangle -- 1
  {40, 150, 100, 140, 60, 10}      // ID 6 - rectangle --2
};

int xul = 1290;
int yul = 572;
Point2D coord_stanga_jos = {0, 0};
Point2D coord_dreapta_jos = {xul, 0};
Point2D coord_dreapta_sus = {xul, yul};
Point2D coord_stanga_sus = {0, yul};

bool robotBusy = false;
String currentCommand = "";