import librosa
from pathlib import Path
import numpy as np


"""
This file just loads a wav file for now

"""

def load_wav_file(filename):
    path = Path(filename)

    if not path.exists():
        print(f"Could not find {path}")
        return np.zeros(1024), []

    waveform, sample_rate = librosa.load(path, sr=44100, mono=True)

    # just fake chord to appease the gui for now
    fake_chord_data = [{
        "root": 0,
        "third": 0,
        "fifth": 0,
        "quality": "File",
        "note_name": path.stem
    }]

    return waveform, fake_chord_data