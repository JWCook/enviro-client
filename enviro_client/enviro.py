import subprocess
from datetime import timedelta
from time import time
from typing import Optional

from loguru import logger

from enviro_client.config import load_config
from enviro_client.display import BG_CYAN, BG_RED, Display, RGBColor
from enviro_client.mqtt import MQTTClient
from enviro_client.sensors import (
    HumiditySensor,
    LightSensor,
    NoiseSensor,
    PressureSensor,
    ProximitySensor,
    Sensor,
    TemperatureSensor,
)

# Total number of display modes is len(sensors) plus extra modes for additional info
N_EXTRA_MODES = 2
MODE_DISPLAY_ALL = 0
MODE_DISPLAY_STATUS = 1


class Enviro:
    """Class that manages the Enviro's sensors, display, and (optionally) an MQTT client for sending
    sensor data.
    """

    def __init__(self):
        logger.debug('Initializing sensors and display')
        self.config = load_config()
        self.device_id = _get_device_id()
        self.mode = 0
        self.start_time = time()

        # Proximity sensor is used internally, but not directly displayed on screen
        self.proximity = ProximitySensor()

        # Configure sensors
        temp = TemperatureSensor()
        self.sensors: tuple[Sensor] = (
            temp,
            PressureSensor(bme280=temp.bme280),
            HumiditySensor(bme280=temp.bme280),
            LightSensor(ltr559=self.proximity.ltr559),
            NoiseSensor(),
        )

        # Configure display
        self.display = Display(n_metrics=len(self.sensors))

        # Configure MQTT client, if enabled
        self.mqtt = None
        if self.config['mqtt'].get('enabled', False):
            self.mqtt = MQTTClient(self.device_id, config=self.config['mqtt'])

    def loop(self):
        """WIP"""
        self.check_mode()
        self.publish()

        if active_sensor := self.get_active_sensor():
            active_sensor.read()
            self.display.draw_graph(active_sensor.status(), active_sensor.history)
        elif self.mode == MODE_DISPLAY_ALL:
            self.display_all()
        elif self.mode == MODE_DISPLAY_STATUS:
            self.display_status()

    def close(self):
        """Clear the display and close the MQTT connection"""
        logger.warning('Shutting down')
        self.display.off()
        self.mqtt.disconnect()

    def display_all(self) -> None:
        """Display all sensor readings"""
        self.display.draw_all_metrics(self.read_all_colors())

    def display_status(self):
        """Display a status message"""
        connected = _check_connection()
        status = (
            f'WiFi: {"connected" if connected else "disconnected"}\n'
            f'Uptime: {self.uptime()}\n'
            f'MQTT host: {self.mqtt.host if self.mqtt else "N/A"}\n'
            f'Packets sent: {self.mqtt.n_sent if self.mqtt else 0}'
        )
        self.display.draw_text_box(status, bg_color=BG_CYAN if connected else BG_RED)

    def check_mode(self):
        """Check if we have changed the mode by using the proximity sensor as a button"""
        n_modes = len(self.sensors) + N_EXTRA_MODES
        if self.proximity.check_press():
            self.mode += 1
            self.mode %= n_modes
            logger.info(f'Switched to mode {self.mode}')

    def get_active_sensor(self) -> Optional[Sensor]:
        """Get the currently selected sensor, if any"""
        sensor_idx = self.mode - N_EXTRA_MODES
        return self.sensors[sensor_idx] if sensor_idx >= 0 else None

    def publish(self):
        """Log and publish sensor data to MQTT, if enabled"""
        data = self.read_all()
        logger.info(data)
        if self.mqtt:
            self.mqtt.publish_json(data)

    def read_all(self) -> dict[str, float]:
        """Get a reading from all sensors in the format ``{sensor_name: value}``"""
        return {sensor.name: sensor.read() for sensor in self.sensors}

    def read_all_colors(self) -> dict[str, RGBColor]:
        """Get a reading from all sensors for display, in the format  ``{sensor_status: bin_color}``"""
        sensor_statuses = {}
        for sensor in self.sensors:
            sensor.read()
            sensor_statuses[sensor.status()] = sensor.bin_color()
        return sensor_statuses

    def uptime(self) -> timedelta:
        """Get the application uptime"""
        return timedelta(seconds=int(time() - self.start_time))


def _check_connection() -> bool:
    """Check for an active network connection"""
    return bool(subprocess.check_output(["hostname", "-I"]))


def _get_device_id() -> str:
    """Get Raspberry Pi serial number"""
    with open("/proc/cpuinfo", "r") as f:
        for line in f.readlines():
            if line.startswith('Serial'):
                return line.split(':')[1].strip()
    return 'N/A'
