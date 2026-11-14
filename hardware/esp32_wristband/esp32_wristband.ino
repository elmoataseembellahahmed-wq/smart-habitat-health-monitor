// NABD wristband prototype for ESP32 (Arduino framework).
//
// STATUS: written for the hardware step of the roadmap; NOT YET TESTED ON A BOARD.
// The server side it talks to (/api/ingest) is implemented and tested.
//
// Sends heart rate, SpO2 and skin temperature every 60 s to the on-board NABD server
// (run_offline.py) as JSON with this device's ID and its own timestamp:
//   {"device_id":"WB-B","timestamp":1794650000,"readings":{"heart_rate":64,"spo2":97.8,"body_temp":36.6}}
// If Wi-Fi is down, samples wait in a ring buffer and are sent later in one batch; the
// server files late samples on the day they were measured and drops duplicates.
//
// Parts: ESP32 dev board, MAX30102 (pulse + SpO2, I2C), MLX90614 or DS18B20 (temperature).
// Libraries: SparkFun MAX3010x, Adafruit MLX90614, ArduinoJson.

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <time.h>
#include <ArduinoJson.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include <Adafruit_MLX90614.h>

const char* WIFI_SSID   = "HABITAT-NET";                       // set for your network
const char* WIFI_PASS   = "change-me";
const char* SERVER_URL  = "http://192.168.1.10:8000/api/ingest"; // the computer running run_offline.py
const char* DEVICE_ID   = "WB-B";                              // must be paired with an astronaut on the server
const uint32_t PERIOD_MS = 60000;

MAX30105 pulse;
Adafruit_MLX90614 thermo;

struct Sample { uint32_t ts; float hr; float spo2; float temp; bool hrOk; bool spo2Ok; };
const int BUF = 240;                 // 4 hours of samples kept while offline
Sample buf[BUF];
int head = 0, count = 0;

void push(const Sample& s) { buf[(head + count) % BUF] = s; if (count < BUF) count++; else head = (head + 1) % BUF; }

bool readVitals(Sample& s) {
  // 100 samples of red/IR light, then the SparkFun SpO2 + heart-rate algorithm.
  static uint32_t ir[100], red[100];
  for (int i = 0; i < 100; i++) {
    while (!pulse.available()) pulse.check();
    red[i] = pulse.getRed(); ir[i] = pulse.getIR(); pulse.nextSample();
  }
  int32_t spo2, hr; int8_t spo2Valid, hrValid;
  maxim_heart_rate_and_oxygen_saturation(ir, 100, red, &spo2, &spo2Valid, &hr, &hrValid);
  s.hr = hr; s.spo2 = spo2; s.hrOk = hrValid; s.spo2Ok = spo2Valid;
  s.temp = thermo.readObjectTempC();
  return true;
}

bool sendBuffer() {
  if (count == 0 || WiFi.status() != WL_CONNECTED) return false;
  JsonDocument doc;                                  // a JSON array of messages
  JsonArray arr = doc.to<JsonArray>();
  int n = min(count, 50);                            // send at most 50 per request
  for (int i = 0; i < n; i++) {
    const Sample& s = buf[(head + i) % BUF];
    JsonObject m = arr.add<JsonObject>();
    m["device_id"] = DEVICE_ID;
    m["timestamp"] = s.ts;
    JsonObject r = m["readings"].to<JsonObject>();
    if (s.hrOk) r["heart_rate"] = s.hr;              // invalid readings are left out, never guessed
    if (s.spo2Ok) r["spo2"] = s.spo2;
    r["body_temp"] = s.temp;                         // wrist skin temperature (an estimate)
  }
  String body; serializeJson(doc, body);
  HTTPClient http; http.begin(SERVER_URL); http.addHeader("Content-Type", "application/json");
  int code = http.POST(body); http.end();
  if (code == 200) { head = (head + n) % BUF; count -= n; return true; }
  return false;                                      // keep the samples and try again later
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  pulse.begin(Wire, I2C_SPEED_FAST); pulse.setup();
  thermo.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  configTime(0, 0, "pool.ntp.org");                  // on a spacecraft: the vehicle's time server
}

void loop() {
  static uint32_t last = 0;
  if (millis() - last >= PERIOD_MS) {
    last = millis();
    Sample s; s.ts = (uint32_t)time(nullptr);
    if (s.ts > 1700000000 && readVitals(s)) push(s);  // no valid clock yet = no timestamped sample
    while (sendBuffer()) {}
  }
}
