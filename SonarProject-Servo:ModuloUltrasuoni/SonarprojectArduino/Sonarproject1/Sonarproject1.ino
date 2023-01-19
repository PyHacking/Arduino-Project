//LiquidCrystal
#include "SR04.h"
#include <LiquidCrystal.h>
#define TRIG_PIN 12
#define ECHO_PIN 13
SR04 sr04 = SR04(ECHO_PIN,TRIG_PIN);
LiquidCrystal lcd(8, 9, 10, 11, 12, 13);

// Includes the Servo library
#include <Servo.h>
// Defines Tirg and Echo pins of the Ultrasonic Sensor
const int trigPin = 7;
const int echoPin = 6;
// Variables for the duration and the distance
long duration;
int distance;
Servo myServo; // Creates a servo object for controlling the servo motor
void setup() {
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT); // Sets the echoPin as an Input
  pinMode(4, OUTPUT); //Red  Led
  pinMode(2, OUTPUT); // Green Led
  Serial.begin(9600);
  myServo.attach(5); // Defines on which pin is the servo motor attached
  lcd.begin(16, 2);
}
void loop() {
  // rotates the servo motor from 15 to 165 degrees
  for(int i=15;i<=165;i++){  
  myServo.write(i);
  delay(100);
  distance = calculateDistance();// Calls a function for calculating the distance measured by the Ultrasonic sensor for each degree
  
  Serial.print(i); // Sends the current degree into the Serial Port
  Serial.print(","); // Sends addition character right next to the previous value needed later in the Processing IDE for indexing
  Serial.print(distance); // Sends the distance value into the Serial Port
  Serial.print("."); // Sends addition character right next to the previous value needed later in the Processing IDE for indexing
  if(distance > 8){
    lcd.print("Target:");
    lcd.setCursor(0, 1);
    lcd.setCursor(1, 2);
    lcd.print(distance);
    lcd.print("cm");
    delay(100);
    lcd.clear();
   }if(distance < 8){
    lcd.clear();
    digitalWrite(4, HIGH);
    digitalWrite(2, LOW);
    lcd.print("Collision:");
    lcd.setCursor(0, 1);
    lcd.setCursor(1, 2);
    lcd.print(distance);
    lcd.print("cm");
    delay(100);
    lcd.clear();
   }else if(distance > 1000){
      lcd.clear();
      lcd.print("Collision:");
      lcd.setCursor(0, 1);
      lcd.setCursor(1, 2);
      lcd.print(distance);
      lcd.print("mm");
      digitalWrite(4, HIGH);
      digitalWrite(2, LOW);
      delay(50);
      digitalWrite(4, LOW);
      digitalWrite(2, LOW);
      delay(50);
      digitalWrite(4, HIGH);
      digitalWrite(2, LOW);     
      delay(100);
    }else{
       digitalWrite(2, HIGH);
       digitalWrite(4, LOW);
    }
 }
  
  // Repeats the previous lines from 165 to 15 degrees
  for(int i=165;i>15;i--){  
  myServo.write(i);
  delay(100);
  distance = calculateDistance();
  Serial.print(i);
  Serial.print(",");
  Serial.print(distance);
  Serial.print(".");
  if(distance > 8){
    lcd.print("Target:");
    lcd.setCursor(0, 1);
    lcd.setCursor(1, 2);
    lcd.print(distance);
    lcd.print("cm");
    delay(100);
    lcd.clear();
  }if(distance < 8){
    lcd.clear();
    digitalWrite(4, HIGH);
    digitalWrite(2, LOW);
    lcd.print("Collision:");
    lcd.setCursor(0, 1);
    lcd.setCursor(1, 2);
    lcd.print(distance);
    lcd.print("cm");
    delay(100);
    lcd.clear();
    }else{
       digitalWrite(2, HIGH);
       digitalWrite(4, LOW);
    }
  }
  
 }
// Function for calculating the distance measured by the Ultrasonic sensor
int calculateDistance(){ 
  digitalWrite(trigPin, LOW); 
  delayMicroseconds(100);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH); 
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH); // Reads the echoPin, returns the sound wave travel time in microseconds
  distance= duration*0.034/2;
  return distance;
}
