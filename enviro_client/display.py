from colorsys import hsv_to_rgb
from typing import Tuple

from fonts.ttf import RobotoMedium as UserFont
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from ST7735 import ST7735

# Display settings
N_COLUMNS = 1  # Display columns for 'combined' mode
TOP_POS = 25  # Position of the top bar

# Font settings
FONT_SIZE = 20
FONT_SIZE_SMALL = 10
FONT = ImageFont.truetype(UserFont, FONT_SIZE)
FONT_SMALL = ImageFont.truetype(UserFont, FONT_SIZE_SMALL)
X_OFFSET = 2
Y_OFFSET = 2

BG_BLACK = (0, 0, 0)
BG_WHITE = (255, 255, 255)


class Display(ST7735):
    def __init__(self, n_metrics=0, n_columns=N_COLUMNS, **kwargs):
        super().__init__(
            port=0,
            cs=1,
            dc=9,
            backlight=12,
            rotation=270,
            spi_speed_hz=10000000,
            **kwargs,
        )
        logger.debug(f'Initializing {self.width}x{self.height} display')
        self.canvas = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.canvas)

        self.n_rows = n_metrics // n_columns
        self.row_size = self.height // self.n_rows
        self.col_size = self.width // n_columns
        self._current_row = 0

    def new_frame(self, fill=BG_BLACK):
        self._current_row = 0
        self.draw.rectangle((0, 0, self.width, self.height), fill=fill)

    def draw_frame(self):
        self.display(self.canvas)

    def draw_metric_text(self, text, color):
        """Draw text for a single metric"""
        x = X_OFFSET + (self.col_size * (self._current_row // self.n_rows))
        y = Y_OFFSET + (self.row_size * (self._current_row % self.n_rows))
        self.draw.text((x, y), text, fill=color, font=FONT_SMALL)
        self._current_row += 1

    def draw_graph(self, text, values):
        """Draw a line graph with colored background"""
        self.new_frame(fill=BG_WHITE)
        for x, value in enumerate(_normalize(values)):
            self._draw_graph_value(x, value)
        self._draw_text_bar(text)
        self.draw_frame()

    def _draw_graph_value(self, x, value):
        # Draw a 1-pixel wide bar, colored based on relative value
        self.draw.rectangle((x, TOP_POS, x + 1, self.height), _value_to_rgb(value))

        # Draw a single black pixel to form a line graph
        line_y = self.height - (value * (self.height - TOP_POS))
        self.draw.rectangle((x, line_y, x + 1, line_y + 1), fill=BG_BLACK)

    def _draw_text_bar(self, text):
        """Display text in the top bar"""
        self.draw.text((0, 0), text, font=FONT, fill=BG_BLACK)


def _normalize(values):
    """Normalize the values between 0 and 1"""
    vmin, vmax = min(values), max(values)
    return [(v - vmin + 1) / (vmax - vmin + 1) for v in values]


def _value_to_rgb(value: float) -> Tuple[int, int, int]:
    """Translate a normalized sensor value to RGB"""
    value = (1.0 - value) * 0.6
    return tuple(int(x * 255.0) for x in hsv_to_rgb(value, 1.0, 1.0))
