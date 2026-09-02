// CueLoop deterministic physical-cue controller for the UNO Q STM32U585.

#include <Arduino.h>
#include <Arduino_RouterBridge.h>

#include "cue_controller_hardware.h"

namespace {

constexpr uint32_t kLinuxHeartbeatTimeoutMs = 6000;
constexpr uint32_t kStatusNotifyIntervalMs = 5000;
constexpr uint32_t kDebounceMs = 35;
constexpr size_t kMaximumEventIdLength = 64;

enum EventClass : int {
  kDoorKnock = 1,
  kAlarmBeep = 2,
  kDogBark = 3,
  kAttentionCall = 4,
};

struct CueState {
  String event_id;
  int class_code = 0;
  int priority = 0;
  int confidence_permille = 0;
  bool active = false;
  bool muted = false;
  uint32_t started_ms = 0;
};

CueState cue;
bool bridge_ready = false;
bool linux_healthy = false;
uint32_t last_linux_heartbeat_ms = 0;
uint32_t last_status_notify_ms = 0;
uint32_t accepted_cues = 0;
uint32_t rejected_cues = 0;
uint32_t button_acknowledgements = 0;
bool last_button_reading = HIGH;
bool stable_button_state = HIGH;
uint32_t last_button_change_ms = 0;

void setLed3(uint8_t red, uint8_t green, uint8_t blue) {
  // UNO Q LED3 PWM polarity is declared inverted by the official board core;
  // the documented API accepts 0=off, 255=full for each color.
  analogWrite(LED3_R, red);
  analogWrite(LED3_G, green);
  analogWrite(LED3_B, blue);
}

void setLed4(bool red, bool green, bool blue) {
  // LED4 is active low.
  digitalWrite(LED4_R, red ? LOW : HIGH);
  digitalWrite(LED4_G, green ? LOW : HIGH);
  digitalWrite(LED4_B, blue ? LOW : HIGH);
}

bool validClassCode(int class_code) {
  return class_code >= kDoorKnock && class_code <= kAttentionCall;
}

bool startCue(String event_id, int class_code, int priority, int confidence_permille) {
  if (event_id.isEmpty() || event_id.length() > kMaximumEventIdLength ||
      !validClassCode(class_code) || priority < 1 || priority > 3 ||
      confidence_permille < 0 || confidence_permille > 1000) {
    rejected_cues++;
    return false;
  }
  cue.event_id = event_id;
  cue.class_code = class_code;
  cue.priority = priority;
  cue.confidence_permille = confidence_permille;
  cue.active = true;
  cue.started_ms = millis();
  accepted_cues++;
  return true;
}

bool clearCue(String event_id) {
  if (!cue.active) {
    return true;
  }
  if (!event_id.isEmpty() && event_id != cue.event_id) {
    return false;
  }
  cue.active = false;
  cue.event_id = "";
  setLed3(0, 0, 0);
#if CUELOOP_HAPTIC_PIN >= 0
  digitalWrite(CUELOOP_HAPTIC_PIN, LOW);
#endif
#if CUELOOP_BUZZER_PIN >= 0
  noTone(CUELOOP_BUZZER_PIN);
#endif
  return true;
}

bool setMuted(bool muted) {
  cue.muted = muted;
  if (muted) {
    setLed3(0, 0, 0);
  }
  return cue.muted;
}

uint32_t linuxHeartbeat(uint32_t /* linux_uptime_ms */) {
  last_linux_heartbeat_ms = millis();
  linux_healthy = true;
  return millis();
}

String controllerStatus() {
  String result = "v1;bridge=";
  result += bridge_ready ? "ready" : "down";
  result += ";linux=";
  result += linux_healthy ? "healthy" : "timeout";
  result += ";active=";
  result += cue.active ? "yes" : "no";
  result += ";muted=";
  result += cue.muted ? "yes" : "no";
  result += ";accepted=";
  result += accepted_cues;
  result += ";rejected=";
  result += rejected_cues;
  result += ";button_acks=";
  result += button_acknowledgements;
  return result;
}

bool cuePulseOn(uint32_t elapsed_ms, int priority) {
  if (priority == 3) {
    const uint32_t phase = elapsed_ms % 1400;
    return phase < 180 || (phase >= 300 && phase < 480) ||
           (phase >= 600 && phase < 780);
  }
  if (priority == 2) {
    const uint32_t phase = elapsed_ms % 1800;
    return phase < 220 || (phase >= 420 && phase < 640);
  }
  return elapsed_ms % 2200 < 300;
}

void classColor(int class_code, uint8_t brightness, uint8_t& red, uint8_t& green,
                uint8_t& blue) {
  red = 0;
  green = 0;
  blue = 0;
  switch (class_code) {
    case kDoorKnock:
      green = static_cast<uint8_t>(brightness * 3 / 4);
      blue = brightness;
      break;
    case kAlarmBeep:
      red = brightness;
      break;
    case kDogBark:
      red = static_cast<uint8_t>(brightness / 4);
      green = static_cast<uint8_t>(brightness / 3);
      blue = brightness;
      break;
    case kAttentionCall:
      red = brightness;
      green = static_cast<uint8_t>(brightness / 2);
      break;
    default:
      red = brightness;
      green = brightness;
      blue = brightness;
      break;
  }
}

void updateCueOutputs() {
  if (!cue.active || cue.muted) {
    setLed3(0, 0, 0);
#if CUELOOP_HAPTIC_PIN >= 0
    digitalWrite(CUELOOP_HAPTIC_PIN, LOW);
#endif
#if CUELOOP_BUZZER_PIN >= 0
    noTone(CUELOOP_BUZZER_PIN);
#endif
    return;
  }
  const bool pulse_on = cuePulseOn(millis() - cue.started_ms, cue.priority);
  if (!pulse_on) {
    setLed3(0, 0, 0);
#if CUELOOP_HAPTIC_PIN >= 0
    digitalWrite(CUELOOP_HAPTIC_PIN, LOW);
#endif
#if CUELOOP_BUZZER_PIN >= 0
    noTone(CUELOOP_BUZZER_PIN);
#endif
    return;
  }
  const uint8_t brightness = static_cast<uint8_t>(
      64 + static_cast<uint32_t>(cue.confidence_permille) * 191 / 1000);
  uint8_t red = 0;
  uint8_t green = 0;
  uint8_t blue = 0;
  classColor(cue.class_code, brightness, red, green, blue);
  setLed3(red, green, blue);
#if CUELOOP_HAPTIC_PIN >= 0
  digitalWrite(CUELOOP_HAPTIC_PIN, HIGH);
#endif
#if CUELOOP_BUZZER_PIN >= 0
  tone(CUELOOP_BUZZER_PIN, cue.priority == 3 ? 1800 : 1200);
#endif
}

void updateHealthLed() {
  if (!bridge_ready || !linux_healthy) {
    const bool on = millis() % 1000 < 400;
    setLed4(on, false, false);
    return;
  }
  if (cue.muted) {
    setLed4(false, false, true);
    return;
  }
  setLed4(false, true, false);
}

void acknowledgeFromButton() {
  if (!cue.active) {
    return;
  }
  const String event_id = cue.event_id;
  clearCue(event_id);
  button_acknowledgements++;
  if (bridge_ready) {
    Bridge.notify("cueloop/ack", event_id);
  }
}

void pollButton() {
  const bool reading = digitalRead(CUELOOP_ACK_BUTTON_PIN);
  if (reading != last_button_reading) {
    last_button_change_ms = millis();
    last_button_reading = reading;
  }
  if (millis() - last_button_change_ms >= kDebounceMs &&
      reading != stable_button_state) {
    stable_button_state = reading;
    if (stable_button_state == LOW) {
      acknowledgeFromButton();
    }
  }
}

}  // namespace

