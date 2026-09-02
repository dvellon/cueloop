#pragma once

#include <stdint.h>

// CueLoop Protocol v1 wire constants. Multi-byte header values are encoded
// explicitly in network byte order by firmware; do not transmit this struct
// by casting because compiler padding and host endianness are not portable.
namespace cueloop {
constexpr uint8_t kMagic[4] = {'C', 'L', 'P', '1'};
constexpr uint8_t kVersion = 1;
constexpr uint8_t kAudioPcm16 = 1;
constexpr uint8_t kReceiverAck = 2;
constexpr uint16_t kFlagSimulated = 1u << 0;
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
}  // namespace cueloop
