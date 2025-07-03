#include "Braccio.h"

// ===== CONFIGURARE POZITII INITIALE SI DELAY =====
// Aici poti schimba pozitiile initiale ale robotului la pornire
int INIT_BASE = 180;          // Pozitia initiala base (0-180)
int INIT_SHOULDER = 90;    // Pozitia initiala shoulder (15-165)
int INIT_ELBOW = 170;       // Pozitia initiala elbow (0-180)
int INIT_WRIST_VER = 80;    // Pozitia initiala wrist vertical (0-180)
int INIT_WRIST_ROT = 40;    // Pozitia initiala wrist rotational (0-180)
int INIT_GRIPPER = 10;      // Pozitia initiala gripper (6-73)

// Delay-ul la initializare (millisecunde intre pasi)
int INIT_DELAY = 30;        // Recomandat: 10-30ms
// ===================================================

extern Servo base;
extern Servo shoulder;
extern Servo elbow;
extern Servo wrist_rot;
extern Servo wrist_ver;
extern Servo gripper;

extern int step_base = 0;
extern int step_shoulder = 45;
extern int step_elbow = 180;
extern int step_wrist_rot = 180;
extern int step_wrist_ver = 90;
extern int step_gripper = 10;
 

_Braccio Braccio;

//Initialize Braccio object
_Braccio::_Braccio() {
}

/**
 * Funcție pentru inițializarea lentă a servo-urilor la pornire
 * @param init_delay: delay-ul între pași la inițializare (recomandat 15-30ms)
 */
void _Braccio::_slowInitialization(int init_delay) {
    // Setează pozițiile curente la 90 grade pentru a avea un punct de plecare neutral
    int current_base = 90;
    int current_shoulder = 90;
    int current_elbow = 90;
    int current_wrist_ver = 90;
    int current_wrist_rot = 90;
    int current_gripper = 40;
    
    // Pozițiile finale dorite (folosesc variabilele configurabile)
    int target_base = INIT_BASE;
    int target_shoulder = INIT_SHOULDER;
    int target_elbow = INIT_ELBOW;
    int target_wrist_ver = INIT_WRIST_VER;
    int target_wrist_rot = INIT_WRIST_ROT;
    int target_gripper = INIT_GRIPPER;
    
    // Mișcare graduală către pozițiile finale
    bool moving = true;
    while (moving) {
        moving = false;
        
        // Base
        if (current_base != target_base) {
            if (current_base < target_base) current_base++;
            else current_base--;
            base.write(current_base);
            moving = true;
        }
        
        // Shoulder
        if (current_shoulder != target_shoulder) {
            if (current_shoulder < target_shoulder) current_shoulder++;
            else current_shoulder--;
            shoulder.write(current_shoulder);
            moving = true;
        }
        
        // Elbow
        if (current_elbow != target_elbow) {
            if (current_elbow < target_elbow) current_elbow++;
            else current_elbow--;
            elbow.write(current_elbow);
            moving = true;
        }
        
        // Wrist Ver
        if (current_wrist_ver != target_wrist_ver) {
            if (current_wrist_ver < target_wrist_ver) current_wrist_ver++;
            else current_wrist_ver--;
            wrist_ver.write(current_wrist_ver);
            moving = true;
        }
        
        // Wrist Rot
        if (current_wrist_rot != target_wrist_rot) {
            if (current_wrist_rot < target_wrist_rot) current_wrist_rot++;
            else current_wrist_rot--;
            wrist_rot.write(current_wrist_rot);
            moving = true;
        }
        
        // Gripper
        if (current_gripper != target_gripper) {
            if (current_gripper < target_gripper) current_gripper++;
            else current_gripper--;
            gripper.write(current_gripper);
            moving = true;
        }
        
        delay(init_delay);
    }
    
    // Setează pozițiile finale în variabilele step
    step_base = target_base;
    step_shoulder = target_shoulder;
    step_elbow = target_elbow;
    step_wrist_ver = target_wrist_ver;
    step_wrist_rot = target_wrist_rot;
    step_gripper = target_gripper;
}

/**
 * Execută secvența de demonstrație predefinită
 * Pozițiile: (0,90,120,80,130,10) -> (0,90,80,80,130,10) -> (0,90,40,80,130,10)
 * Repetă secvența de DEMO_REPEAT_COUNT ori
 */
