#!/usr/bin/env bash
# Minimal install script, which should work for a fresh RPi OS install.
# Mostly adapted from:
# https://github.com/pimoroni/enviroplus-python#installing

# Local config files
BOOT_CONFIG=/boot/config.txt
APP_CONFIG=~/.config/enviro.yml
SYSTEMD_UNIT=/etc/systemd/system/enviro.service

# Remote config files to download, if needed
APP_CONFIG_URL=https://raw.githubusercontent.com/JWCook/enviro-client/main/enviro.yml
SYSTEMD_UNIT_URL=https://raw.githubusercontent.com/JWCook/enviro-client/main/enviro.service

function append-config() {
    sudo sed -i "s/^#$1/$1/" $BOOT_CONFIG
    if ! grep -q "^$1" $BOOT_CONFIG; then
        sudo printf "$1\n" >> $BOOT_CONFIG
    fi
}

function pyfile() {
    python -c "import $@; print($@.__file__)" | sed 's/\.pyc/\.py/'
}

# Set up I2C, SPI, and UART (if not already done)
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 1
sudo raspi-config nonint set_config_var enable_uart 1 $BOOT_CONFIG
append-config 'dtoverlay=pi3-miniuart-bt'
append-config 'dtoverlay=adau7002-simple'

# Install system packages
sudo apt-get update
sudo apt-get install -y libopenjp2-7 libportaudio2 python3-rpi.gpio

# Development mode: install from source
if [ -f pyproject.toml ]; then
    pip install --user -U '.'
# Otherwise install from PyPI
else
    pip install --user -U rpi-enviro-monitor
fi

# Install default config file
if [ ! -f $APP_CONFIG ]; then
    curl -fLo $APP_CONFIG $APP_CONFIG_URL
fi

# Install systemd service and run on startup
if [ ! -f $SYSTEMD_UNIT ]; then
    curl -fLo enviro.service $SYSTEMD_UNIT_URL
    # Update unit file to point to wherever the library has been installed
    entry_point=$(pyfile rpi_enviro_monitor.console)
    sed -i "s|{{ENTRY_POINT}}|$entry_point|" enviro.service
    sudo mv enviro.service $SYSTEMD_UNIT
fi
sudo systemctl enable enviro.service
sudo systemctl start  enviro.service
