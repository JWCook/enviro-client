"""Interface for the
[SPH0645LM4H-B](https://www.knowles.com/docs/default-source/default-document-library/sph0645lm4h-1-datasheet.pdf)
microphone, for basic use as an ambient noise sensor.

Adapted from: https://github.com/pimoroni/enviroplus-python/blob/master/library/enviroplus/noise.py
"""
import numpy as np
import sounddevice

from .base import Sensor


class NoiseSensor(Sensor):
    name = 'noise'
    unit = 'dB'
    bins = (10, 20, 65, 85)

    def __init__(self, *args, sample_rate: int = 16000, duration: float = 0.5, **kwargs):
        """Noise measurement.

        Args:
            sample_rate: Sample rate in Hz
            duraton: Duration, in seconds, of noise sample capture
        """
        super().__init__(*args, **kwargs)
        self.duration = duration
        self.sample_rate = sample_rate

    def get_amplitude_at_frequency_range(self, start: int, end: int):
        """Return the mean amplitude of frequencies in the specified range.

        Args:
            start: Start frequency (in Hz)
            end: End frequency (in Hz)
        """
        n = self.sample_rate // 2
        if start > n or end > n:
            raise ValueError("Maxmimum frequency is {}".format(n))

        recording = self._record()
        magnitude = np.abs(np.fft.rfft(recording[:, 0], n=self.sample_rate))
        return np.mean(magnitude[start:end])

    def get_noise_profile(self, noise_floor=100, low=0.12, mid=0.36, high=None):
        """Returns a noise charateristic profile.

        Bins all frequencies into 3 weighted groups expressed as a percentage of the total frequency range.

        Args:
            noise_floor: "High-pass" frequency, exclude frequencies below this value
            low: Percentage of frequency ranges to count in the low bin (as a float, 0.5 = 50%)
            mid: Percentage of frequency ranges to count in the mid bin (as a float, 0.5 = 50%)
            high: Optional percentage for high bin, effectively creates a "Low-pass" if total percentage is less than 100%
        """
        if high is None:
            high = 1.0 - low - mid

        recording = self._record()
        magnitude = np.abs(np.fft.rfft(recording[:, 0], n=self.sample_rate))

        sample_count = (self.sample_rate // 2) - noise_floor

        mid_start = noise_floor + int(sample_count * low)
        high_start = mid_start + int(sample_count * mid)
        noise_ceiling = high_start + int(sample_count * high)

        amp_low = np.mean(magnitude[noise_floor:mid_start])
        amp_mid = np.mean(magnitude[mid_start:high_start])
        amp_high = np.mean(magnitude[high_start:noise_ceiling])
        amp_total = (amp_low + amp_mid + amp_high) / 3.0

        return amp_low, amp_mid, amp_high, amp_total

    def raw_read(self) -> float:
        measurements = self.get_noise_profile()
        return measurements[-1] * 128

    def _record(self):
        return sounddevice.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            blocking=True,
            channels=1,
            dtype='float64',
        )
