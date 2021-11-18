from abc import abstractmethod
from collections import deque
from threading import RLock
from time import time
from typing import Tuple, Type

from loguru import logger
from numpy import digitize

from ..display import BLUE, CYAN, GREEN, RED, YELLOW, RGBColor

# Default number of sensor readings to keep in history
HISTORY_LEN = 160

# RGB palette for coloring values by "bin"
BIN_COLORS = [
    BLUE,  # Very Low
    CYAN,  # Low
    GREEN,  # Normal
    YELLOW,  # High
    RED,  # Very High
]


class Sensor:
    """Base class for representing a sensor device"""

    metrics: list['Metric']
    metric_classes: list[Type['Metric']]
    sensor_api_class: Type

    def __init__(
        self,
        min_interval: float = 0.1,
        history_len: int = HISTORY_LEN,
    ):
        logger.debug(
            f'Initializing {self.__class__.__name__} with metrics: '
            f'{[cls.__name__ for cls in self.metric_classes]}'
        )
        sensor_api = self.sensor_api_class() if self.sensor_api_class else None
        self.metrics = [cls(sensor_api, min_interval, history_len) for cls in self.metric_classes]
        self.lock = RLock()

    def _read_all(self) -> list[float]:
        """Refresh and return all sensor values"""
        with self.lock:
            return [metric.read() for metric in self.metrics]

    def read_all_values(self) -> dict[str, float]:
        """Get a reading from all sensors in the format ``{sensor_name: value}``"""
        self._read_all()
        return {metric.name: metric.value for metric in self.metrics}

    def read_all_statuses(self) -> dict[str, RGBColor]:
        """Get a reading from all sensors for display, in the format ``{sensor_status: bin_color}``"""
        self._read_all()
        return {metric.format(): metric.bin_color() for metric in self.metrics}


class Metric:
    """Base class for representing the state and metadata of a single sensor metric

    Args:
        sensor_api: An interface to the sensor hardware, if applicable
        history_len: Number of sensor readings to keep in history
        min_interval: Minimum time between sensor readings, in seconds
    """

    name: str
    unit: str
    bins: Tuple[float, float, float, float]
    history: deque[float]
    sensor_api: object

    def __init__(self, sensor_api, min_interval: float, history_len: int):
        self.sensor_api = sensor_api
        self.history = deque([0] * history_len, maxlen=history_len)
        self.last_read = 0.0
        self.min_interval = min_interval

    @property
    def value(self) -> float:
        return self.history[-1]

    @abstractmethod
    def raw_read(self):
        pass

    def read(self) -> float:
        """Read the current sensor value. If the sensor has already been read within the minimum
        interval, the previous reading will be used.
        """
        if not self.last_read or time() - self.last_read >= self.min_interval:
            self.last_read = time()
            self.history.append(self.raw_read())
        else:
            logger.debug(f'Skipping read for {self.name}')
        return self.history[-1]

    def average(self) -> float:
        return sum(self.history) / len(self.history)

    def bin_color(self) -> RGBColor:
        """Get an RGB value corresponding to the current sensor value.
        Note: ``bins`` defines value ranges, and ``BIN_COLORS`` defines correponding colors.
        """
        color_idx = digitize(self.value, self.bins)
        return BIN_COLORS[color_idx]

    def format(self) -> str:
        """Get a formatted status message to display"""
        return f'{self.name}: {self.value:.1f} {self.unit}'
