import subprocess
from datetime import timedelta
from threading import RLock
from time import time
from typing import Optional

from loguru import logger

from .config import load_config
from .display import BG_CYAN, BG_RED, Display, RGBColor
from .mqtt import MQTTClient
from .sensors import (
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

    The main entry points are :py:meth:`Enviro.render`, and :py:meth:`Enviro.publish`, intended to
    be called from a loop. Individual features are broken down into other methods if different
    behavior is needed.
    """

    def __init__(self):
        logger.debug('Initializing sensors and display')
        self.config = load_config()
        self.device_id = _get_device_id()
        self.lock = RLock()
        self.mode = 0
        self.start_time = time()

        # Configure display
        display_interval = self.config['display']['interval']
        self.display = Display(interval=self.config['display']['interval'])

        # Proximity sensor is used internally, but not directly displayed on screen
        self.proximity = ProximitySensor()

        # Configure sensors
        temp = TemperatureSensor(display_interval)
        self.sensors: tuple[Sensor] = (
            temp,
            PressureSensor(display_interval, bme280=temp.bme280),
            HumiditySensor(display_interval, bme280=temp.bme280),
            LightSensor(display_interval, ltr559=self.proximity.ltr559),
            NoiseSensor(display_interval),
        )

        # Configure MQTT client, if enabled
        self.mqtt = None
        if self.config['mqtt'].get('enabled', False):
            self.mqtt = MQTTClient(self.device_id, config=self.config['mqtt'])

    def check_mode(self):
        """Check if we have changed the display mode, by using the proximity sensor as a button"""
        if self.proximity.check_press():
            self.cycle_mode()
        return self.mode

    def cycle_mode(self):
        """Switch to the next display mode"""
        n_modes = len(self.sensors) + N_EXTRA_MODES
        self.mode += 1
        self.mode %= n_modes
        logger.info(f'Switched to mode {self.mode}')

    def close(self):
        """Clear the display and close the MQTT connection"""
        logger.warning('Shutting down')
        self.display.off()
        self.mqtt.disconnect()

    def display_active_sensor(self):
        """Display data from the currently selected sensor"""
        sensor = self.get_active_sensor()
        if not sensor:
            return
        with self.lock:
            sensor.read()
            self.display.draw_graph(sensor.status(), sensor.history)

    def display_all(self) -> None:
        """Display all sensor readings"""
        self.display.draw_list(self.read_all_statuses())

    def display_status(self):
        """Display a status message"""
        connected = _check_connection()
        status = (
            f'WiFi: {"connected" if connected else "disconnected"}\n'
            f'MQTT host: {self.mqtt.host if self.mqtt else "N/A"}\n'
            f'Packets sent: {self.mqtt.n_sent if self.mqtt else 0}\n'
            f'Uptime: {self.uptime()}'
        )
        self.display.draw_text_box(status, bg_color=BG_CYAN if connected else BG_RED)

    def get_active_sensor(self) -> Optional[Sensor]:
        """Get the currently selected sensor, if any"""
        sensor_idx = self.mode - N_EXTRA_MODES
        return self.sensors[sensor_idx] if sensor_idx >= 0 else None

    def publish(self):
        """Log and publish sensor data to MQTT, if enabled"""
        data = self.read_all_values()
        logger.info(data)
        if self.mqtt:
            self.mqtt.publish_json(data)

    def _read_all(self) -> list[float]:
        """Refresh and return all sensor values"""
        with self.lock:
            return [sensor.read() for sensor in self.sensors]

    def read_all_values(self) -> dict[str, float]:
        """Get a reading from all sensors in the format ``{sensor_name: value}``"""
        self._read_all()
        return {sensor.name: sensor.value for sensor in self.sensors}

    def read_all_statuses(self) -> dict[str, RGBColor]:
        """Get a reading from all sensors for display, in the format  ``{sensor_status:
        bin_color}``"""
        self._read_all()
        return {sensor.status(): sensor.bin_color() for sensor in self.sensors}

    def render(self):
        """Draw a new frame on the display according to the currently selected mode"""
        mode = self.check_mode()
        if mode == MODE_DISPLAY_ALL:
            self.display_all()
        elif mode == MODE_DISPLAY_STATUS:
            self.display_status()
        else:
            self.display_active_sensor()

    def uptime(self) -> timedelta:
        """Get the application uptime"""
        return timedelta(seconds=int(time() - self.start_time))


# TODO: Implement sensors for Enviro+... if/when I get one
class EnviroPlus(Enviro):
    ...


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
