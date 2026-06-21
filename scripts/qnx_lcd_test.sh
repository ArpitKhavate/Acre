#!/bin/sh
# I2C 1602 LCD test on QNX, driven through edge/lcd.py over /dev/i2c1.
#
# Start the I2C driver first (exposes /dev/i2c1):
#   i2c-dwc-rpi5 -p0x1f00074000 -c200000000 -q0xa8 --u1
# Confirm the LCD's address (commonly 0x27 or 0x3F); override if needed:
#   ACRE_LCD_I2C_ADDR=0x3F sh scripts/qnx_lcd_test.sh
#
#   sh scripts/qnx_lcd_test.sh

cd "$(dirname "$0")/.." || exit 1

python3 -c "from edge import lcd; lcd.show('ACRE LCD OK', 'HEALTH 100/100'); print('LCD backend:', lcd.backend_name())"

echo "Done. The LCD should read:  ACRE LCD OK / HEALTH 100/100"
