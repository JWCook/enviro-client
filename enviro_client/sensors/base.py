from abc import abstractmethod
from collections import deque
from typing import Tuple

from loguru import logger
from numpy import digitize

from enviro_client.display import BLUE, CYAN, GREEN, RED, YELLOW, RGBColor

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
    """Base class for representing the state and metadata of a single sensor metric"""

    name: str
    unit: str
    bins: Tuple[float, float, float, float]
    history: deque[float]

    def __init__(self, history_len: int = HISTORY_LEN):
        logger.debug(f'Initializing {self.__class__.__name__}')
        self.history = deque([0] * history_len, maxlen=history_len)

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

    def bin_color(self) -> RGBColor:
        """Get an RGB value corresponding to the current sensor value.
        Note: ``bins`` defines value ranges, and ``BIN_COLORS`` defines correponding colors.
        """
        color_idx = digitize(self.value, self.bins)
        return BIN_COLORS[color_idx]

    def status(self) -> str:
        """Get a status message to display"""
        return f'{self.name}: {self.value:.1f} {self.unit}'
