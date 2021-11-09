#!/usr/bin/env python3
from time import sleep

from loguru import logger

from enviro_client import Enviro


def display_text(sensor, enviro):
    sensor.read()
    logger.info(str(sensor))
    enviro.display.draw_graph(str(sensor), sensor.history)


def show_all_metrics(enviro: Enviro):
    enviro.display.new_frame()

    for sensor in enviro.sensors:
        sensor.read()
        enviro.display.draw_metric_text(str(sensor), sensor.color())
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
            sleep(0.25)
    except KeyboardInterrupt:
        enviro.display.new_frame()
        exit(0)
