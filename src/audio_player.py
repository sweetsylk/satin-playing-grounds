import numpy as np
import sounddevice as sd
from dataclasses import dataclass

"""
This is meant to play back the audio from the engine/loader
"""


@dataclass(frozen=True)
class _BufferState:
    buffer: np.ndarray
    length: int


class AudioPlayer:
    def __init__(self, sample_rate=44100, blocksize=1024):
        self.default_rate = sample_rate
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.volume = 0.5

        self._state = _BufferState(np.zeros(blocksize), 0)

        self.cursor = 0.0
        self.playback_rate = 1.0

        self.is_playing = False
        self.looping = False
        self.current_chunk = np.zeros(blocksize)

        self._start_stream()

    @property
    def buffer(self):
        return self._state.buffer

    @property
    def buffer_length(self):
        return self._state.length

    def _start_stream(self):
        try:
            self.stream = sd.OutputStream(
                channels=1,
                blocksize=self.blocksize,
                samplerate=self.sample_rate,
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as e:
            print(f"Error starting stream: {e}")

    def update_rate(self, speed_ratio):
        self.playback_rate = speed_ratio

    def set_volume(self, value):
        self.volume = np.clip(value, 0.0, 1.0)

    def play(self, audio_data):

        self._state = _BufferState(audio_data, len(audio_data))
        self.cursor = 0.0
        self.is_playing = True

    def update_buffer(self, audio_data):
        new_state = _BufferState(audio_data, len(audio_data))
        if self.cursor >= new_state.length:
            self.cursor = 0.0
        self._state = new_state

    def get_state(self):
        return self.current_chunk, self.cursor, self.buffer_length

    def _audio_callback(self, output_data, frames, time, status):
        if status: print(status)

        state = self._state  # sinfular snapsjot
        buffer, buffer_length = state.buffer, state.length

        if not self.is_playing or (self.cursor >= buffer_length and not self.looping):
            output_data.fill(0)
            self.current_chunk = np.zeros(frames)
            self.is_playing = False
            return

        positions = self.cursor + np.arange(frames) * self.playback_rate

        # wrapping :)
        if self.looping:
            positions = positions % buffer_length
        else:
            valid_mask = positions < (buffer_length - 1)
            positions = positions[valid_mask]

        if len(positions) == 0:
            output_data.fill(0)
            self.current_chunk = np.zeros(frames)
            self.is_playing = False
            return

        i = positions.astype(int)
        j = i + 1

        if self.looping:
            j = j % buffer_length
        else:
            j = np.clip(j, 0, buffer_length - 1)

        fractions = positions - i

        chunk = (buffer[i] * (1.0 - fractions) +
                 buffer[j] * fractions) * self.volume

        output_data.fill(0)
        output_data[:len(chunk), 0] = chunk

        self.current_chunk = np.zeros(frames)
        self.current_chunk[:len(chunk)] = chunk


        self.cursor += frames * self.playback_rate
        if self.looping:
            self.cursor = self.cursor % buffer_length