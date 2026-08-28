#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
// namespaces

namespace Log{
  void err(const char*);
  void log(const char*);
  void logData();
}

template <typename DATA>
class List{

  struct El{
    El* next, *prev;
    DATA* data;
    El():next(nullptr), prev(nullptr), data(nullptr){};
  };

  El* head, *tail;
  int count;

  El* nodeAt(int at){
    if(at < 0 || at >= count){
      String msg = "List::nodeAt - index out of bounds: ";
      msg += at;
      Log::err(msg.c_str());
      return nullptr;
    }
    El* cur = head;
    for(int i = 0; i < at; i++)
      cur = cur->next;
    return cur;
  }

public:

  List():head(nullptr), tail(nullptr), count(0){}

  List(DATA& data):head(nullptr), tail(nullptr), count(0){
    add(data);
  }

  ~List(){
    clear();
  }

  int len(){
    return count;
  }

  bool isEmpty(){
    return count == 0;
  }

  void add(DATA& data){
    El* el = new El();
    el->data = new DATA(data);

    if(head == nullptr){
      head = tail = el;
    }else{
      el->prev = tail;
      tail->next = el;
      tail = el;
    }
    count++;
  }

  void add(DATA& data, int at){
    if(at < 0 || at > count){
      String msg = "List::add - index out of bounds: ";
      msg += at;
      Log::err(msg.c_str());
      return;
    }

    if(at == count){
      add(data); // append, reuses tail logic above
      return;
    }

    El* el = new El();
    el->data = new DATA(data);

    if(at == 0){
      el->next = head;
      head->prev = el;
      head = el;
    }else{
      El* pos = nodeAt(at);
      El* before = pos->prev;

      el->next = pos;
      el->prev = before;
      before->next = el;
      pos->prev = el;
    }
    count++;
  }

  DATA* get(int at){
    El* el = nodeAt(at);
    return el ? el->data : nullptr;
  }

  void remove(int at){
    El* el = nodeAt(at);
    if(el == nullptr) return; // nodeAt already logged the error

    if(el->prev) el->prev->next = el->next;
    else head = el->next;

    if(el->next) el->next->prev = el->prev;
    else tail = el->prev;

    delete el->data;
    delete el;
    count--;
  }

  void clear(){
    El* cur = head;
    while(cur){
      El* next = cur->next;
      delete cur->data;
      delete cur;
      cur = next;
    }
    head = tail = nullptr;
    count = 0;
  }

  void remove(DATA& target){
    El* cur = head;

    while(cur){
      if(*(cur->data) == target){
        if(cur->prev) cur->prev->next = cur->next;
        else head = cur->next;

        if(cur->next) cur->next->prev = cur->prev;
        else tail = cur->prev;

        delete cur->data;
        delete cur;
        count--;
        return;
      }
      cur = cur->next;
    }

    Log::err("List::remove - element not found");
  }
};

namespace TaskScheduler{
  struct Task{
    unsigned long interval;
    unsigned long lastRun;
    int run_count;
    void (*func)();

    Task(){
      interval = lastRun = 0;
      func = nullptr;
      run_count = -1;
    }

    Task(unsigned long _interval, void(*_func)(), int run_count=-1) : interval(_interval), lastRun(millis()), func(_func), run_count(run_count) {}

    int update(unsigned long now){
      int runs = 0;
      if(func != nullptr && (unsigned long)(now - lastRun) >= interval){
        lastRun += interval;
        func();
        runs++;
      }
      return runs;
    }

    bool operator==(const Task& other) const {
      return func == other.func &&
            interval == other.interval &&
            lastRun == other.lastRun &&
            run_count == other.run_count;
    }

  };

  List<Task> Tasks;

  void add_task(void (*func)(), unsigned long interval, int run_count=-1){
    Task t = {interval, func, run_count};
    Tasks.add(t);
  }

  void update(){
    unsigned long now = millis();
    unsigned int task_len = Tasks.len();

    for (unsigned int i = 0; i < task_len; i++){
      Task* cur = Tasks.get(i);
      if(cur == nullptr) continue; // shouldn't happen, but nodeAt logs+bails on bad index

      int runs = cur->update(now);

      if(cur->run_count == -1){
        continue; // infinite task, or it didn't fire this call
      }

      cur->run_count -= runs;
      if(cur->run_count <= 0){
        Tasks.remove(i); // index-based, avoids the operator== ambiguity
        i--;              // list shifted down, recheck this index next iteration
      }
    }
  }

}

