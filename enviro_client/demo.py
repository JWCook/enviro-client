#!/usr/bin/env python3
from time import sleep

from loguru import logger

from enviro_client import Enviro


def display_text(sensor, enviro):
    sensor.read()
    logger.info(str(sensor))

    # Scale the values for the metric between 0 and 1
    vmin = min(sensor.history)
    vmax = max(sensor.history)
    colors = [(v - vmin + 1) / (vmax - vmin + 1) for v in sensor.history]
    enviro.display.draw_text(str(sensor), colors)


def show_all_metrics(enviro: Enviro):
    enviro.display.new_frame()

    for idx, sensor in enumerate(enviro.sensors):
        sensor.read()
        enviro.display.add_metric(idx, str(sensor), sensor.color())
        logger.info(str(sensor))

    enviro.display.draw_frame()


if __name__ == '__main__':
    enviro = Enviro()
    try:
        while True:
            if active_sensor := enviro.get_active_sensor():
                display_text(active_sensor, enviro)
            else:
                show_all_metrics(enviro)
            sleep(0.5)
    except KeyboardInterrupt:
        enviro.display.new_frame()
        exit(0)
