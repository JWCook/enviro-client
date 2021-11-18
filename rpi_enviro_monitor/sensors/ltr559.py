"""Interface for the
[LTR559](https://shop.pimoroni.com/products/ltr-559-light-proximity-sensor-breakout)
light/proximity sensor
"""
from time import time

from ltr559 import LTR559

from .base import Sensor, Metric

# Proximity sensor delay in seconds, for using as a "button"
PROXIMITY_DELAY = 0.5


class Light(Metric):
    name = 'light'
    unit = 'Lux'
    bins = (1000, 5000, 10000, 30000)

    # TODO: take proximity into account?
    def raw_read(self) -> float:
        return self.sensor_api.get_lux()  # if proximity < 10 else 1


class Proximity(Metric):
    name = 'proximity'
    unit = 'mm'
    bins = (-1, 10, 100, 1500)
    last_page: float

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_page = time()

    def raw_read(self) -> float:
        return self.sensor_api.get_proximity()

    def check_press(self):
        """Use the proximity sensor as a button: check if it has been "pressed" for more than
        PROXIMITY_DELAY seconds.
        """
        if self.read() > 1500 and time() - self.last_page > PROXIMITY_DELAY:
            self.last_page = time()
            return True
        return False


class LTR559Sensor(Sensor):
    metric_classes = [Light, Proximity]
    sensor_api_class = LTR559
