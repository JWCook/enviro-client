#!/usr/bin/env python3
from logging import basicConfig, getLogger
from time import sleep

from enviro_client import Enviro

basicConfig(level='INFO')
logger = getLogger(__name__)


def display_everything(enviro: Enviro):
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
            display_everything(enviro)
            sleep(0.5)
    except KeyboardInterrupt:
        enviro.display.new_frame()
        exit(0)
