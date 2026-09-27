#include <Wire.h>
#include <LiquidCrystal.h>

const int MIC_PIN = A0;
const int GREEN_PIN = 3;
const int YELLOW_PIN = 4;
const int RED_PIN = 5;
const unsigned long SAMPLE_WINDOW_MS = 50;

int r5=7;
int en=8;
int d4=9;
int d5=10;
int d6=11;
int d7=12;
LiquidCrystal lcd(r5,en,d4,d5,d6,d7);
String confirmedStatus = "OKAY";
unsigned long statusSeconds = 0;

void setup() {
  Serial.begin(115200);
  pinMode(GREEN_PIN, OUTPUT); pinMode(YELLOW_PIN, OUTPUT); pinMode(RED_PIN, OUTPUT);
  //lcd.init(); lcd.backlight();
  updateTrafficLight("OKAY"); updateLCD("OKAY",0);
  lcd.begin(16,2);
}

int readSoundAmplitude() {
  unsigned long start = millis();
  int signalMin=1023, signalMax=0;
  while (millis()-start < SAMPLE_WINDOW_MS) {
    int sample=analogRead(MIC_PIN);
    if(sample<signalMin) signalMin=sample;
    if(sample>signalMax) signalMax=sample;
  }
  return signalMax-signalMin;
}

void sendSoundData() { Serial.print("DATA:"); Serial.println(readSoundAmplitude()); }

void readPythonCommands() {
  if(!Serial.available()) return;
  String command=Serial.readStringUntil('\n'); command.trim();
  if(!command.startsWith("STATUS:")) return;
  int a=command.indexOf(':'); int b=command.indexOf(':',a+1);
  if(b<0) return;
  confirmedStatus=command.substring(a+1,b);
  statusSeconds=command.substring(b+1).toInt();
  updateTrafficLight(confirmedStatus); updateLCD(confirmedStatus,statusSeconds);
}

void updateTrafficLight(String status) {
  digitalWrite(GREEN_PIN,LOW); digitalWrite(YELLOW_PIN,LOW); digitalWrite(RED_PIN,LOW);
  if(status=="OKAY") digitalWrite(GREEN_PIN,HIGH);
  else if(status=="MODERATE") digitalWrite(YELLOW_PIN,HIGH);
  else if(status=="NOT FINE") digitalWrite(RED_PIN,HIGH);
}

void updateLCD(
  String status,
  unsigned long seconds
) {

  String firstLine = "status: " + status;

  unsigned long minutes = seconds / 60;
  unsigned long remainingSeconds = seconds % 60;

  String secondLine =
    "time: " +
    String(minutes) +
    "m " +
    String(remainingSeconds) +
    "s";

  // Clear first row
  lcd.setCursor(0, 0);
  lcd.print("                ");

  // Clear second row
  lcd.setCursor(0, 1);
  lcd.print("                ");

  // Write first row
  lcd.setCursor(0, 0);
  lcd.print(firstLine);

  // Write second row
  lcd.setCursor(0, 1);
  lcd.print(secondLine);
}

void loop() {
  readPythonCommands();
  sendSoundData();
}
