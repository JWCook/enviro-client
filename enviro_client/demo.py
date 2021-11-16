#!/usr/bin/env python3
from time import sleep

from enviro_client.enviro import Enviro

# TODO: Run MQTT publish from a separate thread at different interval
if __name__ == '__main__':
    enviro = Enviro()
    try:
        while True:
            enviro.loop()
            sleep(2)
            # sleep(enviro.mqtt.interval)
    except KeyboardInterrupt:
        enviro.close()
