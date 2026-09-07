// CueLoop CuePod firmware for Seeed Studio XIAO ESP32S3 Sense.
// Raw microphone samples are packetized in RAM and never written to storage.

#include <Arduino.h>
#include <errno.h>
#include <ESP_I2S.h>
#include <Preferences.h>
#include <WiFi.h>
#include <lwip/sockets.h>

#include "cuepod_hardware.h"
#include "cuepod_protocol.h"

namespace {

constexpr uint16_t kDefaultReceiverPort = 57321;
constexpr uint32_t kFrameDurationUs = 20000;
constexpr uint32_t kReceiverTimeoutMs = 5000;
constexpr uint32_t kDiagnosticsIntervalMs = 5000;
constexpr uint32_t kMinimumWifiRetryMs = 1000;
constexpr uint32_t kMaximumWifiRetryMs = 30000;
constexpr uint32_t kMinimumReceiverRetryMs = 500;
constexpr uint32_t kMaximumReceiverRetryMs = 5000;
constexpr int32_t kReceiverConnectTimeoutMs = 250;
constexpr uint32_t kTcpWriteTimeoutMs = 250;
constexpr size_t kStreamPrefixBytes = 2;
constexpr size_t kAckFrameBytes = kStreamPrefixBytes + cueloop::kAckBytes;
constexpr size_t kMaximumSerialCommand = 196;

struct Counters {
  uint32_t captured_frames = 0;
  uint32_t sent_frames = 0;
  uint32_t send_failures = 0;
  uint32_t capture_errors = 0;
  uint32_t wifi_attempts = 0;
  uint32_t wifi_reconnects = 0;
  uint32_t receiver_connect_attempts = 0;
  uint32_t receiver_reconnects = 0;
  uint32_t valid_acks = 0;
  uint32_t bad_acks = 0;
  uint32_t receiver_timeouts = 0;
  uint32_t clipped_samples = 0;
};

Preferences preferences;
I2SClass i2s;
WiFiClient receiver_client;
Counters counters;
String wifi_ssid;
String wifi_password;
IPAddress receiver_ip(192, 168, 1, 2);
uint16_t receiver_port = kDefaultReceiverPort;
uint32_t pod_id = 1;
bool usb_powered_mode = true;
bool streaming_enabled = true;
bool test_tone_enabled = false;
bool microphone_ready = false;
bool receiver_connection_active = false;
bool had_receiver_connection = false;
bool receiver_reachable = false;
bool receiver_timeout_reported = false;
bool was_wifi_connected = false;
uint8_t restart_frames_remaining = 3;
uint32_t sequence_number = 0;
uint64_t sample_clock = 0;
uint32_t last_wifi_attempt_ms = 0;
uint32_t wifi_retry_ms = kMinimumWifiRetryMs;
uint32_t last_receiver_attempt_ms = 0;
uint32_t receiver_retry_ms = kMinimumReceiverRetryMs;
uint32_t last_ack_ms = 0;
uint32_t last_diagnostics_ms = 0;
uint32_t next_test_frame_us = 0;
uint16_t last_audio_rms = 0;
uint16_t last_audio_peak = 0;
String serial_line;
int16_t samples[cueloop::kSamplesPerFrame];
uint8_t datagram[cueloop::kDatagramBytes];
uint8_t ack_frame[kAckFrameBytes];
size_t ack_frame_used = 0;

uint32_t defaultPodId() {
  const uint64_t efuse = ESP.getEfuseMac();
  uint32_t folded = static_cast<uint32_t>(efuse) ^ static_cast<uint32_t>(efuse >> 32);
  folded ^= 0xC0E10000u;
  return folded == 0 ? 1 : folded;
}

void beginNewStream() {
  sequence_number = 0;
  sample_clock = 0;
  restart_frames_remaining = 3;
}

void closeReceiverConnection(bool announce) {
  if (receiver_connection_active && announce) {
    Serial.println("RECEIVER_DISCONNECTED");
  }
  receiver_client.stop();
  receiver_connection_active = false;
  receiver_reachable = false;
  ack_frame_used = 0;
  beginNewStream();
}

void loadConfiguration() {
  preferences.begin("cueloop", false);
  wifi_ssid = preferences.getString("ssid", "");
  wifi_password = preferences.getString("password", "");
  String ip_text = preferences.getString("receiver_ip", "192.168.1.2");
  if (!receiver_ip.fromString(ip_text)) {
    receiver_ip.fromString("192.168.1.2");
  }
  receiver_port = preferences.getUShort("receiver_port", kDefaultReceiverPort);
  if (receiver_port == 0) {
    receiver_port = kDefaultReceiverPort;
  }
  pod_id = preferences.getULong("pod_id", defaultPodId());
  if (pod_id == 0) {
    pod_id = defaultPodId();
  }
  usb_powered_mode = preferences.getBool("usb_mode", true);
  streaming_enabled = preferences.getBool("streaming", true);
  test_tone_enabled = preferences.getBool("test_tone", false);
}

void startWifiAttempt() {
  if (wifi_ssid.isEmpty()) {
    return;
  }
  closeReceiverConnection(false);
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());
  last_wifi_attempt_ms = millis();
  counters.wifi_attempts++;
}