void setup() {
  pinMode(LED3_R, OUTPUT);
  pinMode(LED3_G, OUTPUT);
  pinMode(LED3_B, OUTPUT);
  pinMode(LED4_R, OUTPUT);
  pinMode(LED4_G, OUTPUT);
  pinMode(LED4_B, OUTPUT);
  pinMode(CUELOOP_ACK_BUTTON_PIN, INPUT_PULLUP);
#if CUELOOP_HAPTIC_PIN >= 0
  pinMode(CUELOOP_HAPTIC_PIN, OUTPUT);
  digitalWrite(CUELOOP_HAPTIC_PIN, LOW);
#endif
#if CUELOOP_BUZZER_PIN >= 0
  pinMode(CUELOOP_BUZZER_PIN, OUTPUT);
#endif
  setLed3(0, 0, 0);
  setLed4(false, false, false);

  bridge_ready = Bridge.begin();
  if (bridge_ready) {
    Bridge.provide_safe("cueloop/cue", startCue);
    Bridge.provide_safe("cueloop/clear", clearCue);
    Bridge.provide_safe("cueloop/mute", setMuted);
    Bridge.provide_safe("cueloop/heartbeat", linuxHeartbeat);
    Bridge.provide_safe("cueloop/status", controllerStatus);
    Monitor.begin(115200);
    Monitor.println("CUELOOP_MCU_READY firmware=1 bridge=ready");
  }
  last_linux_heartbeat_ms = millis();
}

void loop() {
  if (linux_healthy && millis() - last_linux_heartbeat_ms > kLinuxHeartbeatTimeoutMs) {
    linux_healthy = false;
  }
  pollButton();
  updateCueOutputs();
  updateHealthLed();

  if (bridge_ready && millis() - last_status_notify_ms >= kStatusNotifyIntervalMs) {
    last_status_notify_ms = millis();
    Bridge.notify(
        "cueloop/mcu_status",
        millis(),
        linux_healthy,
        cue.active,
        cue.muted,
        accepted_cues,
        rejected_cues,
        button_acknowledgements);
  }
  delay(5);
}
