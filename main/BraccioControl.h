// BraccioControl.h
#ifndef BRACCIO_CONTROL_H
#define BRACCIO_CONTROL_H

#include "Constants.h"
#include <Braccio.h> // Necesara pentru ServoMovement


void executeTransportSequence(float pickup_x, float pickup_y, int obiect_id);
void smoothRotateM5(ServoPosition base_pos, int target_m5, int steps);
void moveToPositionThroughTransitionWithFixedM5(ServoPosition pos);

#endif // BRACCIO_CONTROL_H