void onWifiConnected() {
  wifi_retry_ms = kMinimumWifiRetryMs;
  receiver_retry_ms = kMinimumReceiverRetryMs;
  last_receiver_attempt_ms = millis() - receiver_retry_ms;
  last_ack_ms = millis();
  receiver_reachable = false;
  receiver_timeout_reported = false;
  beginNewStream();
  if (was_wifi_connected) {
    counters.wifi_reconnects++;
  }
  was_wifi_connected = true;
  Serial.print("WIFI_CONNECTED ip=");
  Serial.println(WiFi.localIP());
}

void maintainWifi() {
  static wl_status_t previous_status = WL_NO_SHIELD;
  const wl_status_t status = WiFi.status();
  if (status == WL_CONNECTED) {
    if (previous_status != WL_CONNECTED) {
      onWifiConnected();
    }
  } else {
    if (previous_status == WL_CONNECTED) {
      closeReceiverConnection(false);
      Serial.println("WIFI_DISCONNECTED");
    }
    const uint32_t now = millis();
    if (!wifi_ssid.isEmpty() && now - last_wifi_attempt_ms >= wifi_retry_ms) {
      startWifiAttempt();
      wifi_retry_ms = min(kMaximumWifiRetryMs, wifi_retry_ms * 2u);
    }
  }
  previous_status = status;
}

void maintainReceiverConnection() {
  if (!streaming_enabled || WiFi.status() != WL_CONNECTED) {
    return;
  }
  if (receiver_connection_active && receiver_client.connected()) {
    return;
  }
  if (receiver_connection_active) {
    closeReceiverConnection(true);
  }
  const uint32_t now = millis();
  if (now - last_receiver_attempt_ms < receiver_retry_ms) {
    return;
  }
  last_receiver_attempt_ms = now;
  counters.receiver_connect_attempts++;
  receiver_client.stop();
  if (receiver_client.connect(
          receiver_ip, receiver_port, kReceiverConnectTimeoutMs) == 1) {
    receiver_client.setNoDelay(true);
    receiver_connection_active = true;
    receiver_reachable = false;
    receiver_timeout_reported = false;
    ack_frame_used = 0;
    last_ack_ms = now;
    receiver_retry_ms = kMinimumReceiverRetryMs;
    beginNewStream();
    if (had_receiver_connection) {
      counters.receiver_reconnects++;
    }
    had_receiver_connection = true;
    Serial.println("RECEIVER_CONNECTED transport=tcp");
  } else {
    receiver_retry_ms = min(kMaximumReceiverRetryMs, receiver_retry_ms * 2u);
  }
}

uint16_t readBatteryMillivolts() {
#if CUELOOP_BATTERY_ADC_PIN >= 0
  uint32_t sum_mv = 0;
  for (uint8_t index = 0; index < 8; ++index) {
    sum_mv += analogReadMilliVolts(CUELOOP_BATTERY_ADC_PIN);
    delay(2);
  }
  const uint32_t pin_mv = sum_mv / 8;
  const uint32_t battery_mv =
      pin_mv * CUELOOP_BATTERY_SCALE_NUMERATOR / CUELOOP_BATTERY_SCALE_DENOMINATOR;
  return static_cast<uint16_t>(min<uint32_t>(battery_mv, 65535));
#else
  return 0;
#endif
}

