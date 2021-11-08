#!/usr/bin/env python3

import colorsys
import logging
import sys
from queue import Queue
from subprocess import PIPE, Popen
from time import sleep, time

from bme280 import BME280
from enviroplus.noise import Noise
from fonts.ttf import RobotoMedium as UserFont
from ltr559 import LTR559
from PIL import Image, ImageDraw, ImageFont
from ST7735 import ST7735

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
)

logging.info('Press Ctrl+C to exit!')

COLUMN_COUNT = 1  # Display columns for 'combined' mode
TOP_POS = 25  # Position of the top bar
PROX_DELAY = 0.5  # Proximity sensor delay for cycling mode

# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
CPU_TEMP_FACTOR = 2.25

# Sensors
bme280 = BME280()  # BME280 temperature/pressure/humidity sensor
ltr559 = LTR559()  # LTR559 light/proximity sensor
noise = Noise()  # ADS1015 noise sensor

# Initialize display
sleep(1.0)
st7735 = ST7735(port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000)
st7735.begin()
WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
FONT_SIZE = 20
FONT_SIZE_SMALL = 10
FONT = ImageFont.truetype(UserFont, FONT_SIZE)
FONT_SMALL = ImageFont.truetype(UserFont, FONT_SIZE_SMALL)
X_OFFSET = 2
Y_OFFSET = 2

METRICS = {
    'temperature': 'C',
    'pressure': 'hPa',
    'humidity': '%',
    'light': 'Lux',
    'noise': 'dB',
}
values = {}

# Define your own warning limits
# The limits definition follows the order of the metrics array
# Example limits explanation for temperature:
# [4,18,28,35] means
# [-273.15 .. 4] -> Dangerously Low
# (4 .. 18]      -> Low
# (18 .. 28]     -> Normal
# (28 .. 35]     -> High
# (35 .. MAX]    -> Dangerously High
LIMITS = [
    [4, 18, 28, 35],
    [250, 650, 1013.25, 1015],
    [20, 30, 60, 70],
    [-1, -1, 30000, 100000],
    [10, 20, 65, 85],
]

# RGB palette for values on the combined screen
PALETTE = [
    (0, 0, 255),  # Dangerously Low
    (0, 255, 255),  # Low
    (0, 255, 0),  # Normal
    (255, 255, 0),  # High
    (255, 0, 0),  # Dangerously High
]


# Displays data and text on the 0.96' LCD
def display_text(idx, data):
    metric = list(METRICS)[idx]
    unit = METRICS[metric]
    message = f'{metric}: {data:.1f} {unit}'
    logging.info(message)

    # Maintain length of list
    values[metric] = values[metric][1:] + [data]

    # Scale the values for the metric between 0 and 1
    vmin = min(values[metric])
    vmax = max(values[metric])
    colors = [(v - vmin + 1) / (vmax - vmin + 1) for v in values[metric]]

    draw.rectangle((0, 0, WIDTH, HEIGHT), (255, 255, 255))
    for i, color in enumerate(colors):
        r, g, b = to_rgb(color)
        # Draw a 1-pixel wide rectangle of color
        draw.rectangle((i, TOP_POS, i + 1, HEIGHT), (r, g, b))
        # Draw a line graph in black
        line_y = HEIGHT - (TOP_POS + (color * (HEIGHT - TOP_POS))) + TOP_POS
        draw.rectangle((i, line_y, i + 1, line_y + 1), (0, 0, 0))

    # Write the text at the top in black
    draw.text((0, 0), message, font=FONT, fill=(0, 0, 0))
    st7735.display(img)


def to_rgb(color):
    color = (1.0 - color) * 0.6
    return (int(x * 255.0) for x in colorsys.hsv_to_rgb(color, 1.0, 1.0))


# Saves the data to be used in the graphs later and prints to the log
def save_data(idx, data):
    metric = list(METRICS)[idx]
    unit = METRICS[metric]
    # Maintain length of list
    values[metric] = values[metric][1:] + [data]
    logging.info(f'{metric}: {data:.1f} {unit}')


