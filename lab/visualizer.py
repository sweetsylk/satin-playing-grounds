import sys
import numpy as np
from pathlib import Path
import librosa
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel


class AudioVisualizer(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("song")
        self.resize(800, 400)


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)


        self.label = QLabel("look at this")
        self.layout.addWidget(self.label)

        self.graph = pg.PlotWidget()
        self.graph.setBackground('k')
        self.graph.showGrid(x=True, y=True)
        self.layout.addWidget(self.graph)
        script_dir = Path(__file__).parent.resolve()
        project_root = script_dir.parent
        audio_path = project_root / 'assets' / 'kewgardens.wav'

        waveform, sample_rate = librosa.load(audio_path, sr=None, mono = True)
        self.label.setText(f"Kew Garden ({len(waveform)} samples at {sample_rate}Hz)")
        self.graph.plot(waveform, pen='c')
        self.graph.setMouseEnabled(True,False)
        self.graph.setYRange(-1, 1)


# Run the App
app = QApplication(sys.argv)
window = AudioVisualizer()
window.show()
sys.exit(app.exec())