void fillTestTone() {
  // 1 kHz transport tone. It validates capture framing/transport only and is
  // not designed to imitate any real CueLoop event class.
  for (uint16_t index = 0; index < cueloop::kSamplesPerFrame; ++index) {
    const uint64_t absolute_sample = sample_clock + index;
    const uint16_t phase = absolute_sample % 16;
    samples[index] = phase < 8 ? 8192 : -8192;
  }
}

void updateAudioDiagnostics() {
  uint64_t sum_squares = 0;
  uint32_t peak = 0;
  for (uint16_t index = 0; index < cueloop::kSamplesPerFrame; ++index) {
    const int32_t value = samples[index];
    const uint32_t magnitude = static_cast<uint32_t>(value < 0 ? -value : value);
    peak = max(peak, magnitude);
    sum_squares += static_cast<uint64_t>(magnitude) * magnitude;
    if (magnitude >= 32760) {
      counters.clipped_samples++;
    }
  }
  last_audio_peak = static_cast<uint16_t>(min<uint32_t>(peak, 32768));
  last_audio_rms = static_cast<uint16_t>(sqrt(
      static_cast<double>(sum_squares) / cueloop::kSamplesPerFrame));
}

bool captureFrame() {
  if (test_tone_enabled) {
    const uint32_t now_us = micros();
    if (static_cast<int32_t>(now_us - next_test_frame_us) < 0) {
      return false;
    }
    if (now_us - next_test_frame_us > kFrameDurationUs * 4u) {
      next_test_frame_us = now_us;
    }
    next_test_frame_us += kFrameDurationUs;
    fillTestTone();
    updateAudioDiagnostics();
    counters.captured_frames++;
    return true;
  }
  if (!microphone_ready) {
    delay(10);
    return false;
  }
  const size_t bytes_read =
      i2s.readBytes(reinterpret_cast<char*>(samples), sizeof(samples));
  if (bytes_read != sizeof(samples)) {
    counters.capture_errors++;
    return false;
  }
  updateAudioDiagnostics();
  counters.captured_frames++;
  return true;
}

uint16_t packetFlags(uint16_t battery_mv) {
  uint16_t flags = 0;
  if (test_tone_enabled) {
    flags |= cueloop::kFlagTestTone;
  }
  if (usb_powered_mode) {
    flags |= cueloop::kFlagUsbPowered;
  }
  if (battery_mv > 0) {
    flags |= cueloop::kFlagBatteryValid;
  }
  if (restart_frames_remaining > 0) {
    flags |= cueloop::kFlagStreamRestart;
  }
  return flags;
}

void buildDatagram(uint16_t battery_mv) {
  memcpy(datagram, cueloop::kMagic, sizeof(cueloop::kMagic));
  datagram[4] = cueloop::kVersion;
  datagram[5] = cueloop::kAudioPcm16;
  cueloop::putBe16(datagram + 6, packetFlags(battery_mv));
  cueloop::putBe32(datagram + 8, pod_id);
  cueloop::putBe32(datagram + 12, sequence_number);
  cueloop::putBe64(datagram + 16, sample_clock);
  cueloop::putBe32(datagram + 24, millis());
  cueloop::putBe16(datagram + 28, cueloop::kSampleRateHz);
  cueloop::putBe16(datagram + 30, cueloop::kSamplesPerFrame);
  cueloop::putBe16(datagram + 32, battery_mv);
  const int rssi = WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0;
  datagram[34] = static_cast<uint8_t>(constrain(rssi, -128, 127));
  datagram[35] = 0;
  for (uint16_t index = 0; index < cueloop::kSamplesPerFrame; ++index) {
    const uint16_t encoded = static_cast<uint16_t>(samples[index]);
    datagram[cueloop::kHeaderBytes + index * 2] = static_cast<uint8_t>(encoded);
    datagram[cueloop::kHeaderBytes + index * 2 + 1] =
        static_cast<uint8_t>(encoded >> 8);
  }
  cueloop::putBe32(
      datagram + 36,
      cueloop::crc32(datagram + cueloop::kHeaderBytes, cueloop::kPayloadBytes));
  cueloop::putBe32(datagram + 40, cueloop::crc32(datagram, 40));
}

