import librosa
from pathlib import Path
import random
import numpy as np

"""
This file just loads a wav file for now

"""

files = ['kewgardens.wav', 'eastersunday.wav', 'hollandpark.wav', 'hollow.wav', 'satelite.wav', 'stairway.wav']

def load_wav_file(filename=None):
    if filename is None:
        filename = random.choice(files)

    directory = Path(__file__).parent.resolve()
    root = directory.parent
    path = root / 'assets' / filename

    if not path.exists():
        print(f"Couldnt not find {path}")
        return np.zeros(1024), []
    waveform, sample_rate = librosa.load(path, sr=44100, mono=True)

 # just fake chord to appease the gui for now
    fake_chord_data = [{
        "root": 0,
        "third": 0,
        "fifth": 0,
        "quality": "File",
        "note_name": filename
    }]
    return waveform, fake_chord_data