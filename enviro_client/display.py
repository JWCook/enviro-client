from colorsys import hsv_to_rgb
from typing import List, Sequence, Tuple

from fonts.ttf import RobotoMedium as UserFont
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from ST7735 import ST7735

RGBColor = Tuple[float, float, float]

# Display settings
N_COLUMNS = 1  # Display columns for 'combined' mode
TOP_POS = 20  # Position of the top bar

# Font settings
FONT_LG = ImageFont.truetype(UserFont, 16)
FONT_MED = ImageFont.truetype(UserFont, 12)
FONT_MED = ImageFont.truetype(UserFont, 10)
X_OFFSET = 2
Y_OFFSET = 2

BG_BLACK = (0, 0, 0)
BG_CYAN = (0, 170, 170)
BG_RED = (85, 15, 15)
BG_WHITE = (255, 255, 255)

BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)


class Display(ST7735):
    def __init__(
        self, n_metrics: int = 0, n_columns: int = N_COLUMNS, interval: float = 0.25, **kwargs
    ):
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
        self.canvas = Image.new('RGB', (self.width, self.height), color=BG_BLACK)
        self.draw = ImageDraw.Draw(self.canvas)
        self.interval = interval

        # TODO: Calculate this on each draw instead of requiring it up front
        self.n_rows = n_metrics // n_columns
        self.row_size = self.height // self.n_rows
        self.col_size = self.width // n_columns
        self._current_row = 0

    def new_frame(self, fill: RGBColor = BG_BLACK):
        self._current_row = 0
        self.draw.rectangle((0, 0, self.width, self.height), fill=fill)

    def draw_frame(self):
        self.display(self.canvas)

    def draw_all_metrics(self, status_colors: dict[str, RGBColor]):
        """Draw text for all provided metrics"""
        self.new_frame()
        for status, color in status_colors.items():
            self._draw_metric_text(status, color)
        self.draw_frame()

    def _draw_metric_text(self, text: str, text_color: RGBColor):
        """Draw text for a single metric"""
        x = X_OFFSET + (self.col_size * (self._current_row // self.n_rows))
        y = Y_OFFSET + (self.row_size * (self._current_row % self.n_rows))
        self.draw.text((x, y), text, fill=text_color, font=FONT_MED)
        self._current_row += 1

    def draw_graph(self, text: str, values: Sequence[float]):
        """Draw a line graph with colored background"""
        self.new_frame(fill=BG_WHITE)
        for x, value in enumerate(_normalize(values)):
            self._draw_graph_value(x, value)
        self._draw_text_bar(text)
        self.draw_frame()

    def _draw_graph_value(self, x: float, value: float):
        """Draw a 1-pixel wide bar, colored based on relative value, with a black pixel used to form
        a line graph
        """
        self.draw.rectangle((x, TOP_POS, x + 1, self.height), _value_to_rgb(value))
        line_y = self.height - (value * (self.height - TOP_POS))
        self.draw.rectangle((x, line_y, x + 1, line_y + 1), fill=BG_BLACK)

    def _draw_text_bar(self, text: str):
        """Display text using a status bar at the top of the screen"""
        self.draw.text((0, 0), text, font=FONT_LG, fill=BG_BLACK)

    def draw_text_box(
        self,
        text: str,
        text_color: RGBColor = BG_WHITE,
        bg_color: RGBColor = BG_CYAN,
    ):
        """Display text in a box using the whole screen"""
        self.new_frame()
        size_x, size_y = self.draw.textsize(text, FONT_MED)
        x = (self.width - size_x) / 2
        y = (self.height / 2) - (size_y / 2)
        self.draw.rectangle((0, 0, self.width, self.height), bg_color)
        self.draw.text((x, y), text, font=FONT_MED, fill=text_color)
        self.draw_frame()

    def off(self):
        """Clear the display and turn the backlight off"""
        self.new_frame()
        self.draw_frame()
        self.set_backlight(0)


def _normalize(values: Sequence[float]) -> List[float]:
    """Normalize the values between 0 and 1"""
    vmin, vmax = min(values), max(values)
    return [(v - vmin + 1) / (vmax - vmin + 1) for v in values]


def _value_to_rgb(value: float) -> RGBColor:
    """Translate a normalized sensor value to RGB"""
    value = (1.0 - value) * 0.6
    return tuple(round(v * 255) for v in hsv_to_rgb(value, 1.0, 1.0))  # type: ignore
