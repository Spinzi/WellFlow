#include <Arduino.h>
#include <ArduinoJson.h>

// namespaces

namespace Log{
  void err(const char*);
  void log(const char*);
  void logData();
}

// namespaces for variables + variables

namespace Pins{
  constexpr int BUTTON = 5;

  constexpr int LED_OK = 11;
  constexpr int LED_POOR_WATER = 10;
  constexpr int LED_ERROR = 9;
}

constexpr const unsigned int logIntervalMs = 2000;
String serialBuffer;

// other function definitions

bool getButton(int);
bool getLedState(int);
void readSerial(void (*)(JsonDocument&));
void processCommands(JsonDocument&);

// essential arduino functions

void setup() {
  Serial.begin(9600);

  pinMode(Pins::BUTTON, INPUT_PULLUP);

  pinMode(Pins::LED_OK, OUTPUT);
  pinMode(Pins::LED_POOR_WATER, OUTPUT);
  pinMode(Pins::LED_ERROR, OUTPUT);
}

void loop() {
  readSerial(processCommands);
}

// get values functions

bool getButton(int button){
  return !digitalRead(button);
}

bool getLedState(int led){
  return digitalRead(led);
}

// read and process functions

void readSerial(void (*func)(JsonDocument&)){
  while(Serial.available()){
    char c = Serial.read();
    Serial.println(c);
    if (c == '\n') {
        JsonDocument doc;

        if (deserializeJson(doc, serialBuffer) == DeserializationError::Ok) {
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
        }else if(strcmp(led, "led_ok")){
          digitalWrite(Pins::LED_OK, val ? HIGH : LOW);
        }else if(strcmp(led, "led_poor_water")){
          digitalWrite(Pins::LED_POOR_WATER, val ? HIGH : LOW);
        }else if(strcmp(led, "led_err")){
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