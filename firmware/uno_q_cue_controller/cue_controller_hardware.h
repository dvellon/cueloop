#pragma once

#if __has_include("cue_controller_hardware.local.h")
#include "cue_controller_hardware.local.h"
#endif

// Optional normally-open acknowledgement button from D4 to GND. With no
// button attached INPUT_PULLUP remains safely inactive.
#ifndef CUELOOP_ACK_BUTTON_PIN
#define CUELOOP_ACK_BUTTON_PIN D4
#endif

// Optional active-high external outputs. Leave disabled for the minimum BOM;
// the two MCU-controlled onboard RGB LEDs remain the verified fallback.
#ifndef CUELOOP_BUZZER_PIN
#define CUELOOP_BUZZER_PIN -1
#endif
#ifndef CUELOOP_HAPTIC_PIN
#define CUELOOP_HAPTIC_PIN -1
#endif
