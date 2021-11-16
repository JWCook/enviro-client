import json
from ssl import PROTOCOL_TLSv1_2

from loguru import logger
from paho.mqtt.client import Client as BaseClient


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
        self.publish(self.topic, json.dumps(data))
        self.n_sent += 1
