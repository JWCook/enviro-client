from typing import Tuple

from enviro_client.display import Display
from enviro_client.sensors import (
    HumiditySensor,
    LightSensor,
    NoiseSensor,
    PressureSensor,
    ProximitySensor,
    Sensor,
    TemperatureSensor,
)


class Enviro:
    def __init__(self):
        self.proximity = ProximitySensor()
        self.mode = 0
        temp = TemperatureSensor()
        self.sensors: Tuple[Sensor] = (
            temp,
            PressureSensor(bme280=temp.bme280),
            HumiditySensor(bme280=temp.bme280),
            LightSensor(ltr559=self.proximity.ltr559),
            NoiseSensor(),
        )

        self.display = Display(len(self.sensors))
