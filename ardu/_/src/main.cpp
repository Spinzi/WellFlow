#include <Arduino.h>
#include <ArduinoJson.h>
// namespaces

namespace Log{
  void err(const char*);
  void log(const char*);
  void logData();
}


namespace TaskScheduler{
  struct Task{
    unsigned long interval;
    unsigned long lastRun;
    void (*func)();

    Task(){
      interval = lastRun = 0;
      func = nullptr;
    }

    Task(unsigned long _interval, void(*_func)()) : interval(_interval), lastRun(0), func(_func) {}

    void update(unsigned long now){
      if(func != nullptr && lastRun + interval <= now){
        lastRun = now;
        func();
      }
    }

  };

  constexpr int max_count = 16;
  Task Tasks[max_count];
  unsigned int count = 0;


  void add_task(void (*func)(), unsigned long interval){
    Tasks[count++] = {interval, func};
  }

  void update(){
    unsigned long now = millis();
    for (unsigned int i = 0; i < count; i++)
      Tasks[i].update(now);
  }

}

// namespaces for variables + variables

namespace Pins{
  constexpr int BUTTON = 5;

  constexpr int LED_OK = 10;
  constexpr int LED_POOR_WATER = 9;
  constexpr int LED_ERROR = 8;
  constexpr int ULTRASONIC_ECHO = 2;
  constexpr int ULTRASONIC_TRIG = 3;
}

constexpr const unsigned int logIntervalMs = 2000;
String serialBuffer;

// other function definitions

bool getButton(int);
bool getLedState(int);
void readSerial(void (*)(JsonDocument&));
void serialTask();
void processCommands(JsonDocument&);
float getDistanceCm(int, int);

// essential arduino functions

void setup() {
  Serial.begin(9600);

  pinMode(Pins::BUTTON, INPUT_PULLUP);

  pinMode(Pins::LED_OK, OUTPUT);
  pinMode(Pins::LED_POOR_WATER, OUTPUT);
  pinMode(Pins::LED_ERROR, OUTPUT);

  pinMode(Pins::ULTRASONIC_TRIG, OUTPUT);
  pinMode(Pins::ULTRASONIC_ECHO, INPUT);

  TaskScheduler::add_task(serialTask, 1);
  TaskScheduler::add_task(Log::logData, 500);
}

void loop() {
  TaskScheduler::update();
}

// get values functions

bool getButton(int button){
  return !digitalRead(button);
}

bool getLedState(int led){
  return digitalRead(led);
}

float getDistanceCm(int echoPin, int trigPin){
  float duration, distance;
  
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  duration = pulseIn(echoPin, HIGH);  
  distance = (duration*.0343)/2; 
  return distance;
}

// read and process functions

void readSerial(void (*func)(JsonDocument&)){
  while(Serial.available()){
    char c = Serial.read();
    if (c == '\n') {
      JsonDocument doc;

      if (deserializeJson(doc, serialBuffer) == DeserializationError::Ok) {
        Log::log("Received Serial.");
        func(doc);
      } else {
        Log::err("Invalid JSON");
      }

      serialBuffer = "";
    }
    else {
        serialBuffer += c;
    }
  }
}

void serialTask(){
  readSerial(processCommands);
}

void processCommands(JsonDocument &doc){
  if(!doc.is<JsonArray>()){
    Log::err("Read JSON object is not an array.");
    return;
  }

  JsonArray arr = doc.as<JsonArray>();

  for(JsonObject obj : arr){
    const char* type = obj["type"];
    if(type == nullptr){
      Log::err("Missing type");
    }else if (strcmp(type, "command") == 0){

      const char* cmd = obj["command"];

      if(cmd == nullptr){
        Log::err("Missing command");
      }else if(strcmp(cmd, "set_led") == 0){
        //leds are - led_ok, led_poor_water, led_err

        const char* led = obj["led"];

        if(!obj["value"].is<bool>()){
          Log::err("Value is not a bool in led command.");
          continue;
        }

        bool val = obj["value"];

        if(led == nullptr){
          Log::err("Missing led");
        }else if(strcmp(led, "led_ok") == 0){
          digitalWrite(Pins::LED_OK, val ? HIGH : LOW);
        }else if(strcmp(led, "led_poor_water") == 0){
          digitalWrite(Pins::LED_POOR_WATER, val ? HIGH : LOW);
        }else if(strcmp(led, "led_err") == 0){
          digitalWrite(Pins::LED_ERROR, val ? HIGH : LOW);
        }else{
          String msg ="Unknown led:";
          msg += led;
          Log::err(msg.c_str());
        }

      }else{
        String msg = "Unknown command:";
        msg += cmd;
        Log::err(msg.c_str());
      }

    }else{
      String msg = "Unknown type:";
      msg += type;
      Log::err(msg.c_str());
    }
  }
}

// log namespace functions

void Log::logData(){

  JsonDocument doc;

  doc["type"] = "data";

  doc["button"] = getButton(Pins::BUTTON);
  doc["okLed"] = getLedState(Pins::LED_OK);
  doc["poorWaterLed"] = getLedState(Pins::LED_POOR_WATER);
  doc["errorLed"] = getLedState(Pins::LED_ERROR);
  doc["distance"] = getDistanceCm(Pins::ULTRASONIC_ECHO, Pins::ULTRASONIC_TRIG);

  serializeJson(doc, Serial);
  Serial.println();
}

void Log::log(const char* msg){
  JsonDocument doc;
  doc["type"] = "message";
  doc["message"] = msg;

  serializeJson(doc, Serial);
  Serial.println();
}

void Log::err(const char* err){
  JsonDocument doc;
  doc["type"] = "err";
  doc["err"] = err;

  serializeJson(doc, Serial);
  Serial.println();
}