bool writeAll(const uint8_t* data, size_t length) {
  size_t offset = 0;
  const uint32_t started_ms = millis();
  const int socket_fd = receiver_client.fd();
  if (socket_fd < 0) {
    return false;
  }
  while (offset < length && receiver_client.connected()) {
    const int written = send(
        socket_fd,
        data + offset,
        length - offset,
        MSG_DONTWAIT);
    if (written > 0) {
      offset += static_cast<size_t>(written);
      continue;
    }
    if (written < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
      break;
    }
    if (millis() - started_ms >= kTcpWriteTimeoutMs) {
      break;
    }
    delay(1);
  }
  return offset == length;
}

void sendFrame() {
  const uint16_t battery_mv = readBatteryMillivolts();
  buildDatagram(battery_mv);
  bool sent = false;
  if (streaming_enabled && receiver_connection_active &&
      receiver_client.connected() && WiFi.status() == WL_CONNECTED) {
    uint8_t prefix[kStreamPrefixBytes];
    cueloop::putBe16(prefix, static_cast<uint16_t>(sizeof(datagram)));
    sent = writeAll(prefix, sizeof(prefix)) &&
           writeAll(datagram, sizeof(datagram));
    if (sent) {
      counters.sent_frames++;
      if (restart_frames_remaining > 0) {
        restart_frames_remaining--;
      }
    } else {
      counters.send_failures++;
      closeReceiverConnection(true);
    }
  }
  sequence_number++;
  sample_clock += cueloop::kSamplesPerFrame;
}

bool validateAck(const uint8_t* ack, size_t length) {
  if (length != cueloop::kAckBytes || memcmp(ack, cueloop::kMagic, 4) != 0) {
    return false;
  }
  if (ack[4] != cueloop::kVersion || ack[5] != cueloop::kReceiverAck ||
      cueloop::getBe16(ack + 6) != 0 || cueloop::getBe32(ack + 8) != pod_id) {
    return false;
  }
  return cueloop::getBe32(ack + 20) == cueloop::crc32(ack, 20);
}

void pollAcknowledgements() {
  if (!receiver_connection_active || !receiver_client.connected()) {
    return;
  }
  while (receiver_client.available() > 0) {
    const int value = receiver_client.read();
    if (value < 0) {
      break;
    }
    if (ack_frame_used >= sizeof(ack_frame)) {
      counters.bad_acks++;
      closeReceiverConnection(true);
      return;
    }
    ack_frame[ack_frame_used++] = static_cast<uint8_t>(value);
    if (ack_frame_used == kStreamPrefixBytes &&
        cueloop::getBe16(ack_frame) != cueloop::kAckBytes) {
      counters.bad_acks++;
      closeReceiverConnection(true);
      return;
    }
    if (ack_frame_used == sizeof(ack_frame)) {
      if (validateAck(ack_frame + kStreamPrefixBytes, cueloop::kAckBytes)) {
        counters.valid_acks++;
        last_ack_ms = millis();
        receiver_reachable = true;
        receiver_timeout_reported = false;
      } else {
        counters.bad_acks++;
      }
      ack_frame_used = 0;
    }
  }

  if (streaming_enabled && millis() - last_ack_ms > kReceiverTimeoutMs) {
    receiver_reachable = false;
    if (!receiver_timeout_reported) {
      counters.receiver_timeouts++;
      receiver_timeout_reported = true;
      restart_frames_remaining = 3;
      Serial.println("RECEIVER_TIMEOUT");
      closeReceiverConnection(false);
    }
  }
}

