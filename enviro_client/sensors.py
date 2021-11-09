import subprocess
from abc import abstractmethod
from collections import deque
from time import time
from typing import Tuple

from bme280 import BME280
from enviroplus.noise import Noise
from ltr559 import LTR559
from numpy import digitize

# Sensor settings
CPU_TEMP_FACTOR = 2.25  # Factor for compensation of CPU temperature
HISTORY_LEN = 5  # Number of sensor readings to keep in history
PROXIMITY_DELAY = 0.5  # Proximity sensor delay for cycling modes

# RGB palette for coloring values by "bin"
BIN_COLORS = [
    (0, 0, 255),  # Very Low
    (0, 255, 255),  # Low
    (0, 255, 0),  # Normal
    (255, 255, 0),  # High
    (255, 0, 0),  # Very High
]


class Sensor:
    """Representation of sensor state and metadata"""

    name: str
    unit: str
    bins: Tuple[int, int, int, int]
    value: float
    history: deque[float]

    def __init__(self):
        self.history = deque([0] * HISTORY_LEN, maxlen=HISTORY_LEN)

    @property
    def value(self) -> float:
        return self.history[-1]

    @abstractmethod
    def raw_read(self):
        pass

    def read(self) -> float:
        value = self.raw_read()
        self.history.append(value)
        return value

    def average(self) -> float:
        return sum(self.history) / len(self.history)

    def color(self) -> Tuple[int, int, int]:
        """Get an RGB value corresponding to the current sensor value.
        Note: ``bins`` defines value ranges, and ``BIN_COLORS`` defines correponding colors.
        """
        color_idx = digitize(self.value, self.bins)
        return BIN_COLORS[color_idx]

    def __str__(self):
        return f'{self.name}: {self.value:.1f} {self.unit}'


class CPUTemperatureSensor(Sensor):
    name = 'temperature'
    unit = 'C'
    bins = (4, 18, 28, 35)

    def raw_read(self):
        """Get the temperature of the CPU for compensation"""
        output = subprocess.check_output(['vcgencmd', 'measure_temp'])
        # Output is in the format: "temp=39.5'C"
        value = output.decode().split('=')[-1].split("'")[0]
        return float(value)


class TemperatureSensor(Sensor):
    name = 'temperature'
    unit = 'C'
    bins = (4, 18, 28, 35)

    def __init__(self, bme280: BME280 = None):
        super().__init__()
        self.cpu_temp = CPUTemperatureSensor()
        self.bme280 = bme280 or BME280()

    def raw_read(self):
        """Get temperature, and smooth out with some averaging to decrease jitter"""
        self.cpu_temp.read()
        avg_cpu_temp = self.cpu_temp.average()
        raw_temp = self.bme280.get_temperature()
        return raw_temp - ((avg_cpu_temp - raw_temp) / CPU_TEMP_FACTOR)


class HumiditySensor(Sensor):
    name = 'humidity'
    unit = '%'
    bins = (20, 30, 60, 70)

    def __init__(self, bme280: BME280 = None):
        super().__init__()
        self.bme280 = bme280 or BME280()

    def raw_read(self) -> float:
        return self.bme280.get_humidity()


class PressureSensor(Sensor):
    name = 'pressure'
    unit = 'hPa'
    bins = (250, 650, 1013.25, 1015)

    def __init__(self, bme280: BME280 = None):
        super().__init__()
        self.bme280 = bme280 or BME280()

    def raw_read(self) -> float:
        return self.bme280.get_pressure()


class LightSensor(Sensor):
    name = 'light'
    unit = 'Lux'
    bins = (-1, -1, 30000, 100000)

    def __init__(self, ltr559: LTR559 = None):
        super().__init__()
        self.ltr559 = ltr559 or LTR559()

    def raw_read(self) -> float:
        return self.ltr559.get_lux()  # if proximity < 10 else 1


class ProximitySensor(Sensor):
    name = 'proximity'
    unit = 'mm'
    bins = (-1, 10, 100, 1500)
    last_page: float

    def __init__(self, ltr559: LTR559 = None):
        super().__init__()
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


class NoiseSensor(Sensor):
    name = 'noise'
    unit = 'dB'
    bins = (10, 20, 65, 85)

    def __init__(self, noise: Noise = None):
        super().__init__()
        self.noise = noise or Noise()

    def raw_read(self) -> float:
        measurements = self.noise.get_noise_profile()
        return measurements[-1] * 128
