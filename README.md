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
* Display bar charts for individual sensor metrics
* Display combined sensor readings and device status
* Toggle between display modes using the proximity sensor
* Publish sensor readings via MQTT (optional)
* Configure via a yaml config file

`enviro-client` can also be used as a python library, if you don't plan on using it as a service,
or if you want different behavior.

## Installation

### Requirements
* Raspberry Pi OS 'Bullseye' (not tested on earlier releases)
* Python 3.9+

### Quick installation
To install and configure `enviro-client` as a systemd service:
```
curl -fLo install.sh https://raw.githubusercontent.com/JWCook/enviro-client/main/install.sh
./install.sh
```
Then, update config settings in `~/.config/enviro.yml` as needed.

### Alternate installation
If the included script doesn't work for you, try the
[enviroplus-python install script](https://github.com/pimoroni/enviroplus-python#installing),
which accounts for more variations in system configurations.

Then install this package:
```
pip install --user enviro-client
```
And see [install.sh](https://github.com/JWCook/enviro-client/blob/main/install.sh) for optional
setup steps.

### Local development
Requires [poetry](https://python-poetry.org/docs/master/#installation).
```python
poetry install
```

## Credits
* Most features are adapted from the examples in [enviroplus-python](https://github.com/pimoroni/enviroplus-python)
* MQTT client is adapted from [rpi-enviro-mqtt](https://github.com/robmarkcole/rpi-enviro-mqtt)
  (also in enviroplus-python examples)
* Example systemd service is taken from
  [rpi-enviro-mqtt](https://github.com/robmarkcole/rpi-enviro-mqtt)
