import numpy as np
import sounddevice as sd

"""
This is meant to play back the audio from the engine/loader
"""
class AudioPlayer:
    def __init__(self, sample_rate=44100, blocksize=1024):
        self.default_rate = sample_rate
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.volume = 0.5

        self.buffer = np.zeros(blocksize)
        self.buffer_length = 0
        self.cursor = 0
        self.is_playing = False
        self.current_chunk = np.zeros(blocksize)

        self._start_stream()

    def _start_stream(self): # private FOR NOW LEAVE IT ALONE DONT FORGET
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

    def update_rate(self, new_rate):
        if self.stream.active:
            self.stream.stop()
        self.stream.close()

        self.sample_rate = new_rate
        self._start_stream()

    def set_volume(self, value):
        self.volume = np.clip(value, 0.0, 1.0)

    def play(self, audio_data):
        self.buffer = audio_data
        self.buffer_length = len(audio_data)
        self.cursor = 0
        self.is_playing = True

    def update_buffer(self, audio_data):
        new_len = len(audio_data)

        if self.cursor >= new_len:
            self.cursor = 0
        self.buffer = audio_data
        self.buffer_length = new_len

    def get_state(self):
        return self.current_chunk, self.cursor, self.buffer_length

    def _audio_callback(self, output_data, frames, time, status): # LEAVE THIS ALONE FOR NOW
        if status: print(status)

        if not self.is_playing or self.cursor >= self.buffer_length:
            output_data.fill(0)
            self.current_chunk = np.zeros(frames)
            return

        start = self.cursor
        end = self.cursor + frames

        if end > self.buffer_length:
            remaining = self.buffer_length - start
            output_data[:remaining, 0] = self.buffer[start:] * self.volume
            output_data[remaining:, 0] = 0

            self.current_chunk = np.zeros(frames)
            self.current_chunk[:remaining] = self.buffer[start:] * self.volume
            self.cursor = self.buffer_length
        else:
            chunk = self.buffer[start:end]
            output_data[:, 0] = chunk * self.volume
            self.current_chunk = chunk * self.volume
            self.cursor += frames