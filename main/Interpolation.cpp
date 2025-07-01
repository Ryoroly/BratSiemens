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

  float min_y = min(min(coord_stanga_jos.y, coord_dreapta_jos.y),
                    min(coord_dreapta_sus.y, coord_stanga_sus.y));
  float max_y = max(max(coord_stanga_jos.y, coord_dreapta_jos.y),
                    max(coord_dreapta_sus.y, coord_stanga_sus.y));

  float norm_x = (x - min_x) / (max_x - min_x);
  float norm_y = (y - min_y) / (max_y - min_y);

  norm_x = constrain(norm_x, 0.0f, 1.0f);
  norm_y = constrain(norm_y, 0.0f, 1.0f);

  result.m1_base = interpolateBilinear(
    pos_stanga_jos.m1_base, pos_dreapta_jos.m1_base,
    pos_stanga_sus.m1_base, pos_dreapta_sus.m1_base,
    norm_x, norm_y
  );

  // Aplicăm offseturile pentru pozițiile din colțuri
  int base_m2 = interpolateBilinear(
    pos_stanga_jos.m2_shoulder, pos_dreapta_jos.m2_shoulder,
    pos_stanga_sus.m2_shoulder, pos_dreapta_sus.m2_shoulder,
    norm_x, norm_y
  );
  result.m2_shoulder = constrain(base_m2 + M2_OFFSET_CORNERS, 15, 165);

  int base_m3 = interpolateBilinear(
    pos_stanga_jos.m3_elbow, pos_dreapta_jos.m3_elbow,
    pos_stanga_sus.m3_elbow, pos_dreapta_sus.m3_elbow,
    norm_x, norm_y
  );
  result.m3_elbow = constrain(base_m3 + M3_OFFSET_CORNERS, 0, 180);

  result.m4_wrist_vert = interpolateBilinear(
    pos_stanga_jos.m4_wrist_vert, pos_dreapta_jos.m4_wrist_vert,
    pos_stanga_sus.m4_wrist_vert, pos_dreapta_sus.m4_wrist_vert,
    norm_x, norm_y
  );

  result.m5_wrist_rot = interpolateBilinear(
    pos_stanga_jos.m5_wrist_rot, pos_dreapta_jos.m5_wrist_rot,
    pos_stanga_sus.m5_wrist_rot, pos_dreapta_sus.m5_wrist_rot,
    norm_x, norm_y
  );

  result.m6_gripper = interpolateBilinear(
    pos_stanga_jos.m6_gripper, pos_dreapta_jos.m6_gripper,
    pos_stanga_sus.m6_gripper, pos_dreapta_sus.m6_gripper,
    norm_x, norm_y
  );

  return result;
}

int interpolateBilinear(int bottom_left, int bottom_right, int top_left, int top_right, float x, float y) {
  float bottom_interp = bottom_left + (bottom_right - bottom_left) * x;
  float top_interp = top_left + (top_right - top_left) * x;
  float result = bottom_interp + (top_interp - bottom_interp) * y;

  return (int)round(result);
}