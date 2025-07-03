// Interpolation.cpp
#include "Interpolation.h"
#include "Constants.h" // Pentru acces la variabilele globale și offset-uri
#include <Arduino.h> // Pentru constrain și round



ServoPosition calculateInterpolatedPosition(float x, float y) {
  ServoPosition result;

  float min_x = min(min(coord_stanga_jos.x, coord_dreapta_jos.x),
                    min(coord_dreapta_sus.x, coord_stanga_sus.x));
  float max_x = max(max(coord_stanga_jos.x, coord_dreapta_jos.x),
                    max(coord_dreapta_sus.x, coord_stanga_sus.x));


  // Includ și coordonatele punctelor de mijloc în calculul limitelor
  min_x = min(min_x, coord_mijloc_jos.x);
  max_x = max(max_x, coord_mijloc_jos.x);
  min_x = min(min_x, coord_mijloc_sus.x);
  max_x = max(max_x, coord_mijloc_sus.x);

  float min_y = min(min(coord_stanga_jos.y, coord_dreapta_jos.y),
                    min(coord_dreapta_sus.y, coord_stanga_sus.y));
  float max_y = max(max(coord_stanga_jos.y, coord_dreapta_jos.y),
                    max(coord_dreapta_sus.y, coord_stanga_sus.y));


  // Includ și coordonatele Y ale punctelor de mijloc
  min_y = min(min_y, coord_mijloc_jos.y);
  max_y = max(max_y, coord_mijloc_jos.y);
  min_y = min(min_y, coord_mijloc_sus.y);
  max_y = max(max_y, coord_mijloc_sus.y);

  float norm_x = (x - min_x) / (max_x - min_x);
  float norm_y = (y - min_y) / (max_y - min_y);

  norm_x = constrain(norm_x, 0.0f, 1.0f);
  norm_y = constrain(norm_y, 0.0f, 1.0f);

  // Interpolez pentru fiecare servo folosind 6 puncte
    result.m1_base = interpolate6Points(
        pos_stanga_jos.m1_base, pos_mijloc_jos.m1_base, pos_dreapta_jos.m1_base,
        pos_stanga_sus.m1_base, pos_mijloc_sus.m1_base, pos_dreapta_sus.m1_base,
        norm_x, norm_y
    );
    
    int base_m2 = interpolate6Points(
        pos_stanga_jos.m2_shoulder, pos_mijloc_jos.m2_shoulder, pos_dreapta_jos.m2_shoulder,
        pos_stanga_sus.m2_shoulder, pos_mijloc_sus.m2_shoulder, pos_dreapta_sus.m2_shoulder,
        norm_x, norm_y
    );
    result.m2_shoulder = constrain(base_m2 + M2_OFFSET_CORNERS, 15, 165);
    
    int base_m3 = interpolate6Points(
        pos_stanga_jos.m3_elbow, pos_mijloc_jos.m3_elbow, pos_dreapta_jos.m3_elbow,
        pos_stanga_sus.m3_elbow, pos_mijloc_sus.m3_elbow, pos_dreapta_sus.m3_elbow,
        norm_x, norm_y
    );
    result.m3_elbow = constrain(base_m3 + M3_OFFSET_CORNERS, 0, 180);
    
    result.m4_wrist_vert = interpolate6Points(
        pos_stanga_jos.m4_wrist_vert, pos_mijloc_jos.m4_wrist_vert, pos_dreapta_jos.m4_wrist_vert,
        pos_stanga_sus.m4_wrist_vert, pos_mijloc_sus.m4_wrist_vert, pos_dreapta_sus.m4_wrist_vert,
        norm_x, norm_y
    );
    
    result.m5_wrist_rot = interpolate6Points(
        pos_stanga_jos.m5_wrist_rot, pos_mijloc_jos.m5_wrist_rot, pos_dreapta_jos.m5_wrist_rot,
        pos_stanga_sus.m5_wrist_rot, pos_mijloc_sus.m5_wrist_rot, pos_dreapta_sus.m5_wrist_rot,
        norm_x, norm_y
    );
    
    result.m6_gripper = interpolate6Points(
        pos_stanga_jos.m6_gripper, pos_mijloc_jos.m6_gripper, pos_dreapta_jos.m6_gripper,
        pos_stanga_sus.m6_gripper, pos_mijloc_sus.m6_gripper, pos_dreapta_sus.m6_gripper,
        norm_x, norm_y
    );
    
    return result;
}

// Noua funcție de interpolare cu 6 puncte
int interpolate6Points(int bottom_left, int bottom_middle, int bottom_right,
                      int top_left, int top_middle, int top_right,
                      float x, float y) {
    
    // Interpolez pe rândul de jos (bottom) cu 3 puncte
    float bottom_interp;
    if (x <= 0.5f) {
        // Între stânga și mijloc
        float local_x = x * 2.0f; // Normalizez la [0,1] pentru segmentul stânga-mijloc
        bottom_interp = bottom_left + (bottom_middle - bottom_left) * local_x;
    } else {
        // Între mijloc și dreapta
        float local_x = (x - 0.5f) * 2.0f; // Normalizez la [0,1] pentru segmentul mijloc-dreapta
        bottom_interp = bottom_middle + (bottom_right - bottom_middle) * local_x;
    }
    
    // Interpolez pe rândul de sus (top) cu 3 puncte
    float top_interp;
    if (x <= 0.5f) {
        // Între stânga și mijloc
        float local_x = x * 2.0f;
        top_interp = top_left + (top_middle - top_left) * local_x;
    } else {
        // Între mijloc și dreapta
        float local_x = (x - 0.5f) * 2.0f;
        top_interp = top_middle + (top_right - top_middle) * local_x;
    }
    
    // Interpolez final între bottom și top
    float result = bottom_interp + (top_interp - bottom_interp) * y;
    
    return (int)round(result);
}

// Funcție alternativă de interpolare cu 6 puncte folosind interpolarea biquadratică
int interpolate6PointsBiquadratic(int bottom_left, int bottom_middle, int bottom_right,
                                 int top_left, int top_middle, int top_right,
                                 float x, float y) {
    
    // Calculez coeficienții pentru interpolarea pe X (folosind 3 puncte)
    // Pentru rândul de jos
    float a_bottom = 2.0f * bottom_left - 4.0f * bottom_middle + 2.0f * bottom_right;
    float b_bottom = -3.0f * bottom_left + 4.0f * bottom_middle - bottom_right;
    float c_bottom = bottom_left;
    
    // Pentru rândul de sus
    float a_top = 2.0f * top_left - 4.0f * top_middle + 2.0f * top_right;
    float b_top = -3.0f * top_left + 4.0f * top_middle - top_right;
    float c_top = top_left;
    
    // Calculez valorile interpolate pe X pentru fiecare rând
    float bottom_interp = a_bottom * x * x + b_bottom * x + c_bottom;
    float top_interp = a_top * x * x + b_top * x + c_top;
    
    // Interpolez linear între bottom și top
    float result = bottom_interp + (top_interp - bottom_interp) * y;
    
    return (int)round(result);
}