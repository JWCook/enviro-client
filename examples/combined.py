#!/usr/bin/env python)3

import colorsys
import logging
import sys
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

# Initialize display
sleep(1.0)
st7735 = ST7735(port=0, cs=1, dc=9, backlight=12, rotation=270, spi_speed_hz=10000000)
st7735.begin()
WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
font_size_small = 10
font_size_large = 20
font = ImageFont.truetype(UserFont, font_size_large)
smallfont = ImageFont.truetype(UserFont, font_size_small)
x_offset = 2
y_offset = 2

metrics = {
    'temperature': 'C',
    'pressure': 'hPa',
    'humidity': '%',
    'light': 'Lux',
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
limits = [
    [4, 18, 28, 35],
    [250, 650, 1013.25, 1015],
    [20, 30, 60, 70],
    [-1, -1, 30000, 100000],
]

# RGB palette for values on the combined screen
palette = [
    (0, 0, 255),  # Dangerously Low
    (0, 255, 255),  # Low
    (0, 255, 0),  # Normal
    (255, 255, 0),  # High
    (255, 0, 0),  # Dangerously High
]


# Displays data and text on the 0.96' LCD
def display_text(idx, data):
    metric = list(metrics)[idx]
    unit = metrics[metric]
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
    draw.text((0, 0), message, font=font, fill=(0, 0, 0))
    st7735.display(img)


def to_rgb(color):
    color = (1.0 - color) * 0.6
    return (int(x * 255.0) for x in colorsys.hsv_to_rgb(color, 1.0, 1.0))


# Saves the data to be used in the graphs later and prints to the log
def save_data(idx, data):
    metric = list(metrics)[idx]
    unit = metrics[metric]
    # Maintain length of list
    values[metric] = values[metric][1:] + [data]
    logging.info(f'{metric}: {data:.1f} {unit}')


# Displays all the text on the 0.96' LCD
def display_everything():
    draw.rectangle((0, 0, WIDTH, HEIGHT), (0, 0, 0))
    row_count = len(metrics) / COLUMN_COUNT
    for i, (metric, unit) in enumerate(metrics.items()):
        data_value = values[metric][-1]
        x = x_offset + ((WIDTH // COLUMN_COUNT) * (i // row_count))
        y = y_offset + ((HEIGHT / row_count) * (i % row_count))

        rgb = palette[0]
        for j, lim in enumerate(limits[i]):
            if data_value > lim:
                rgb = palette[j + 1]

        message = f'{metric[:4]}: {data_value:.1f} {unit}'
        draw.text((x, y), message, font=smallfont, fill=rgb)

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


def main():
    cpu_temp_history = [get_cpu_temperature()] * 5
    delay = 0.5  # Debounce the proximity tap
    mode = 4  # The starting mode
    last_page = 0

    for v in metrics:
        values[v] = [1] * WIDTH

    # The main loop
    try:
        while True:
            proximity = ltr559.get_proximity()

            # If the proximity crosses the threshold, toggle the mode
            if proximity > 1500 and time() - last_page > delay:
                mode += 1
                mode %= len(metrics) + 1
                last_page = time()

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

            # Everything on one screen
            elif mode == 4:
                # Temperature; Smooth out with some averaging to decrease jitter
                data = get_temperature(cpu_temp_history)
                save_data(0, data)
                display_everything()

                # Pressure
                raw_data = bme280.get_pressure()
                save_data(1, raw_data)
                display_everything()

                # Humidity
                raw_data = bme280.get_humidity()
                save_data(2, raw_data)

                # Light
                if proximity < 10:
                    raw_data = ltr559.get_lux()
                else:
                    raw_data = 1
                save_data(3, raw_data)
                display_everything()

    # Exit cleanly
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
