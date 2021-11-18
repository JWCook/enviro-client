"""Interface for the
[BME280](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)
humidity, pressure, and temperature sensor
"""
import subprocess

from bme280 import BME280

from .base import Sensor, Metric

CPU_TEMP_FACTOR = 2.0


class Humidity(Metric):
    name = 'humidity'
    unit = '%'
    bins = (20, 30, 50, 70)

    def raw_read(self) -> float:
        return self.sensor_api.get_humidity()


class Pressure(Metric):
    name = 'pressure'
    unit = 'hPa'
    bins = (970, 990, 1013.25, 1020)

    def raw_read(self) -> float:
        return self.sensor_api.get_pressure()


class Temperature(Metric):
    name = 'temperature'
    unit = 'C'
    bins = (4, 18, 28, 35)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cpu_temp = CPUTemperature(history_len=5)

    def raw_read(self):
        """Get temperature, with CPU temp compensation, and with some averaging to decrease jitter"""
        self.cpu_temp.read()
        avg_cpu_temp = self.cpu_temp.average()
        raw_temp = self.sensor_api.get_temperature()
        compensation = (avg_cpu_temp - raw_temp) / CPU_TEMP_FACTOR
        return raw_temp - compensation


class CPUTemperature(Metric):
    """Interface to get CPU temperature to compensate for its effect on sensor readings"""

    name = 'temperature'
    unit = 'C'
    bins = (4, 18, 28, 35)

    def raw_read(self):
        """Get the temperature of the CPU for compensation"""
        output = subprocess.check_output(['vcgencmd', 'measure_temp'])
        # Output is in the format: "temp=39.5'C"
        value = output.decode().split('=')[-1].split("'")[0]
        return float(value)


class BME280Sensor(Sensor):
    metric_classes = [Temperature, Pressure, Humidity]
    sensor_api_class = BME280
