#!/bin/sh
# Standalone LED + buzzer test for QNX on Raspberry Pi 5 (uses gpio-rp1).
# Run this FIRST, before the Python pipeline, to prove your wiring works.
#
#   sh scripts/qnx_led_test.sh
#
# BCM pins must match edge/config.py: RED=17 GREEN=27 BLUE=23 BUZZER=22

RED=17
GREEN=27
BLUE=23
BUZZER=22

echo "Configuring pins as outputs..."
for p in $RED $GREEN $BLUE $BUZZER; do
  gpio-rp1 set $p op dl
done

echo "RED on"
gpio-rp1 set $RED dh; sleep 1; gpio-rp1 set $RED dl

echo "GREEN on"
gpio-rp1 set $GREEN dh; sleep 1; gpio-rp1 set $GREEN dl

echo "BLUE on"
gpio-rp1 set $BLUE dh; sleep 1; gpio-rp1 set $BLUE dl

echo "BUZZER beep"
gpio-rp1 set $BUZZER dh; sleep 1; gpio-rp1 set $BUZZER dl

echo "Done. If each color lit and the buzzer beeped, wiring is correct."
