import subprocess
from datetime import timedelta
from time import time
from typing import Dict, Optional, Tuple

from loguru import logger

from enviro_client import (
    Display,
    HumiditySensor,
    LightSensor,
    NoiseSensor,
    PressureSensor,
    ProximitySensor,
    Sensor,
    TemperatureSensor,
    load_config,
)


class Enviro:
    def __init__(self):
        logger.debug('Initializing display and sensors')
        self.config = load_config()
        self.display = Display(n_metrics=5)
        self.proximity = ProximitySensor()
        self.mode = 0
        self.start_time = time()

        temp = TemperatureSensor()
        self.sensors: Tuple[Sensor] = (
            temp,
            PressureSensor(bme280=temp.bme280),
            HumiditySensor(bme280=temp.bme280),
            LightSensor(ltr559=self.proximity.ltr559),
            NoiseSensor(),
        )

    def check_connection(self) -> bool:
        """Check for an active network connection"""
        return bool(subprocess.check_output(["hostname", "-I"]))

    def check_mode(self) -> int:
        """Check if we have changed the mode by using the proximity sensor as a button"""
        if self.proximity.check_press():
            self.mode += 1
            self.mode %= len(self.sensors) + 1
            logger.info(f'Switched to mode {self.mode}')
        return self.mode

    def get_active_sensor(self) -> Optional[Sensor]:
        """Return the currently selected sensor (if any)"""
        mode = self.check_mode()
        return self.sensors[mode - 1] if mode > 0 else None

    def read_all(self) -> Dict[str, float]:
        """Get a reading from all sensors"""
        return {sensor.name: sensor.read() for sensor in self.sensors}

    def get_device_id(self) -> str:
        """Get Raspberry Pi serial number"""
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[1].strip()
        return 'N/A'

    def uptime(self) -> timedelta:
        """Get the application (not device) uptime"""
        return timedelta(seconds=int(time() - self.start_time))