namespace Lcd{
  bool lockScreen = false;
  LiquidCrystal_I2C lcd(0x27, 16, 2);
  constexpr int max_screens = 3; // < max_screen
  unsigned int screen=0;
  void prt(const char*, const char*);
  void loadScreen(int);//loads specific screen - cancel if its the same 
  unsigned int getNextScreen();//returns value of next screen
  void processNext(); //gets and loads next screen in order - looping
}

namespace WaterPump{
  bool inUse();
  void set(bool);
  void clean();
  void beginPumpProtocol();
  void stopPumpProtocol();
}

// namespaces for variables + variables

namespace Pins{
  constexpr int BUTTON = 5;

  constexpr int LED_OK = 10;
  constexpr int LED_POOR_WATER = 9;
  constexpr int LED_ERROR = 8;

  constexpr int ULTRASONIC_ECHO = 2;
  constexpr int ULTRASONIC_TRIG = 3;

  constexpr int WATER_PUMP = 4;
}

namespace Dist{
  float distToBottom = 150.0, distToTop = 0.0;
  float getDistanceCm(int, int);
  float getLevel();
  float getLevel(float);
}

#define DHTTYPE DHT11
#define DHTPIN A1

constexpr const unsigned int logIntervalMs = 2000;
String serialBuffer;

// Plain namespace cache of the latest sensor/state values (single instance,
// so no need for a struct+object). Replaces the old global JsonDocument
// "data" variable, which relied on a heap-allocating copy (data = doc;)
// that could silently fail under low SRAM and leave fields as null. Plain
// variables have a fixed size and never allocate, so this can't fail silently.
namespace SensorData{
  bool button=false, okLed=false, poorWaterLed=false, errorLed=false;
  float distance=0;
  int sram=0;
  float outsideTemp=0, outsideHum=0;
}

// classes & structs for sensor or other things 

DHT dht(DHTPIN, DHTTYPE);

struct Dht_var{
  float temperature, humidity;

  Dht_var():temperature(0.0f),humidity(0.0f){}
  
  Dht_var(float t, float h) : temperature(t), humidity(h){}
};

// other function definitions

bool getButton(int);
bool getLedState(int);
void readSerial(void (*)(JsonDocument&));
void serialTask();
void processCommands(JsonDocument&);

Dht_var getTempAndHum(DHT _dht);
int freeSRAM();
void waterPumpButtonCheck();

// essential arduino functions

