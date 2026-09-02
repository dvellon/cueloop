#pragma once

#include <Arduino.h>

namespace cueloop {

constexpr uint8_t kMagic[4] = {'C', 'L', 'P', '1'};
constexpr uint8_t kVersion = 1;
constexpr uint8_t kAudioPcm16 = 1;
constexpr uint8_t kReceiverAck = 2;
constexpr uint16_t kFlagTestTone = 1u << 1;
constexpr uint16_t kFlagUsbPowered = 1u << 2;
constexpr uint16_t kFlagBatteryValid = 1u << 3;
constexpr uint16_t kFlagStreamRestart = 1u << 4;
constexpr uint16_t kSampleRateHz = 16000;
constexpr uint16_t kSamplesPerFrame = 320;
constexpr uint16_t kHeaderBytes = 44;
constexpr uint16_t kPayloadBytes = kSamplesPerFrame * sizeof(int16_t);
constexpr uint16_t kDatagramBytes = kHeaderBytes + kPayloadBytes;
constexpr uint16_t kAckBytes = 24;

inline void putBe16(uint8_t* target, uint16_t value) {
  target[0] = static_cast<uint8_t>(value >> 8);
  target[1] = static_cast<uint8_t>(value);
}

inline void putBe32(uint8_t* target, uint32_t value) {
  target[0] = static_cast<uint8_t>(value >> 24);
  target[1] = static_cast<uint8_t>(value >> 16);
  target[2] = static_cast<uint8_t>(value >> 8);
  target[3] = static_cast<uint8_t>(value);
}

inline void putBe64(uint8_t* target, uint64_t value) {
  putBe32(target, static_cast<uint32_t>(value >> 32));
  putBe32(target + 4, static_cast<uint32_t>(value));
}

inline uint16_t getBe16(const uint8_t* source) {
  return static_cast<uint16_t>(source[0] << 8) | source[1];
}

inline uint32_t getBe32(const uint8_t* source) {
  return (static_cast<uint32_t>(source[0]) << 24) |
         (static_cast<uint32_t>(source[1]) << 16) |
         (static_cast<uint32_t>(source[2]) << 8) |
         static_cast<uint32_t>(source[3]);
}

inline uint32_t crc32(const uint8_t* data, size_t length) {
  uint32_t value = 0xFFFFFFFFu;
  for (size_t index = 0; index < length; ++index) {
    value ^= data[index];
    for (uint8_t bit = 0; bit < 8; ++bit) {
      value = (value >> 1) ^ (0xEDB88320u & (0u - (value & 1u)));
    }
  }
  return ~value;
}

}  // namespace cueloop
