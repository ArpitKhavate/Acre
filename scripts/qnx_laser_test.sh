#!/bin/sh
# Standalone laser-emitter test for QNX on Raspberry Pi 5 (uses gpio-rp1).
# The laser is a digital on/off output, same as an LED.
#
#   sh scripts/qnx_laser_test.sh
#
# BCM pin must match edge/config.py: LASER=24
# SAFETY: never aim the laser at anyone's eyes.

LASER=24

echo "Configuring GPIO$LASER as output (off)..."
gpio-rp1 set $LASER op dl

i=1
while [ $i -le 3 ]; do
  echo "laser ON"
  gpio-rp1 set $LASER dh
  sleep 1
  echo "laser OFF"
  gpio-rp1 set $LASER dl
  sleep 1
  i=$((i + 1))
done

echo "Done. If the laser blinked 3 times, wiring is correct."
