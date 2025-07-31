#include <Adafruit_MAX31855.h>
#include <Arduino.h>

// Pin definitions
const int MUX_S0 = 2;
const int MUX_S1 = 3;
const int MUX_S2 = 4;
const int MUX_S3 = 5;
const int MAXDO = 12;
const int MAXCS = 10;
const int MAXCLK = 13;

Adafruit_MAX31855 thermocouple(MAXCLK, MAXCS, MAXDO);

// Configuration parameters
int numChannels = 3;           // Default: 3 channels
int numSamples = 10;            // Default: 10 samples
unsigned long sampleIntervalMs = 1000;  // Default: 1 second
bool isLogging = false;        // Default: not logging

unsigned long lastSampleTime = 0;
String inputBuffer = "";

void setMuxChannel(int channel) {
  digitalWrite(MUX_S0, channel & 0x01);
  digitalWrite(MUX_S1, (channel >> 1) & 0x01);
  digitalWrite(MUX_S2, (channel >> 2) & 0x01);
  digitalWrite(MUX_S3, (channel >> 3) & 0x01);
  delayMicroseconds(10);
}

void readTemperatures(double* temperatures) {
  for (int ch = 1; ch < numChannels + 1; ch++) {
    setMuxChannel(ch);
    delay(100);  // Let MUX settle

    double sum = 0;
    int validSamples = 0;

    for (int s = 0; s < numSamples; s++) {
      double temp = thermocouple.readCelsius();
      if (!isnan(temp)) {
        sum += temp;
        validSamples++;
      }
      delay(20);
    }

    if (validSamples > 0) {
      temperatures[ch] = sum / validSamples;
    } else {
      temperatures[ch] = NAN;  // All readings failed
    }
  }
}

void printTemperatures(double* temperatures) {
  for (int ch = 1; ch < numChannels + 1; ch++) {
    Serial.print(temperatures[ch], 2);
    if (ch < numChannels) Serial.print(",");
  }
  Serial.println();
}

void processCommand(String command) {
  command.trim();
  command.toUpperCase();
  
  if (command == "START") {
    isLogging = true;
    lastSampleTime = millis();
    Serial.println("START OK");
  }
  else if (command == "STOP") {
    isLogging = false;
    Serial.println("STOP OK");
  }
  else if (command == "ACQUIRE") {
    double temperatures[numChannels];
    readTemperatures(temperatures);
    Serial.print("TEMP: ");
    printTemperatures(temperatures);
  }
  else if (command == "STATUS") {
    Serial.print("STATUS: Rate=");
    Serial.print(sampleIntervalMs / 1000);
    Serial.print(",Channels=");
    Serial.print(numChannels);
    Serial.print(",Samples=");
    Serial.print(numSamples);
    Serial.print(",Active=");
    Serial.println(isLogging ? "true" : "false");
  }
  else if (command == "RESET") {
    numChannels = 3;
    numSamples = 10;
    sampleIntervalMs = 1000;
    isLogging = false;
    Serial.println("RESET OK");
  }
  else if (command.startsWith("RATE ")) {
    int rate = command.substring(5).toInt();
    if (rate >= 1 && rate <= 255) {
      sampleIntervalMs = rate * 1000;
      Serial.println("RATE OK");
    } else {
      Serial.println("RATE ERROR: Invalid rate (1-255 seconds)");
    }
  }
  else if (command.startsWith("CHANNELS ")) {
    int channels = command.substring(9).toInt();
    if (channels >= 1 && channels <= 12) {
      numChannels = channels;
      Serial.println("CHANNELS OK");
    } else {
      Serial.println("CHANNELS ERROR: Invalid channels (1-12)");
    }
  }
  else if (command.startsWith("SAMPLES ")) {
    int samples = command.substring(8).toInt();
    if (samples >= 1 && samples <= 20) {
      numSamples = samples;
      Serial.println("SAMPLES OK");
    } else {
      Serial.println("SAMPLES ERROR: Invalid samples (1-20)");
    }
  }
  else if (command.length() > 0) {
    Serial.println("ERROR: Unknown command");
  }
}

void setup() {
  Serial.begin(9600);
  
  // Configure multiplexer control pins
  pinMode(MUX_S0, OUTPUT);
  pinMode(MUX_S1, OUTPUT);
  pinMode(MUX_S2, OUTPUT);
  pinMode(MUX_S3, OUTPUT);

  Serial.println("Multi-Channel Thermocouple Logger Ready");
  Serial.println("Commands: START, STOP, ACQUIRE, RATE, CHANNELS, SAMPLES, STATUS, RESET");
  delay(500);
}

void loop() {
  // Handle serial commands
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }

  // Handle continuous logging
  if (isLogging && (millis() - lastSampleTime >= sampleIntervalMs)) {
    lastSampleTime = millis();
    
    double temperatures[numChannels];
    readTemperatures(temperatures);
    printTemperatures(temperatures);
  }
}