# Displays all the text on the 0.96' LCD
def display_everything():
    draw.rectangle((0, 0, WIDTH, HEIGHT), (0, 0, 0))
    row_count = len(METRICS) / COLUMN_COUNT
    row_size = HEIGHT / row_count
    col_size = WIDTH // COLUMN_COUNT
    for i, (metric, unit) in enumerate(METRICS.items()):
        data_value = values[metric][-1]
        x = X_OFFSET + (col_size * (i // row_count))
        y = Y_OFFSET + (row_size * (i % row_count))

        rgb = PALETTE[0]
        for j, lim in enumerate(LIMITS[i]):
            if data_value > lim:
                rgb = PALETTE[j + 1]

        message = f'{metric[:4]}: {data_value:.1f} {unit}'
        draw.text((x, y), message, font=FONT_SMALL, fill=rgb)

    st7735.display(img)


def get_temperature(cpu_temp_history):
    """Get temperature, and smooth out with some averaging to decrease jitter"""
    cpu_temp = get_cpu_temperature()
    cpu_temp_history = cpu_temp_history[1:] + [cpu_temp]
    avg_cpu_temp = sum(cpu_temp_history) / float(len(cpu_temp_history))
    raw_temp = bme280.get_temperature()
    return raw_temp - ((avg_cpu_temp - raw_temp) / CPU_TEMP_FACTOR)


def get_cpu_temperature():
    """Get the temperature of the CPU for compensation"""
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1 : output.rindex("'")])


def get_ambient_noise():
    measurements = noise.get_noise_profile()
    return measurements[-1] * 128


def show_noise_profile(disp, draw, img):
    """Show a simple noise profile.

    This example grabs a basic 3-bin noise profile of low, medium and high frequency noise, plotting the noise characteristics as colored bars.
    """
    low, mid, high, amp = noise.get_noise_profile()

    img2 = img.copy()
    draw.rectangle((0, 0, disp.width, disp.height), (0, 0, 0))
    img.paste(img2, (1, 0))
    draw.line(
        (0, 0, 0, amp * 64),
        fill=(int(low * 128), int(mid * 128), int(high * 128)),
    )

    disp.display(img)


def check_mode(mode, last_page):
    """If the proximity crosses the threshold, toggle the mode"""
    proximity = ltr559.get_proximity()
    if proximity > 1500 and time() - last_page > PROX_DELAY:
        mode += 1
        mode %= len(METRICS) + 1
        last_page = time()
    return mode, proximity, last_page


def draw_frame(mode, last_page, cpu_temp_history):
    mode, proximity, last_page = check_mode(mode, last_page)

    # Temperature
    if mode == 0:
        data = get_temperature(cpu_temp_history)
        display_text(mode, data)

    # Pressure
    elif mode == 1:
        data = bme280.get_pressure()
        display_text(mode, data)

    # Humidity
    elif mode == 2:
        data = bme280.get_humidity()
        display_text(mode, data)

    # Light
    elif mode == 3:
        data = ltr559.get_lux() if proximity < 10 else 1
        display_text(mode, data)

    # Noise
    elif mode == 4:
        data = get_ambient_noise()
        display_text(mode, data)

    # Everything on one screen
    elif mode == 5:
        # Temperature; Smooth out with some averaging to decrease jitter
        data = get_temperature(cpu_temp_history)
        save_data(0, data)
        display_everything()

        # Pressure
        data = bme280.get_pressure()
        save_data(1, data)
        display_everything()

        # Humidity
        data = bme280.get_humidity()
        save_data(2, data)
        display_everything()

        # Light
        if proximity < 10:
            data = ltr559.get_lux()
        else:
            data = 1
        save_data(3, data)
        display_everything()

        # Noise
        data = get_ambient_noise()
        save_data(4, data)
        display_everything()


def main():
    cpu_temp_history = [get_cpu_temperature()] * 5
    mode = 5
    last_page = 0
    for v in METRICS:
        values[v] = [1] * WIDTH

    try:
        while True:
            draw_frame(mode, last_page, cpu_temp_history)
            sleep(0.5)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
