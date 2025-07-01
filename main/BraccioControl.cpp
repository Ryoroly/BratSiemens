// BraccioControl.cpp
#include "BraccioControl.h"
#include "Constants.h"
#include "Interpolation.h" // Necesara pentru calculateInterpolatedPosition
#include <Arduino.h> // Pentru Serial.println
#include <Braccio.h>

void executeTransportSequence(float pickup_x, float pickup_y, int obiect_id) {
  // PASUL 1: Mergem la poziția de ridicare cu gripper deschis și M5 FIXAT LA 30
  ServoPosition pickup_pos = calculateInterpolatedPosition(pickup_x, pickup_y);
  pickup_pos.m6_gripper = 10; // Gripper deschis

  // Aplicăm offseturile pentru apucare mai bună
  pickup_pos.m2_shoulder = constrain(pickup_pos.m2_shoulder + M2_OFFSET_PICKUP, 15, 165);
  pickup_pos.m3_elbow = constrain(pickup_pos.m3_elbow + M3_OFFSET_PICKUP, 0, 180);

  // IMPORTANT: Setăm M5 la poziția FIXĂ de pickup (30 grade)!
  pickup_pos.m5_wrist_rot = M5_PICKUP_POSITION;

  Serial.println(">>> Pas 1: Merg la poziția de ridicare cu M5 FIXAT la 30 grade...");
  Serial.print(">>> Poziție ajustată: M2="); Serial.print(pickup_pos.m2_shoulder);
  Serial.print(", M3="); Serial.print(pickup_pos.m3_elbow);
  Serial.print(", M5="); Serial.print(pickup_pos.m5_wrist_rot);
  Serial.println(" (M5 FIXAT la poziția de pickup!)");

  moveToPositionThroughTransitionWithFixedM5(pickup_pos);

  // PASUL 2: Închidem gripperul pentru a ridica obiectul
  Serial.println(">>> Pas 2: Închid gripperul...");
  pickup_pos.m6_gripper = 70; // Închidem gripperul
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        pickup_pos.m1_base,
                        pickup_pos.m2_shoulder,
                        pickup_pos.m3_elbow,
                        pickup_pos.m4_wrist_vert,
                        pickup_pos.m5_wrist_rot,
                        pickup_pos.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // PASUL 3: Ridicăm la poziția de trecere cu obiectul și M5 la 130
  Serial.println(">>> Pas 3: Ridic la poziția de trecere și rotesc M5 la 130...");
  ServoPosition trecere_cu_obiect = pos_trecere;
  trecere_cu_obiect.m1_base = pickup_pos.m1_base;
  trecere_cu_obiect.m6_gripper = 70; // Era 50
  trecere_cu_obiect.m5_wrist_rot = M5_TRANSPORT_POSITION; // M5 la poziția de transport (130)

  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        trecere_cu_obiect.m1_base,
                        trecere_cu_obiect.m2_shoulder,
                        trecere_cu_obiect.m3_elbow,
                        trecere_cu_obiect.m4_wrist_vert,
                        trecere_cu_obiect.m5_wrist_rot,
                        trecere_cu_obiect.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // PASUL 4: Rotim M1 către poziția țintă (M5 rămâne la 130!)
  ServoPosition target_pos = pos_objects[obiect_id];
  ServoPosition trecere_rotit = pos_trecere;
  trecere_rotit.m1_base = target_pos.m1_base;
  trecere_rotit.m6_gripper = 70; // 50
  trecere_rotit.m5_wrist_rot = M5_TRANSPORT_POSITION; // M5 rămâne la poziția de transport

  Serial.println(">>> Pas 4: Rotesc M1 către poziția țintă (M5 rămâne la 130!)...");
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        trecere_rotit.m1_base,
                        trecere_rotit.m2_shoulder,
                        trecere_rotit.m3_elbow,
                        trecere_rotit.m4_wrist_vert,
                        trecere_rotit.m5_wrist_rot,
                        trecere_rotit.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // PASUL 5: Coborâm la poziția țintă (M5 rămâne la 130)
  target_pos.m6_gripper = 70; //50
  target_pos.m5_wrist_rot = M5_TRANSPORT_POSITION; // M5 rămâne la poziția de transport
  Serial.println(">>> Pas 5: Cobor la poziția țintă cu M5 la 130...");
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        target_pos.m1_base,
                        target_pos.m2_shoulder,
                        target_pos.m3_elbow,
                        target_pos.m4_wrist_vert,
                        target_pos.m5_wrist_rot,
                        target_pos.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // PASUL 6: Deschidem gripperul pentru a lăsa obiectul
  Serial.println(">>> Pas 6: Deschid gripperul...");
  target_pos.m6_gripper = 10;
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        target_pos.m1_base,
                        target_pos.m2_shoulder,
                        target_pos.m3_elbow,
                        target_pos.m4_wrist_vert,
                        target_pos.m5_wrist_rot,
                        target_pos.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // PASUL 7: Ridicăm la poziția de trecere
  Serial.println(">>> Pas 7: Ridic la poziția de trecere...");
  ServoPosition trecere_final = pos_trecere;
  trecere_final.m1_base = target_pos.m1_base;
  trecere_final.m5_wrist_rot = M5_TRANSPORT_POSITION; // Păstrăm M5 la 130
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        trecere_final.m1_base,
                        trecere_final.m2_shoulder,
                        trecere_final.m3_elbow,
                        trecere_final.m4_wrist_vert,
                        trecere_final.m5_wrist_rot,
                        trecere_final.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // PASUL 8: Resetăm progresiv M5 pentru următoarea comandă
  Serial.println(">>> Pas 8: Resetez progresiv M5 pentru următoarea comandă...");
  smoothRotateM5(trecere_final, pos_trecere.m5_wrist_rot, 3); // Înapoi la poziția standard
}

