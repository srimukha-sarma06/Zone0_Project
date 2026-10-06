/*
 * Modulino Thermo - Temperature Humidity Matrix
 *
 * This example code is in the public domain. 
 * Copyright (c) 2025 Arduino
 * SPDX-License-Identifier: MPL-2.0
 */



// 2* flag motor band chalu
// temp sab band buzzer chalu new tone





#include <Arduino_Modulino.h>
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

ModulinoThermo thermo;
ModulinoBuzzer buzzer;
ArduinoLEDMatrix matrix;

float temperature = -273.15;

// Melody notes
int temp_alert[]  = {523, 659, 523, 659, 523, 0, 784, 523};
int motor_flag[]  = {262, 196, 196, 220, 196, 0, 247, 262};

// Machine pins
const int machine1 = 9;
const int machine2 = 10;
const int machine3 = 11;
const int button1 = 2;
const int button2 = 3;
const int button3 = 4 ;


bool machine1state = HIGH;
bool machine2state = HIGH;
bool machine3state = HIGH;

// -------------------------------------------------

void playMelody(int *melody) {
  for (int i = 0; i < 8; i++) {
    buzzer.tone(melody[i], 250);
    delay(250);
  }
}

// -------------------------------------------------

void setup() {
  Serial.begin(9600);
  Monitor.begin(9600);

  Modulino.begin();
  thermo.begin();
  buzzer.begin();
  matrix.begin();

  pinMode(machine1, OUTPUT);
  pinMode(machine2, OUTPUT);
  pinMode(machine3, OUTPUT);

  digitalWrite(machine1, HIGH);
  digitalWrite(machine2, HIGH);
  digitalWrite(machine3, HIGH);
  pinMode(button1, INPUT_PULLUP);
  pinMode(button2, INPUT_PULLUP);
  pinMode(button3, INPUT_PULLUP);

  delay(100);
}

// -------------------------------------------------

void loop() {

  // Read temperature
  temperature = thermo.getTemperature();
  String temperature_text = String(temperature, 1) + "°C";

  Serial.print("T:");
  Serial.println(temperature, 1);

  // ---------- Over-temperature protection ----------

  // ---------- LED Matrix Display ----------
  matrix.beginDraw();
  matrix.stroke(0xFFFFFFFF);
  matrix.textScrollSpeed(75);
  matrix.textFont(Font_5x7);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println(" " + temperature_text + " ");
  matrix.endText(SCROLL_LEFT);
  matrix.endDraw();

  // ---------- Serial Commands ----------
  if (Monitor.available()) {
    String cmd = Monitor.readStringUntil('\n');
    cmd.trim();

    if (cmd == "STOP_M1") {
        machine1state = LOW;
        digitalWrite(machine1, LOW);
        Monitor.println("Motor 1 OFF");
        playMelody(motor_flag);
    }
    else if (cmd == "STOP_M2") {
        machine2state = LOW;
        digitalWrite(machine2, LOW);
        Monitor.println("Motor 2 OFF");
        playMelody(motor_flag);
    }
    else if (cmd == "STOP_M3") {
        machine3state = LOW;
        digitalWrite(machine3, LOW);
        Monitor.println("Motor 3 OFF");
        playMelody(motor_flag);
    }
    else if (cmd == "FIRE") {
        if (temperature > 50.0) {
            machine1state = LOW;
            machine2state = LOW;
            machine3state = LOW;
    
            digitalWrite(machine1, LOW);
            digitalWrite(machine2, LOW);
            digitalWrite(machine3, LOW);
    
            Monitor.println("FIRE CONFIRMED - MACHINES OFF");
            playMelody(temp_alert);
        }
    }
    else {
        Monitor.println("Invalid command");
    }
  }
  int pressed = 0;

  if (digitalRead(button1) == LOW) pressed = 1;
  if (digitalRead(button2) == LOW) pressed = 2;
  if (digitalRead(button3) == LOW) pressed = 3;

  switch (pressed) {
    case 1:
      Monitor.println("Button 1 pressed");
      digitalWrite(machine1, HIGH);
      machine1state = HIGH;      
      break;

    case 2:
      Monitor.println("Button 2 pressed");
      digitalWrite(machine2, HIGH);
      machine2state = HIGH;
      break;

    case 3:
      Monitor.println("Button 3 pressed");
      digitalWrite(machine3, HIGH);
      machine3state = HIGH;
      break;

    default:
      // No button pressed
      break;
  }

  // delay(200);

  
}




//For admin match case kar sakte he for saare buttons assign ho jayenge uss button daba to uske according waali machine chalu


// int flag(//get web/){
//   int type =0;
//   //update type from web ui
//   return type;
// }
// int admin_flag_release(){
//   type=0;
//   return type;
// }

// void status(){

//   switch(flag){
//     case 1:
//     digitalWrite()
//   }
// }
