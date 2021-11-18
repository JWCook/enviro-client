#!/usr/bin/env bash
# Minimal install script, mostly adapted from:
# https://github.com/pimoroni/enviroplus-python#installing

# TODO: Install from PyPI/git without cloning
# DEFAULT_CONFIG=https://raw.githubusercontent.com/JWCook/enviro-client/main/enviro.yml
# SYSTEMD_UNIT=https://raw.githubusercontent.com/JWCook/enviro-client/main/enviro.service
BOOT_CONFIG=/boot/config.txt
APP_CONFIG=~/.config/enviro.yml



function append-config() {
    sed -i "s/^#$1/$1/" $BOOT_CONFIG
    if ! grep -q "^$1" $BOOT_CONFIG; then
        printf "$1\n" >> $BOOT_CONFIG
    fi
}

# Set up I2C, SPI, and UART (if not already done)
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 1
sudo raspi-config nonint set_config_var enable_uart 1 $BOOT_CONFIG
sudo append-config 'dtoverlay=pi3-miniuart-bt'
sudo append-config 'dtoverlay=adau7002-simple'

# Install system and python packages
sudo apt-get install -y libportaudio2
pip install --user -Ue .
# pip install --user -U enviro-client

# Copy config file with default settings
test -f $APP_CONFIG && cp enviro.yml $APP_CONFIG

# Install as a systemd service and run on startup
sudo cp enviro.service /etc/systemd/system/
sudo systemctl enable enviro.service
sudo systemctl start  enviro.service