void printStatus() {
  Serial.print("STATUS pod_id=0x");
  Serial.print(pod_id, HEX);
  Serial.print(" wifi_configured=");
  Serial.print(wifi_ssid.isEmpty() ? "no" : "yes");
  Serial.print(" wifi_connected=");
  Serial.print(WiFi.status() == WL_CONNECTED ? "yes" : "no");
  Serial.print(" receiver=");
  Serial.print(receiver_ip);
  Serial.print(':');
  Serial.print(receiver_port);
  Serial.print(" transport=tcp");
  Serial.print(" reachable=");
  Serial.print(receiver_reachable ? "yes" : "no");
  Serial.print(" source=");
  Serial.print(test_tone_enabled ? "test-tone" : "microphone");
  Serial.print(" power_mode=");
  Serial.print(usb_powered_mode ? "usb" : "battery");
  Serial.print(" stream=");
  Serial.println(streaming_enabled ? "on" : "off");
  Serial.print("COUNTERS captured=");
  Serial.print(counters.captured_frames);
  Serial.print(" sent=");
  Serial.print(counters.sent_frames);
  Serial.print(" send_failures=");
  Serial.print(counters.send_failures);
  Serial.print(" capture_errors=");
  Serial.print(counters.capture_errors);
  Serial.print(" wifi_attempts=");
  Serial.print(counters.wifi_attempts);
  Serial.print(" wifi_reconnects=");
  Serial.print(counters.wifi_reconnects);
  Serial.print(" receiver_connect_attempts=");
  Serial.print(counters.receiver_connect_attempts);
  Serial.print(" receiver_reconnects=");
  Serial.print(counters.receiver_reconnects);
  Serial.print(" valid_acks=");
  Serial.print(counters.valid_acks);
  Serial.print(" bad_acks=");
  Serial.print(counters.bad_acks);
  Serial.print(" receiver_timeouts=");
  Serial.print(counters.receiver_timeouts);
  Serial.print(" clipped_samples=");
  Serial.print(counters.clipped_samples);
  Serial.print(" audio_rms=");
  Serial.print(last_audio_rms);
  Serial.print(" audio_peak=");
  Serial.print(last_audio_peak);
  Serial.print(" rssi_dbm=");
  Serial.print(WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0);
  Serial.print(" free_heap=");
  Serial.println(ESP.getFreeHeap());
}

bool parseOnOff(const String& value, bool& output) {
  if (value.equalsIgnoreCase("ON")) {
    output = true;
    return true;
  }
  if (value.equalsIgnoreCase("OFF")) {
    output = false;
    return true;
  }
  return false;
}

void handleCommand(const String& command) {
  if (command == "HELP") {
    Serial.println(
        "COMMANDS: STATUS | SET_WIFI<TAB>ssid<TAB>password | "
        "SET_RECEIVER<TAB>ipv4<TAB>port | SET_POD_ID<TAB>id | "
        "TEST<TAB>ON|OFF | STREAM<TAB>ON|OFF | POWER<TAB>USB|BATTERY | ERASE");
    return;
  }
  if (command == "STATUS") {
    printStatus();
    return;
  }
  if (command == "ERASE") {
    preferences.clear();
    Serial.println("CONFIG_ERASED restarting");
    delay(100);
    ESP.restart();
  }
  if (command.startsWith("SET_WIFI\t")) {
    const int separator = command.indexOf('\t', 9);
    if (separator < 0) {
      Serial.println("ERROR SET_WIFI requires SSID and password separated by tabs");
      return;
    }
    const String new_ssid = command.substring(9, separator);
    const String new_password = command.substring(separator + 1);
    if (new_ssid.isEmpty() || new_ssid.length() > 32 || new_password.length() > 64) {
      Serial.println("ERROR invalid SSID/password length");
      return;
    }
    preferences.putString("ssid", new_ssid);
    preferences.putString("password", new_password);
    wifi_ssid = new_ssid;
    wifi_password = new_password;
    wifi_retry_ms = kMinimumWifiRetryMs;
    last_wifi_attempt_ms = millis() - wifi_retry_ms;
    Serial.println("WIFI_SAVED password_not_echoed");
    return;
  }
  if (command.startsWith("SET_RECEIVER\t")) {
    const int separator = command.indexOf('\t', 13);
    if (separator < 0) {
      Serial.println("ERROR SET_RECEIVER requires IPv4 and port");
      return;
    }
    IPAddress candidate;
    const String ip_text = command.substring(13, separator);
    const long port = command.substring(separator + 1).toInt();
    if (!candidate.fromString(ip_text) || port < 1 || port > 65535) {
      Serial.println("ERROR invalid receiver IPv4/port");
      return;
    }
    receiver_ip = candidate;
    receiver_port = static_cast<uint16_t>(port);
    preferences.putString("receiver_ip", ip_text);
    preferences.putUShort("receiver_port", receiver_port);
    closeReceiverConnection(false);
    receiver_retry_ms = kMinimumReceiverRetryMs;
    last_receiver_attempt_ms = millis() - receiver_retry_ms;
    Serial.println("RECEIVER_SAVED");
    return;
  }
  if (command.startsWith("SET_POD_ID\t")) {
    char* end = nullptr;
    const uint32_t candidate = strtoul(command.substring(11).c_str(), &end, 0);
    if (candidate == 0 || end == nullptr || *end != '\0') {
      Serial.println("ERROR invalid pod ID");
      return;
    }
    pod_id = candidate;
    preferences.putULong("pod_id", pod_id);
    beginNewStream();
    Serial.println("POD_ID_SAVED");
    return;
  }
  if (command.startsWith("TEST\t")) {
    bool value = false;
    if (!parseOnOff(command.substring(5), value)) {
      Serial.println("ERROR TEST expects ON or OFF");
      return;
    }
    test_tone_enabled = value;
    preferences.putBool("test_tone", value);
    next_test_frame_us = micros();
    beginNewStream();
    Serial.println(value ? "TEST_TONE_ON" : "TEST_TONE_OFF");
    return;
  }
  if (command.startsWith("STREAM\t")) {
    bool value = false;
    if (!parseOnOff(command.substring(7), value)) {
      Serial.println("ERROR STREAM expects ON or OFF");
      return;
    }
    streaming_enabled = value;
    preferences.putBool("streaming", value);
    beginNewStream();
    if (value) {
      last_ack_ms = millis();
      receiver_timeout_reported = false;
      receiver_retry_ms = kMinimumReceiverRetryMs;
      last_receiver_attempt_ms = millis() - receiver_retry_ms;
    } else {
      closeReceiverConnection(false);
    }
    Serial.println(value ? "STREAM_ON" : "STREAM_OFF");
    return;
  }
  if (command.startsWith("POWER\t")) {
    const String value = command.substring(6);
    if (value.equalsIgnoreCase("USB")) {
      usb_powered_mode = true;
    } else if (value.equalsIgnoreCase("BATTERY")) {
      usb_powered_mode = false;
    } else {
      Serial.println("ERROR POWER expects USB or BATTERY");
      return;
    }
    preferences.putBool("usb_mode", usb_powered_mode);
    Serial.println(usb_powered_mode ? "POWER_MODE_USB" : "POWER_MODE_BATTERY");
    return;
  }
  Serial.println("ERROR unknown command; send HELP");
}

