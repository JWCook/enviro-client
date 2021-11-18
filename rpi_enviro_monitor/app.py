#!/usr/bin/env python3
from threading import Thread
from time import sleep

from . import Enviro


def display_loop(enviro):
    while True:
        enviro.render()
        sleep(enviro.display.interval)


def publish_loop(enviro):
    while True:
        enviro.publish()
        sleep(enviro.mqtt.interval)


def run():
    enviro = Enviro()

    # Run MQTT publisher in a separate thread so it can run at a different interval than display
    if enviro.mqtt:
        publish_thread = Thread(target=publish_loop, args=(enviro,), daemon=True)
        publish_thread.start()

    # Run display loop in main thread
    try:
        display_loop(enviro)
    except KeyboardInterrupt:
        enviro.close()


if __name__ == '__main__':
    run()