void _Braccio::executeDemoSequence() {
    // Repetă secvența de câte ori este specificat
    for(int repeat = 0; repeat < DEMO_REPEAT_COUNT; repeat++) {
        // Poziția 1: (0,90,120,80,130,10)
        ServoMovement(DEMO_SERVO_SPEED, 0, 90, 120, 80, 130, 10);
        delay(DEMO_MOVEMENT_DELAY);
        
        // Poziția 2: (0,90,80,80,130,10)
        ServoMovement(DEMO_SERVO_SPEED, 0, 90, 80, 80, 130, 10);
        delay(DEMO_MOVEMENT_DELAY);
        
        // Poziția 3: (0,90,40,80,130,10)
        ServoMovement(DEMO_SERVO_SPEED, 0, 90, 40, 80, 130, 10);
        delay(DEMO_MOVEMENT_DELAY);
    }
}

/**
 * Braccio initialization and set intial position
 * Modifing this function you can set up the initial position of all the
 * servo motors of Braccio
 * @param soft_start_level: default value is 0 (SOFT_START_DEFAULT)
 * You should set begin(SOFT_START_DISABLED) if you are using the Arm Robot shield V1.6
 * SOFT_START_DISABLED disable the Braccio movements
 * @param init_delay: delay pentru inițializarea lentă (default 20ms), 0 = inițializare rapidă
 * @param demo_enabled: 1 pentru a executa secvența demo, 0 pentru a o dezactiva (default: folosește DEMO_SEQUENCE_ENABLED)
 */
unsigned int _Braccio::begin(int soft_start_level, int init_delay, int demo_enabled) {
	//Calling Braccio.begin(SOFT_START_DISABLED) the Softstart is disabled and you can use the pin 12
	if(soft_start_level!=SOFT_START_DISABLED){
		pinMode(SOFT_START_CONTROL_PIN,OUTPUT);
		digitalWrite(SOFT_START_CONTROL_PIN,LOW);
	}

	// initialization pin Servo motors
	base.attach(11);
	shoulder.attach(10);
	elbow.attach(9);
	wrist_rot.attach(6);
	wrist_ver.attach(5);
	gripper.attach(3);
        
	if(init_delay == -1) {
		// Folosește delay-ul default din variabilele configurabile
		init_delay = INIT_DELAY;
	}
	
	if(init_delay > 0) {
		// Inițializare lentă cu delay controlabil
		_slowInitialization(init_delay);
	} else {
		// Inițializare rapidă (folosesc variabilele configurabile)
		base.write(INIT_BASE);
		shoulder.write(INIT_SHOULDER);
		elbow.write(INIT_ELBOW);
		wrist_ver.write(INIT_WRIST_VER);
		wrist_rot.write(INIT_WRIST_ROT);
		gripper.write(INIT_GRIPPER);

		
		
		step_base = INIT_BASE;
		step_shoulder = INIT_SHOULDER;
		step_elbow = INIT_ELBOW;
		step_wrist_ver = INIT_WRIST_VER;
		step_wrist_rot = INIT_WRIST_ROT;
		step_gripper = INIT_GRIPPER;

		wrist_ver.write(80);
	}

	if(soft_start_level!=SOFT_START_DISABLED)
    		_softStart(soft_start_level);

	// Verifică dacă să execute secvența de demonstrație
	if(demo_enabled == -1) {
		// Folosește setarea din define
		demo_enabled = DEMO_SEQUENCE_ENABLED;
	}
	
	if(demo_enabled == 1) {
		// Așteaptă puțin după inițializare înainte de a începe demo-ul
		delay(1000);
		executeDemoSequence();
	}
	
	return 1;
}

/*
Software implementation of the PWM for the SOFT_START_CONTROL_PIN,HIGH
@param high_time: the time in the logic level high
@param low_time: the time in the logic level low
*/
void _Braccio::_softwarePWM(int high_time, int low_time){
	digitalWrite(SOFT_START_CONTROL_PIN,HIGH);
	delayMicroseconds(high_time);
	digitalWrite(SOFT_START_CONTROL_PIN,LOW);
	delayMicroseconds(low_time); 
}

