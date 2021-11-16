#!/usr/bin/env python3
import json
from ssl import PROTOCOL_TLSv1_2
from time import sleep

from loguru import logger
from paho.mqtt.client import Client as BaseClient

from enviro_client import Enviro


class MQTTClient(BaseClient):
    """Custom MQTT client class using settings loaded from a config file"""

    def __init__(self, device_id: str, config: dict, **kwargs):
        super().__init__(client_id=f'rpi-{device_id}', **kwargs)

        # Load info from config file
        self.host = config['host']
        self.interval = config['interval']
        self.topic = f"{config['topic']}/{device_id}"
        self.n_sent = 0

        # Add authentication, if specified
        if config['tls'] is True:
            self.tls_set(tls_version=PROTOCOL_TLSv1_2)
        if config['username'] and config['password']:
            self.username_pw_set(config['username'], config['password'])

        # Connect to MQTT broker
        logger.info(f"Connecting {device_id} to MQTT broker {config['host']}:{config['port']}")
        self.connect(config['host'], port=config['port'])
        self.loop_start()

    def publish_json(self, data: dict):
        """Publish a message in JSON format"""
        logger.info(data)
        self.publish(self.topic, json.dumps(data))
        self.n_sent += 1


def display_mqtt_status(enviro: Enviro, mqtt_client: MQTTClient):
    """Display basic status on screen"""
    connected = enviro.check_connection()
    enviro.display.draw_text_box(
        f'WiFi: {"connected" if connected else "disconnected"}\n'
        f'MQTT host: {mqtt_client.host}\n'
        f'Uptime: {enviro.uptime()}\n'
        f'Packets sent: {mqtt_client.n_sent}',
        bg_color=(0, 170, 170) if connected else (85, 15, 15),
    )


# TODO: Combine with demo.py, run in separate thread, add as another display option
# TODO: Retry if disconnected
def main():
    # Use Raspberry Pi serial as client ID
    enviro = Enviro()
    mqtt_client = MQTTClient(enviro.get_device_id(), config=enviro.config['mqtt'])

    # Main loop to read data, display, and send over mqtt
    while True:
        try:
            mqtt_client.publish(enviro.read_all())
            display_mqtt_status(enviro, mqtt_client.host, mqtt_client.n_sent)
            sleep(mqtt_client.interval)
        except KeyboardInterrupt:
            logger.warning('Shutting down')
            enviro.display.off()
            exit(0)


if __name__ == "__main__":
    main()
