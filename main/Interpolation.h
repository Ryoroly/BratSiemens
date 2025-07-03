// Interpolation.h
#ifndef INTERPOLATION_H
#define INTERPOLATION_H

#include "Constants.h"

ServoPosition calculateInterpolatedPosition(float x, float y);
int interpolateBilinear(int bottom_left, int bottom_right, int top_left, int top_right, float x, float y);
int interpolate6Points(int bottom_left, int bottom_middle, int bottom_right,
                      int top_left, int top_middle, int top_right,
                      float x, float y);

int interpolate6PointsBiquadratic(int bottom_left, int bottom_middle, int bottom_right,
                                 int top_left, int top_middle, int top_right,
                                 float x, float y);
                                 
#endif // INTERPOLATION_H