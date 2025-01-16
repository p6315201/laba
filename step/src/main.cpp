#include <Arduino.h>
#include <AccelStepper.h>


AccelStepper stepper_1(AccelStepper::DRIVER, 19, 18);

uint32_t lastSendTime = 0;

double degToRad(int degrees);

void setup()
{
  Serial.begin(115200);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);
  stepper_1.setMaxSpeed(1000);
}

void loop()
{ 
  while(Serial.available() == 0){}

  int angle = Serial.parseInt();
  Serial.println(angle);
  double x = sin(degToRad(angle))*200;

  stepper_1.setSpeed(800);
  stepper_1.moveTo((int)x);
  stepper_1.runSpeedToPosition(); 
}

double degToRad(int degrees)
{
  return degrees * (PI / 180);
}
