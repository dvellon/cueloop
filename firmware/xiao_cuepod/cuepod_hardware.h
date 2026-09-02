#pragma once

#if __has_include("cuepod_hardware.local.h")
#include "cuepod_hardware.local.h"
#endif

#ifndef CUELOOP_PDM_CLOCK_PIN
// Seeed Studio's Arduino-ESP32 3.x documentation for the XIAO ESP32S3 Sense
// expansion board specifies GPIO42 as PDM clock and GPIO41 as PDM data.
#define CUELOOP_PDM_CLOCK_PIN 42
#endif
#ifndef CUELOOP_PDM_DATA_PIN
#define CUELOOP_PDM_DATA_PIN 41
#endif

// The installed XIAO_ESP32S3 board variant does not expose a verified battery
// ADC definition. Leave telemetry invalid rather than invent a voltage. A
// physical revision with a measured divider may override all three values in
// a local ignored cuepod_hardware.local.h file.
#ifndef CUELOOP_BATTERY_ADC_PIN
#define CUELOOP_BATTERY_ADC_PIN -1
#endif
#ifndef CUELOOP_BATTERY_SCALE_NUMERATOR
#define CUELOOP_BATTERY_SCALE_NUMERATOR 1
#endif
#ifndef CUELOOP_BATTERY_SCALE_DENOMINATOR
#define CUELOOP_BATTERY_SCALE_DENOMINATOR 1
#endif
