# Enviro client
A python client for the [Pimoroni Enviro](https://shop.pimoroni.com/products/enviro?variant=31155658489939).
This adapts a subset of the examples from the
[enviroplus-python](https://github.com/pimoroni/enviroplus-python) repo, combines them, and exposes them in a more pythonic interface.

Currently this package is mainly just for learning purposes, and does not (yet) support the Enviro+ air quality sensors.

## Features
Enviro-client combines the following features into one service:
* Display sensor reading bar charts on the LCD
* Display combined sensor readings and device status
* Toggle between display modes using the proximity sensor
* Publish sensor readings via MQTT (optional)
* Configure display and MQTT settings via a yaml config file

If you want different behavior, these features are also exposed via the `Enviro` class.

## Installation
First, it's recommended to set up system dependencies with the
[enviroplus-python install script](https://github.com/pimoroni/enviroplus-python#installing).

Then:
```
pip install enviro-client
```
