from logging import getLogger
from typing import Optional, Tuple

from enviro_client import (
    Display,
    HumiditySensor,
    LightSensor,
    NoiseSensor,
    PressureSensor,
    ProximitySensor,
    Sensor,
    TemperatureSensor,
)

logger = getLogger(__name__)


class Enviro:
    def __init__(self):
        self.display = Display(n_metrics=5)
        self.proximity = ProximitySensor()
        self.mode = 0

        temp = TemperatureSensor(self.display.width)
        self.sensors: Tuple[Sensor] = (
            temp,
            PressureSensor(self.display.width, bme280=temp.bme280),
            HumiditySensor(self.display.width, bme280=temp.bme280),
            LightSensor(self.display.width, ltr559=self.proximity.ltr559),
            NoiseSensor(self.display.width),
        )

    def check_mode(self) -> int:
        """If the proximity crosses the threshold, toggle the mode"""
        if self.proximity.check_press():
            self.mode += 1
            self.mode %= len(self.sensors) + 1
            logger.info(f'Switched to mode {self.mode}')
        return self.mode

    def get_active_sensor(self) -> Optional[Sensor]:
        """Return the currently selected sensor (if any)"""
        mode = self.check_mode()
        return self.sensors[mode - 1] if mode > 0 else None
