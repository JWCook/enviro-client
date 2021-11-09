"""Interface for LTR559 light/proximity sensor"""
from time import time

from ltr559 import LTR559

from enviro_client.sensors import Sensor

# Proximity sensor delay in seconds, for using as a "button"
PROXIMITY_DELAY = 0.5


class LightSensor(Sensor):
    name = 'light'
    unit = 'Lux'
    bins = (-1, -1, 30000, 100000)

    def __init__(self, *args, ltr559: LTR559 = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ltr559 = ltr559 or LTR559()

    def raw_read(self) -> float:
        return self.ltr559.get_lux()  # if proximity < 10 else 1


class ProximitySensor(Sensor):
    name = 'proximity'
    unit = 'mm'
    bins = (-1, 10, 100, 1500)
    last_page: float

    def __init__(self, *args, ltr559: LTR559 = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ltr559 = ltr559 or LTR559()
        self.last_page = time()

    def raw_read(self) -> float:
        return self.ltr559.get_proximity()

    def check_press(self):
        """Use the proximity sensor as a button: check if it has been "pressed" for more than
        PROXIMITY_DELAY seconds.
        """
        if self.read() > 1500 and time() - self.last_page > PROXIMITY_DELAY:
            self.last_page = time()
            return True
        return False