void setup() {
  Serial.begin(9600);

  pinMode(Pins::BUTTON, INPUT_PULLUP);

  pinMode(Pins::LED_OK, OUTPUT);
  pinMode(Pins::LED_POOR_WATER, OUTPUT);
  pinMode(Pins::LED_ERROR, OUTPUT);

  pinMode(Pins::ULTRASONIC_TRIG, OUTPUT);
  pinMode(Pins::ULTRASONIC_ECHO, INPUT);

  pinMode(Pins::WATER_PUMP, OUTPUT);

  TaskScheduler::add_task(serialTask, 1);
  TaskScheduler::add_task(Log::logData, 1000); // DHT11 needs ~1s between reads
  TaskScheduler::add_task(Lcd::processNext, 3000);
  TaskScheduler::add_task(WaterPump::clean, 20000);
  TaskScheduler::add_task(waterPumpButtonCheck, 50);

  dht.begin();

  Lcd::lcd.init();
  Lcd::lcd.backlight();
  Lcd::prt("CK Ticleni      ", "Starting...     ");
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

float Dist::getDistanceCm(int echoPin, int trigPin){
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

Dht_var getTempAndHum(DHT _dht){
  Dht_var v;
  v.humidity = _dht.readHumidity();
  v.temperature = _dht.readTemperature();

  if(isnan(v.temperature) || isnan(v.humidity)){
    Log::err("Could not read temp or hum.");
    return Dht_var(0, 0);
  }
  return v;
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

  bool btn   = getButton(Pins::BUTTON);
  bool ok    = getLedState(Pins::LED_OK);
  bool poor  = getLedState(Pins::LED_POOR_WATER);
  bool err   = getLedState(Pins::LED_ERROR);
  float dist = Dist::getDistanceCm(Pins::ULTRASONIC_ECHO, Pins::ULTRASONIC_TRIG);
  float level_perc = Dist::getLevel(dist);
  int sram   = freeSRAM();

  Dht_var _dht_data = getTempAndHum(dht);

  doc["buttonPumping"] = btn;
  doc["okLed"] = ok;
  doc["poorWaterLed"] = poor;
  doc["errorLed"] = err;
  doc["distance"] = dist;
  doc["waterLevel"] = level_perc;
  doc["SRAM"] = sram;
  doc["outsideTemp"] = _dht_data.temperature;
  doc["outsideHum"] = _dht_data.humidity;

  // Cache primitives directly into the namespace - plain assignment, no
  // dynamic allocation, so this can never silently fail like the old
  // "data = doc;" JsonDocument copy could under low SRAM.
  SensorData::button = btn;
  SensorData::okLed = ok;
  SensorData::poorWaterLed = poor;
  SensorData::errorLed = err;
  SensorData::distance = dist;
  SensorData::sram = sram;

  // Only overwrite the cached temp/humidity on a successful DHT read, so a
  // failed poll doesn't wipe out the last good value.
  if(!isnan(_dht_data.temperature) && !isnan(_dht_data.humidity)){
    SensorData::outsideTemp = _dht_data.temperature;
    SensorData::outsideHum = _dht_data.humidity;
  }

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

void Lcd::prt(const char* first_row, const char* second_row){
  Lcd::lcd.setCursor(0, 0);
  Lcd::lcd.print(first_row);
  Lcd::lcd.setCursor(0, 1);
  Lcd::lcd.print(second_row);
}

void Lcd::loadScreen(int screen){
  if(screen == (int)Lcd::screen) return; // matches the declared "cancel if same" behavior

  char r1[17], r2[17]; // 16 chars + null terminator, matches 16x2 LCD

  switch(screen){
    case 0:
      Lcd::prt("SMART Kids CLUB ", "WellFlow-Ticleni");
      break;

    case 1:
      Lcd::prt("Water level: --%", "                ");
      break;

    case 2: {
      char tmp[24];

      snprintf(tmp, sizeof(tmp), "Temp: %dC", (int)SensorData::outsideTemp);
      snprintf(r1, sizeof(r1), "%-16.16s", tmp);

      snprintf(tmp, sizeof(tmp), "Umid: %d%%", (int)SensorData::outsideHum);
      snprintf(r2, sizeof(r2), "%-16.16s", tmp);

      Lcd::prt(r1, r2);
      break;
    }

    case 3:
      Lcd::prt("Pumping...      ", " - - - -- - - - ");
      break;

    default:
      Lcd::prt("Error           ", "Unknown screen  ");
  }

  Lcd::screen = screen;
}

unsigned int Lcd::getNextScreen(){
  if(Lcd::max_screens <= Lcd::screen + 1)
    return 0;
  else
    return Lcd::screen + 1;
}

void Lcd::processNext(){
  if(Lcd::lockScreen) return;
  Lcd::loadScreen(Lcd::getNextScreen());
}

bool WaterPump::inUse(){
  return digitalRead(Pins::WATER_PUMP); 
}

void WaterPump::set(bool val){
  digitalWrite(Pins::WATER_PUMP, val?HIGH:LOW);
}

void WaterPump::beginPumpProtocol(){
  if(Lcd::lockScreen) return;
  Lcd::loadScreen(3);
  Lcd::lockScreen = true;
  WaterPump::set(true);
}

void WaterPump::stopPumpProtocol(){
  if(!Lcd::lockScreen) return;
  Lcd::lockScreen = false;
  WaterPump::set(false);
  Lcd::processNext();
}

void WaterPump::clean(){
  WaterPump::beginPumpProtocol();
  TaskScheduler::add_task(WaterPump::stopPumpProtocol, 5000, 1);
}

int freeSRAM() {
    extern int __heap_start, *__brkval;
    int v;
    return (int)&v - (__brkval == 0 ? (int)&__heap_start : (int)__brkval);
}

void waterPumpButtonCheck(){
  if(getButton(Pins::BUTTON))
    WaterPump::beginPumpProtocol();
  else
    WaterPump::stopPumpProtocol();
}

float Dist::getLevel() {
  return ((distToBottom - getDistanceCm(0, 0)) /
    (distToBottom - distToTop)) * 100.0;
}

float Dist::getLevel(float distance) {
  return ((distToBottom - distance) /
    (distToBottom - distToTop)) * 100.0;
}