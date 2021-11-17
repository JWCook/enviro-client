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
    def __init__(self, interval: float = 0.25, **kwargs):
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

    def _new_frame(self, fill: RGBColor = BG_BLACK):
        self.draw.rectangle((0, 0, self.width, self.height), fill=fill)

    def _draw_frame(self):
        self.display(self.canvas)

    def draw_list(self, text_and_colors: dict[str, RGBColor]):
        """Draw a list of colored lines of text"""
        self._new_frame()

        # TODO: Use multiple columns if needed (if/when adding enviro+ sensors)
        n_rows = len(text_and_colors) // N_COLUMNS
        row_size = self.height // len(text_and_colors)
        col_size = self.width // N_COLUMNS

        def get_text_coords(row):
            return (
                X_OFFSET + (col_size * (row // n_rows)),
                Y_OFFSET + (row_size * (row % n_rows)),
            )

        for row, (text, color) in enumerate(text_and_colors.items()):
            self.draw.text(get_text_coords(row), text, fill=color, font=FONT_MED)
        self._draw_frame()

    def draw_graph(self, text: str, values: Sequence[float]):
        """Draw a line graph with colored background"""
        self._new_frame(fill=BG_WHITE)
        for x, value in enumerate(_normalize(values)):
            self._draw_graph_value(x, value)
        self._draw_text_bar(text)
        self._draw_frame()

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
        self._new_frame()
        size_x, size_y = self.draw.textsize(text, FONT_MED)
        x = (self.width - size_x) / 2
        y = (self.height / 2) - (size_y / 2)
        self.draw.rectangle((0, 0, self.width, self.height), bg_color)
        self.draw.text((x, y), text, font=FONT_MED, fill=text_color)
        self._draw_frame()

    def off(self):
        """Clear the display and turn the backlight off"""
        self._new_frame()
        self._draw_frame()
        self.set_backlight(0)


def _normalize(values: Sequence[float]) -> List[float]:
    """Normalize the values between 0 and 1"""
    vmin, vmax = min(values), max(values)
    return [(v - vmin + 1) / (vmax - vmin + 1) for v in values]


def _value_to_rgb(value: float) -> RGBColor:
    """Translate a normalized sensor value to RGB"""
    value = (1.0 - value) * 0.6
    return tuple(round(v * 255) for v in hsv_to_rgb(value, 1.0, 1.0))  # type: ignore
