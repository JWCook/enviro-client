#!/usr/bin/env python3
import json
import ssl
from subprocess import check_output
from time import sleep

from loguru import logger
from paho.mqtt.client import Client as MQTTClient

from enviro_client import Enviro, load_config


# Check for Wi-Fi connection
def check_connection() -> bool:
    return bool(check_output(["hostname", "-I"]))


# Display Raspberry Pi serial and Wi-Fi status on LCD
def display_status(enviro: Enviro, mqtt_host: str, n_sent: int):
    wifi_status = "connected" if check_connection() else "disconnected"
    enviro.display.draw_text_box(
        f'WiFi: {wifi_status}\nMQTT host: {mqtt_host}\n'
        f'Uptime: {enviro.uptime()}\nData points sent: {n_sent}',
        bg_color=(0, 170, 170) if check_connection() else (85, 15, 15),
    )


def configure_client(config: dict, device_id: str) -> MQTTClient:
    """Get a configured MQTT client"""
    # Use Raspberry Pi serial as client ID
    device_id = f'rpi-{device_id}'
    mqtt_client = MQTTClient(client_id=device_id)

    # Add authentication, if specified
    if config['tls'] is True:
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
    if config['username'] and config['password']:
        mqtt_client.username_pw_set(config['username'], config['password'])

    # Connect to MQTT broker
    logger.info(f"Connecting {device_id} to MQTT broker {config['host']}:{config['port']}")
    mqtt_client.connect(config['host'], port=config['port'])
    mqtt_client.loop_start()
    return mqtt_client


# TODO: Combine with demo.py, run in separate thread, add as another display option
def main():
    enviro = Enviro()
    device_id = enviro.get_device_id()
    n_sent = 0

    # Configure MQTT client
    config = load_config()['mqtt']
    mqtt_client = configure_client(config, device_id)
    topic = f"{config['topic']}/{device_id}"

    # TODO: Retry if disconnected
    # Main loop to read data, display, and send over mqtt
    while True:
        try:
            values = enviro.read_all()
            logger.info(values)
            mqtt_client.publish(topic, json.dumps(values))
            n_sent += 1
            display_status(enviro, config['host'], n_sent)
            sleep(config['interval'])
        except KeyboardInterrupt:
            logger.warning('Shutting down')
            enviro.display.set_backlight(0)
            exit(0)


if __name__ == "__main__":
    main()