/*
* This function, used only with the Braccio Shield V4 and greater,
* turn ON the Braccio softly and save it from brokes.
* The SOFT_START_CONTROL_PIN is used as a software PWM
* @param soft_start_level: the minimum value is -70, default value is 0 (SOFT_START_DEFAULT)
*/
void _Braccio::_softStart(int soft_start_level){      
	long int tmp=millis();
	while(millis()-tmp < LOW_LIMIT_TIMEOUT)
		_softwarePWM(80+soft_start_level, 450 - soft_start_level);   //the sum should be 530usec	

	while(millis()-tmp < HIGH_LIMIT_TIMEOUT)
		_softwarePWM(75 + soft_start_level, 430 - soft_start_level); //the sum should be 505usec

	digitalWrite(SOFT_START_CONTROL_PIN,HIGH);
}

/**
 * This functions allow you to control all the servo motors
 * 
 * @param stepDelay The delay between each servo movement
 * @param vBase next base servo motor degree
 * @param vShoulder next shoulder servo motor degree
 * @param vElbow next elbow servo motor degree
 * @param vWrist_ver next wrist rotation servo motor degree
 * @param vWrist_rot next wrist vertical servo motor degree
 * @param vgripper next gripper servo motor degree
 */
int _Braccio::ServoMovement(int stepDelay, int vBase, int vShoulder, int vElbow,int vWrist_ver, int vWrist_rot, int vgripper) {

	// Check values, to avoid dangerous positions for the Braccio
    	if (stepDelay > 30) stepDelay = 30;
	if (stepDelay < 10) stepDelay = 10;
	if (vBase < 0) vBase=0;
	if (vBase > 180) vBase=180;
	if (vShoulder < 15) vShoulder=15;
	if (vShoulder > 165) vShoulder=165;
	if (vElbow < 0) vElbow=0;
	if (vElbow > 180) vElbow=180;
	if (vWrist_ver < 0) vWrist_ver=0;
	if (vWrist_ver > 180) vWrist_ver=180;
	if (vWrist_rot > 180) vWrist_rot=180;
	if (vWrist_rot < 0) vWrist_rot=0;
    	if (vgripper < 6) vgripper = 6;
	if (vgripper > 73) vgripper = 73;

	int exit = 1;

	//Until the all motors are in the desired position
	while (exit) 
	{			
		//For each servo motor if next degree is not the same of the previuos than do the movement		
		if (vBase != step_base) 
		{			
			base.write(step_base);
			//One step ahead
			if (vBase > step_base) {
				step_base++;
			}
			//One step beyond
			if (vBase < step_base) {
				step_base--;
			}
		}

		if (vShoulder != step_shoulder)  
		{
			shoulder.write(step_shoulder);
			//One step ahead
			if (vShoulder > step_shoulder) {
				step_shoulder++;
			}
			//One step beyond
			if (vShoulder < step_shoulder) {
				step_shoulder--;
			}

		}

		if (vElbow != step_elbow)  
		{
			elbow.write(step_elbow);
			//One step ahead
			if (vElbow > step_elbow) {
				step_elbow++;
			}
			//One step beyond
			if (vElbow < step_elbow) {
				step_elbow--;
			}

		}

		if (vWrist_ver != step_wrist_rot) 
		{
			wrist_rot.write(step_wrist_rot);
			//One step ahead
			if (vWrist_ver > step_wrist_rot) {
				step_wrist_rot++;				
			}
			//One step beyond
			if (vWrist_ver < step_wrist_rot) {
				step_wrist_rot--;
			}

		}

		if (vWrist_rot != step_wrist_ver)
		{
			wrist_ver.write(step_wrist_ver);
			//One step ahead
			if (vWrist_rot > step_wrist_ver) {
				step_wrist_ver++;
			}
			//One step beyond
			if (vWrist_rot < step_wrist_ver) {
				step_wrist_ver--;
			}
		}

		if (vgripper != step_gripper)
		{
			gripper.write(step_gripper);
			if (vgripper > step_gripper) {
				step_gripper++;
			}
			//One step beyond
			if (vgripper < step_gripper) {
				step_gripper--;
			}
		}
		
		//delay between each movement
		delay(stepDelay);
		
		//It checks if all the servo motors are in the desired position 
		if ((vBase == step_base) && (vShoulder == step_shoulder)
				&& (vElbow == step_elbow) && (vWrist_ver == step_wrist_rot)
				&& (vWrist_rot == step_wrist_ver) && (vgripper == step_gripper)) {
			step_base = vBase;
			step_shoulder = vShoulder;
			step_elbow = vElbow;
			step_wrist_rot = vWrist_ver;
			step_wrist_ver = vWrist_rot;
			step_gripper = vgripper;
			exit = 0;
		} else {
			exit = 1;
		}
	}
}