void pollSerial() {
  while (Serial.available()) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\r') {
      continue;
    }
    if (character == '\n') {
      if (!serial_line.isEmpty()) {
        handleCommand(serial_line);
        serial_line = "";
      }
      continue;
    }
    if (serial_line.length() >= kMaximumSerialCommand) {
      serial_line = "";
      Serial.println("ERROR command too long");
      continue;
    }
    serial_line += character;
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);
  delay(250);
  loadConfiguration();

  i2s.setPinsPdmRx(CUELOOP_PDM_CLOCK_PIN, CUELOOP_PDM_DATA_PIN);
  microphone_ready = i2s.begin(
      I2S_MODE_PDM_RX,
      cueloop::kSampleRateHz,
      I2S_DATA_BIT_WIDTH_16BIT,
      I2S_SLOT_MODE_MONO);
  next_test_frame_us = micros();
  Serial.println("CUELOOP_CUEPOD_READY firmware=1 protocol=1 raw_audio_storage=disabled");
  Serial.println(microphone_ready ? "MICROPHONE_READY" : "MICROPHONE_ERROR use TEST ON");
  Serial.println(wifi_ssid.isEmpty() ? "WIFI_NOT_CONFIGURED send HELP" : "WIFI_CONFIGURED");
  printStatus();
  if (!wifi_ssid.isEmpty()) {
    last_wifi_attempt_ms = millis() - kMinimumWifiRetryMs;
  }
}

void loop() {
  pollSerial();
  maintainWifi();
  maintainReceiverConnection();
  pollAcknowledgements();

  if (captureFrame()) {
    if (streaming_enabled) {
      sendFrame();
    } else {
      sequence_number++;
      sample_clock += cueloop::kSamplesPerFrame;
    }
  }

  const uint32_t now = millis();
  if (now - last_diagnostics_ms >= kDiagnosticsIntervalMs) {
    last_diagnostics_ms = now;
    printStatus();
  }
}
