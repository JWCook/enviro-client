#!/usr/bin/env python3
import json
import ssl
import time
from subprocess import check_output

import paho.mqtt.client as mqtt
from loguru import logger

from enviro_client import Enviro, load_config


# Check for Wi-Fi connection
def check_wifi():
    return bool(check_output(["hostname", "-I"]))


# Display Raspberry Pi serial and Wi-Fi status on LCD
def display_status(enviro: Enviro, mqtt_broker):
    wifi_status = "connected" if check_wifi() else "disconnected"
    enviro.disp.draw_text_box(
        f'WiFi: {wifi_status}\nmqtt-broker: {mqtt_broker}',
        bg_color=(0, 170, 170) if check_wifi() else (85, 15, 15),
    )


def configure_client(config, device_id):
    # Use Raspberry Pi serial as client ID
    device_id = f'rpi-{device_id}'
    mqtt_client = mqtt.Client(client_id=device_id)

    # Add authentication, if specified
    if config['tls'] is True:
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
    if config['username'] and config['password']:
        mqtt_client.username_pw_set(config['username'], config['password'])

    # Add callbacks
    # mqtt_client.on_connect = on_connect
    # mqtt_client.on_publish = on_publish

    logger.info(f"Connecting {device_id} to MQTT broker {config['host']}:{config['port']}")
    mqtt_client.connect(config['host'], port=config['port'])
    mqtt_client.loop_start()
    return mqtt_client


def main():
    enviro = Enviro()
    device_id = enviro.get_device_id()

    # Configure MQTT client
    config = load_config()['mqtt']
    mqtt_client = configure_client(config, device_id)
    topic = f"{config['topic']}/{device_id}"

    # Main loop to read data, display, and send over mqtt
    while True:
        try:
            values = enviro.read_all()
            logger.info(values)
            mqtt_client.publish(topic, json.dumps(values))
            display_status(enviro.display, config['host'])
            time.sleep(config['interval'])
        except KeyboardInterrupt:
            enviro.display.set_backlight(0)
            exit(0)


# Optional: MQTT callbacks
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("connected OK")
#     else:
#         print("Bad connection Returned code=", rc)


# def on_publish(client, userdata, mid):
#     print("mid: " + str(mid))


if __name__ == "__main__":
    main()
