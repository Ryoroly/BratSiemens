#ifndef BRACCIO_H_
#define BRACCIO_H_

#include <Arduino.h>
#include <Servo.h>

// You should set begin(SOFT_START_DISABLED) if you are using the Arm Robot shield V1.6
#define SOFT_START_DISABLED		-999

//The default value for the soft start
#define SOFT_START_DEFAULT		0

//The software PWM is connected to PIN 12. You cannot use the pin 12 if you are using
#define SOFT_START_CONTROL_PIN	12

//Low and High Limit Timeout for the Software PWM
#define LOW_LIMIT_TIMEOUT 2000
#define HIGH_LIMIT_TIMEOUT 6000

// ===== CONFIGURARE SECVENTA DE DEMONSTRATIE =====
// Setează pe 1 pentru a executa secvența de demonstrație după inițializare
// Setează pe 0 pentru a dezactiva secvența
#define DEMO_SEQUENCE_ENABLED 0  // 1 = activat, 0 = dezactivat

// Delay-ul între mișcările din secvența de demonstrație (millisecunde)
#define DEMO_MOVEMENT_DELAY 0     // 0 = fără delay între pozițiile din secvență
#define DEMO_SERVO_SPEED 10       // Viteza servo-urilor în secvență (5-10ms recomandat)
#define DEMO_REPEAT_COUNT 2       // Numărul de repetări al secvenței
// ==================================================

class _Braccio {

public:
  _Braccio();
  	
  /**
  * Braccio initializations and set intial position
  * Modifing this function you can set up the initial position of all the
  * servo motors of Braccio 
  * @param soft_start_level: the minimum value is -70, default value is 0 (SOFT_START_DEFAULT)
  * You should set begin(SOFT_START_DISABLED) if you are using the Arm Robot shield V1.6
  * @param init_delay: delay pentru inițializarea lentă (default INIT_DELAY), 0 = inițializare rapidă
  * @param demo_enabled: 1 pentru a executa secvența demo, 0 pentru a o dezactiva (default: folosește DEMO_SEQUENCE_ENABLED)
  */
  unsigned int begin(int soft_start_level=SOFT_START_DEFAULT, int init_delay=-1, int demo_enabled=-1);
  
  int ServoMovement(int delay, int Vbase,int Vshoulder, int Velbow, int Vwrist_ver, int Vwrist_rot, int Vgripper);

  /**
  * Execută secvența de demonstrație predefinită
  * Pozițiile: (0,90,120,80,130,10) -> (0,90,80,80,130,10) -> (0,90,40,80,130,10)
  */
  void executeDemoSequence();
	
private:
  void _softStart(int soft_start_level);
	
  void _softwarePWM(int high_time, int low_time);
  
  void _slowInitialization(int init_delay);

};

extern _Braccio Braccio;

#endif