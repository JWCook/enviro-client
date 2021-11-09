from fonts.ttf import RobotoMedium as UserFont
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
        self.begin()
        self.img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)

        self.n_rows = n_metrics // n_columns
        self.row_size = self.height // self.n_rows
        self.col_size = self.width // n_columns

    def new_frame(self):
        self.draw.rectangle(
            (0, 0, self.width, self.height),
            (0, 0, 0),
        )

    def draw_frame(self):
        self.display(self.img)

    def add_metric(self, idx, text, color):
        x = X_OFFSET + (self.col_size * (idx // self.n_rows))
        y = Y_OFFSET + (self.row_size * (idx % self.n_rows))
        self.draw.text((x, y), text, fill=color, font=FONT_SMALL)
