#!/usr/bin/env python3

import colorsys
import logging
import subprocess
from abc import abstractmethod
from collections import deque
from time import sleep, time
from typing import Tuple

from bme280 import BME280
from enviroplus.noise import Noise
from fonts.ttf import RobotoMedium as UserFont
from ltr559 import LTR559
from numpy import digitize
from PIL import Image, ImageDraw, ImageFont
from ST7735 import ST7735

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


# Sensor settings
CPU_TEMP_FACTOR = 2.25  # Factor for compensation of CPU temperature
HISTORY_LEN = 5  # Number of sensor readings to keep in history
PROXIMITY_DELAY = 0.5  # Proximity sensor delay for cycling modes

# Display settings
COLUMN_COUNT = 1  # Display columns for 'combined' mode
TOP_POS = 25  # Position of the top bar

# Font settings
FONT_SIZE = 20
FONT_SIZE_SMALL = 10
FONT = ImageFont.truetype(UserFont, FONT_SIZE)
FONT_SMALL = ImageFont.truetype(UserFont, FONT_SIZE_SMALL)
X_OFFSET = 2
Y_OFFSET = 2

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


class Display(ST7735):
    def __init__(self, **kwargs):
        super().__init__(
            port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000, **kwargs
        )
        self.begin()
        self.img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)

    def new_frame(self):
        self.draw.rectangle(
            (0, 0, self.width, self.height),
            (0, 0, 0),
        )

    def draw_frame(self):
        self.display(self.img)

    def add_metric(self, x, y, text, color):
        self.draw.text((x, y), text, fill=color, font=FONT_SMALL)


class Enviro:
    def __init__(self):
        # Reuse sensor interfaces used for multiple metrics
        bme280 = BME280()
        ltr559 = LTR559()

        self.sensors: Tuple[Sensor] = (
            TemperatureSensor(bme280=bme280),
            PressureSensor(bme280=bme280),
            HumiditySensor(bme280=bme280),
            LightSensor(ltr559=ltr559),
            NoiseSensor(),
        )

        self.proximity = ProximitySensor(ltr559=ltr559)
        self.mode = 0

        sleep(0.5)
        self.display = Display()


# Displays all the text on the 0.96' LCD
def display_everything(enviro: Enviro):
    enviro.display.new_frame()
    row_count = len(enviro.sensors) / COLUMN_COUNT
    row_size = enviro.display.height / row_count
    col_size = int(enviro.display.width / COLUMN_COUNT)

    for i, sensor in enumerate(enviro.sensors):
        x = X_OFFSET + (col_size * (i // row_count))
        y = Y_OFFSET + (row_size * (i % row_count))

        sensor.read()
        enviro.display.add_metric(x, y, str(sensor), sensor.color())
        logger.info(str(sensor))

    enviro.display.draw_frame()


if __name__ == '__main__':
    enviro = Enviro()
    try:
        while True:
            display_everything(enviro)
            sleep(0.5)
    except KeyboardInterrupt:
        exit(0)