// Funcție nouă pentru rotirea progresivă a M5
void smoothRotateM5(ServoPosition base_pos, int target_m5, int steps) {
  int current_m5 = base_pos.m5_wrist_rot;
  int step_size = (target_m5 - current_m5) / steps;

  Serial.print(">>> Rotesc M5 de la "); Serial.print(current_m5);
  Serial.print(" la "); Serial.print(target_m5);
  Serial.print(" în "); Serial.print(steps); Serial.println(" pași");

  for (int i = 1; i <= steps; i++) {
    int intermediate_m5;
    if (i == steps) {
      intermediate_m5 = target_m5; // Ultimul pas - poziția exactă
    } else {
      intermediate_m5 = current_m5 + (step_size * i);
    }

    Serial.print(">>> Pas M5 "); Serial.print(i);
    Serial.print("/"); Serial.print(steps);
    Serial.print(": M5="); Serial.println(intermediate_m5);

    Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                          base_pos.m1_base,
                          base_pos.m2_shoulder,
                          base_pos.m3_elbow,
                          base_pos.m4_wrist_vert,
                          intermediate_m5,
                          base_pos.m6_gripper);
    delay(DELAY_MODIFICABIL);
  }

  // Actualizăm poziția de bază cu noua valoare M5
  base_pos.m5_wrist_rot = target_m5;
}

void moveToPositionThroughTransitionWithFixedM5(ServoPosition pos) {
  // Mergem mai întâi la poziția de trecere cu M1 corect și M5 la poziția standard
  ServoPosition trecere_pos = pos_trecere;
  trecere_pos.m1_base = pos.m1_base;
  trecere_pos.m6_gripper = pos.m6_gripper;
  // M5 rămâne la poziția standard din pos_trecere

  Serial.println(">>> Merg la poziția de trecere cu M5 standard...");
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        trecere_pos.m1_base,
                        trecere_pos.m2_shoulder,
                        trecere_pos.m3_elbow,
                        trecere_pos.m4_wrist_vert,
                        trecere_pos.m5_wrist_rot,
                        trecere_pos.m6_gripper);
  delay(DELAY_MODIFICABIL);

  // Acum rotim progresiv M5 la poziția de pickup (30)
  Serial.println(">>> Rotesc progresiv M5 pe drum către pickup la 30 grade...");
  smoothRotateM5(trecere_pos, M5_PICKUP_POSITION, 3); // Rotim M5 la 30

  // În final, mergem la poziția de pickup cu M5 la 30
  Serial.println(">>> Ajung la poziția de pickup cu M5 la 30 grade...");
  pos.m5_wrist_rot = M5_PICKUP_POSITION; // Asigurăm că M5 este la 30
  Braccio.ServoMovement(DELAY_BRACCIO_MOVEMENT,
                        pos.m1_base,
                        pos.m2_shoulder,
                        pos.m3_elbow,
                        pos.m4_wrist_vert,
                        pos.m5_wrist_rot,
                        pos.m6_gripper);
}