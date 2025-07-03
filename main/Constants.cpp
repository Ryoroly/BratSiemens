// Constants.cpp
#include "Constants.h"

// Inițializarea variabilelor globale
//pentru partea dreapta sus 
int m1dinstanga = 110;
int m1dindreapta = 105; 

//pentru partea dreapta jos 
int m1dinstangajos = 120;
int m1dindreaptajos = 110;


//pentru stanga sus
int m1dinstangasus = 72;//pentru stanga sus 
int m1dindreaptasus = 66;//pentru stanga sus 


//pentru stanga jos
int m1dinstangastjos = 65;//pentru stanga sus 
int m1dindreaptastjos = 60;//pentru stanga sus 


ServoPosition pos_stanga_jos;
ServoPosition pos_dreapta_jos;
ServoPosition pos_dreapta_sus;
ServoPosition pos_stanga_sus;

ServoPosition pos_mijloc_jos;
ServoPosition pos_mijloc_sus;


// pos_mijloc_jos= {90, 120, 150, 165, 40, 70};
// pos_mijloc_sus= {90, 160, 100, 165, 40, 70};

void initializeServoPositions(int pozitiefinalam1) {
    if(pozitiefinalam1 < 90) { //cand pleca din stanga in dreapta 
        pos_stanga_jos = {m1dinstangastjos, 130, 145, 165, 15, 10};
        pos_dreapta_jos = {m1dinstangajos, 130, 145, 165, 60, 10};
        pos_dreapta_sus = {m1dinstanga, 160, 100, 160, 45, 10};
        pos_stanga_sus = {m1dinstangasus, 155, 100, 160, 20, 10};
        pos_mijloc_jos= {90, 120, 150, 165, 40, 70};
        pos_mijloc_sus= {90, 160, 100, 165, 40, 70};
    }
    else { //cand pleaca din dreapta in stanga
        pos_stanga_jos = {m1dindreaptastjos, 130, 145, 165, 15, 10};
        pos_dreapta_jos = {m1dindreaptajos, 130, 145, 165, 60, 10};
        pos_dreapta_sus = {m1dindreapta, 160, 100, 160, 45, 10};
        pos_stanga_sus = {m1dindreaptasus, 155, 100, 160, 20, 10};
        pos_mijloc_jos= {90, 120, 150, 165, 40, 70};
        pos_mijloc_sus= {90, 160, 100, 165, 40, 70};
    }
}

// void initializeServoPositions(int pozitiefinalam1) {
//     if(pozitiefinalam1 < 90) { //cand pleca din stanga in dreapta 
//         pos_stanga_jos = {m1dinstangastjos, 130, 145, 165, 0, 10};
//         pos_dreapta_jos = {m1dinstangajos, 130, 145, 165, 60, 10};
//         pos_dreapta_sus = {m1dinstanga, 160, 100, 160, 45, 10};
//         pos_stanga_sus = {m1dinstangasus, 155, 100, 160, 10, 10};
//     }
//     else { //cand pleaca din dreapta in stanga
//         pos_stanga_jos = {m1dindreaptastjos, 130, 145, 165, 0, 10};
//         pos_dreapta_jos = {m1dindreaptajos, 130, 145, 165, 60, 10};
//         pos_dreapta_sus = {m1dindreapta, 160, 100, 160, 45, 10};
//         pos_stanga_sus = {m1dindreaptasus, 155, 100, 160, 10, 10};
//     }
// }




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

Point2D coord_mijloc_jos = {xul/2, 0};
Point2D coord_mijloc_sus = {xul, yul/2};


bool robotBusy = false;
String currentCommand = "";