# Enviro client
**WIP**

A python client for the [Pimoroni Enviro](https://shop.pimoroni.com/products/enviro?variant=31155658489939).
This adapts a subset of the examples from the
[enviroplus-python](https://github.com/pimoroni/enviroplus-python) repo, combines them into a single
service, and also exposes them for eaiser use as a python library.

Currently this is mainly just for learning purposes, and does not (yet) support the Enviro+
gas and PM sensors.

## Features
`enviro-client` combines the following features into one program, intended to be used as a systemd service:
* Display sensor reading bar charts on the LCD
* Display combined sensor readings and device status
* Toggle between display modes using the proximity sensor
* Publish sensor readings via MQTT (optional)
* Configure display and MQTT settings via a yaml config file

Alternatively, `enviro-client` can be used as a python library if you don't plan on using these
features as a service, or if you want different behavior.

## Installation

### Quick installation (WIP)
To install and configure `enviro-client` as a systemd service:
```
git clone https://github.com/JWCook/enviro-client
cd enviro-client
./install.sh
```
Update config settings in `~/.config/enviro.yml`

### Alternate installation
First, set up system dependencies with the
[enviroplus-python install script](https://github.com/pimoroni/enviroplus-python#installing).

Then:
```
pip install --user -U enviro-client
```

Copy the [included config file](https://raw.githubusercontent.com/JWCook/enviro-client/main/enviro.yml)
to `~/.config/enviro.yml`, and update as needed.

If you would like to run `enviro-client` as a service, copy the
[included service file](https://raw.githubusercontent.com/JWCook/enviro-client/main/enviro.service)
to `/etc/systemd/system/enviro.service` and enable:
```
sudo systemctl enable enviro.service
sudo systemctl start  enviro.service
```