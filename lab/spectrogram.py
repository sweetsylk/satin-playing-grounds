import sys
import numpy as np
from pathlib import Path
import librosa
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel


class AudioVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Experiment")
        self.resize(800, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel("Loading Audio... please wait.")
        self.layout.addWidget(self.label)


        self.graph = pg.PlotWidget()
        self.graph.setBackground('k')
        self.layout.addWidget(self.graph)


        script_dir = Path(__file__).parent.resolve()
        project_root = script_dir.parent
        audio_path = project_root / 'assets' / 'KewGardens.wav'


        waveform, sample_rate = librosa.load(audio_path, sr=None, mono=True)


        stft = librosa.stft(waveform, n_fft=2048, hop_length=512)
        spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

        self.label.setText(f"Kew Garden ({len(waveform)} samples at {sample_rate}Hz)")


        self.img = pg.ImageItem()
        self.graph.addItem(self.img)


        self.img.setImage(spectrogram.T)


        colormap = pg.colormap.get('inferno')
        self.img.setLookupTable(colormap.getLookupTable())

        self.graph.setLabel('bottom', "Time Bins")
        self.graph.setLabel('left', "Frequency Bins")


# Run the App
app = QApplication(sys.argv)
window = AudioVisualizer()
window.show()
sys.exit(app.exec())