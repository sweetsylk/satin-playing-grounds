import sys
import numpy as np
import sounddevice as sd
from scipy import signal
import scipy.signal as wav
import librosa
from pathlib import Path
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer
import random


def test_audio():
    return



def white_noise(
        duration: float = 1.0,
        amplitude: float=0.5,
        sample_rate: int = 44100
) -> np.ndarray:
    n_samples = int(duration * sample_rate)
    noise = np.random.uniform(-1, 1, n_samples)
    noise *= amplitude
    return noise

def sine_tone(
        frequency: int=440,
        duration: float=1.0,
        amplitude:float=0.3,
        sample_rate:int=44100
) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = np.sin(2 * np.pi * frequency * t) * amplitude
    return audio

def square_tone(
        frequency: int=440,
        duration: float=1.0,
        amplitude:float=0.3,
        sample_rate:int=44100
) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sine_wave = np.sin(2 * np.pi * frequency * t) * amplitude

    audio = np.sign(sine_wave) * amplitude
    return audio

def triangle_tone(
        frequency: int=440,
        duration: float=1.0,
        amplitude:float=0.3,
        sample_rate:int=44100
) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = signal.sawtooth(2 * np.pi * frequency * t, 0.5) * amplitude

    return audio

def saw_tone(
        frequency: int = 440,
        duration: float = 1.0,
        amplitude: float = 0.3,
        sample_rate: int = 44100
) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = signal.sawtooth(2 * np.pi * frequency * t, 1) * amplitude
    return audio
def transpose(frequency, semitone):
    return frequency * np.power(2, (semitone/12))

def play_audio():
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    audio_path = project_root / 'assets' / 'KewGardens.wav'
    waveform, sample_rate = librosa.load(audio_path, sr=None, mono=True)
    return waveform




def chord_player(n):
    # this be playing major and minor chords
    chunk_parts = []
    wave_functions = [sine_tone, square_tone, triangle_tone, saw_tone] # our wavetables we can pick from

    frequencies = 440.0 * (2.0 ** ((np.arange(60, 97) - 69.0) / 12.0)) # this an array of all frequencies a4 to a8

    print("generating random ass textures")

    for i in range(n):
        pitch = np.random.choice(frequencies)
        root_frequency = pitch / np.power(2, (9 / 12)) # transposed down 9 semitones
        duration = 0.5

        # building our chords
        root_function = random.choice(wave_functions)
        third_function = random.choice(wave_functions)
        fifth_function = random.choice(wave_functions)
        root = root_function(root_frequency, duration)
        third_frequency = transpose(root_frequency, np.random.choice([3, 4])) # radomly can be major or minor
        third = third_function(third_frequency, duration)
        fifth_frequency = transpose(root_frequency, 7)
        fifth = fifth_function(fifth_frequency, duration)

        chord = (root + third + fifth) * 0.3
        chunk_parts.append(chord)

    full_song = np.concatenate(chunk_parts)
    return full_song

class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oscilliscope")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.graph = pg.PlotWidget()
        self.graph.setYRange(-1, 1)
        self.graph.setMouseEnabled(True, False)

        self.graph.showAxis('left', False)
        self.graph.showAxis('bottom', False)
        self.graph.showGrid(x=True, y=True, alpha=0.5)


        self.layout.addWidget(self.graph)

        self.buffer = chord_player(32)
        self.buffer_length = len(self.buffer)

        # cursor thing
        self.cursor = 0

        # each buffer we are dealing wid
        self.current_chunk = np.zeros(1024)


        # audio stream setup
        self.stream = sd.OutputStream(
            channels=1,
            blocksize=1024,  # chunk size
            samplerate=44100,
            callback=self.audio_callback  # can be called for sound data
        )
        self.stream.start()

        # for GUI
        self.timer = QTimer()
        self.timer.setInterval(30)  # roughly 30fps
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        self.phase = 0

    def audio_callback(self, outdata, frames, time, status):
        # this called by self.stream on a seperate thread
        if status:
            print(status)


        start = self.cursor
        end = self.cursor + frames


        if start >= self.buffer_length: # have we reached the end
            outdata.fill(0)
            self.current_chunk = np.zeros(frames)
            return

        if end > self.buffer_length: # if there are parts buffer cant cover
            remaining = self.buffer_length - start

            outdata[:remaining, 0] = self.buffer[start:]
            outdata[remaining:, 0] = 0 # padding

            # update the chunks
            self.current_chunk = np.zeros(frames)
            self.current_chunk[:remaining] = self.buffer[start:]

            self.cursor = self.buffer_length  # moving cursor along the buffers

        else:
            chunk = self.buffer[start:end]
            outdata[:, 0] = chunk
            self.current_chunk = chunk
            self.cursor += frames

    def update_plot(self):
        self.graph.clear()
        self.graph.plot(self.current_chunk, pen='c')



app = QApplication(sys.argv)
window = Oscilloscope()
window.show()
sys.exit(app.exec())