"""Interface for the
[BME280](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)
humidity, pressure, and temperature sensor
"""
import subprocess

from bme280 import BME280

from enviro_client.sensors import Sensor

CPU_TEMP_FACTOR = 2.25


class CPUTemperatureSensor(Sensor):
    """Interface to get CPU temperature via vcgencmd to compensate for its effect on temperature
    sensor readings
    """

    name = 'temperature'
    unit = 'C'
    bins = (4, 18, 28, 35)

    def raw_read(self):
        """Get the temperature of the CPU for compensation"""
        output = subprocess.check_output(['vcgencmd', 'measure_temp'])
        # Output is in the format: "temp=39.5'C"
        value = output.decode().split('=')[-1].split("'")[0]
        return float(value)


class HumiditySensor(Sensor):
    name = 'humidity'
    unit = '%'
    bins = (20, 30, 60, 70)

    def __init__(self, *args, bme280: BME280 = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.bme280 = bme280 or BME280()

    def raw_read(self) -> float:
        return self.bme280.get_humidity()


class PressureSensor(Sensor):
    name = 'pressure'
    unit = 'hPa'
    bins = (250, 650, 1013.25, 1015)

    def __init__(self, *args, bme280: BME280 = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.bme280 = bme280 or BME280()

    def raw_read(self) -> float:
        return self.bme280.get_pressure()


class TemperatureSensor(Sensor):
    name = 'temperature'
    unit = 'C'
    bins = (4, 18, 28, 35)

    def __init__(self, *args, bme280: BME280 = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cpu_temp = CPUTemperatureSensor()
        self.bme280 = bme280 or BME280()

    def raw_read(self):
        """Get temperature, with CPU temp compensation, and with some averaging to decrease jitter"""
        self.cpu_temp.read()
        avg_cpu_temp = self.cpu_temp.average()
        raw_temp = self.bme280.get_temperature()
        compensation = (avg_cpu_temp - raw_temp) / CPU_TEMP_FACTOR
        return raw_temp - compensation
