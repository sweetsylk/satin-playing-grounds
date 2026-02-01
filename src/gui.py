import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QLabel, QPushButton, QComboBox, QSpinBox, QSlider)
from PyQt6.QtCore import QTimer, Qt
from audio_engine import chord_player, find_note, apply_downsample
from audio_player import AudioPlayer
from audio_controller import PlaybackController
from audio_loader import load_wav_file

"""
This just deals with the visual elements of all this
"""


class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio thing")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)


        self.layout = QVBoxLayout()
        self.main_layout.addLayout(self.layout)

        self.player = AudioPlayer()
        self.chord_data = []
        self.samples_per_chord = 0
        self.current_filename = None
        self.info_label = QLabel("Ready")
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        self.layout.addWidget(self.info_label)

        self._init_controls()

        self._init_speed_slider()
        self._init_downsample_slider()

        self.graph = pg.PlotWidget()
        self.graph.setYRange(-1, 1)
        self.graph.showAxis('left', False)
        self.graph.showAxis('bottom', False)
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.layout.addWidget(self.graph)

        self.play_button = QPushButton("go for it")
        self.play_button.setMinimumHeight(50)
        self.play_button.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #fc1c6e; color: white;")
        self.play_button.clicked.connect(self.start_playback)
        self.layout.addWidget(self.play_button)

        self._init_volume_slider()

        self.controller = PlaybackController(self)
        self.play_button.clicked.connect(lambda: self.controller.start_playback(keep_position=False))
        self.downsample_slider.sliderReleased.connect(lambda: self.controller.start_playback(keep_position=True))
        self.timer = QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def _init_volume_slider(self):
        self.volume_layout = QVBoxLayout()

        self.vol_label_top = QLabel("Vol")
        self.vol_label_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_layout.addWidget(self.vol_label_top)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.update_volume)
        self.volume_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignCenter)

        self.volume_label = QLabel("50%")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_layout.addWidget(self.volume_label)

        self.main_layout.addLayout(self.volume_layout)

    def _init_controls(self):
        self.controls_layout = QHBoxLayout()

        self.bpm_input = QSpinBox()
        self.bpm_input.setRange(40, 300)
        self.bpm_input.setValue(120)

        self.bpm_input.valueChanged.connect(lambda: self.update_speed(self.speed_slider.value()))
        self.controls_layout.addWidget(QLabel("BPM:"))
        self.controls_layout.addWidget(self.bpm_input)

        self.root_combo = QComboBox()
        self.root_combo.addItems(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        self.controls_layout.addWidget(QLabel("Key:"))
        self.controls_layout.addWidget(self.root_combo)

        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Major", "Minor"])
        self.controls_layout.addWidget(self.scale_combo)

        self.wave_combo = QComboBox()
        self.wave_combo.addItems([
            "Random (All)", "Sine", "Square", "Triangle", "Saw",
            "Sine + Triangle", "Square + Saw", "White Noise",
            "play file"
        ])
        self.controls_layout.addWidget(QLabel("the options:"))
        self.controls_layout.addWidget(self.wave_combo)

        self.layout.addLayout(self.controls_layout)

    def _init_speed_slider(self):
        self.speed_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: 100% (120 BPM)")
        self.speed_label.setFixedWidth(200)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.update_speed)
        self.speed_slider.sliderReleased.connect(self.update_player_rate)

        self.speed_layout.addWidget(QLabel("Speed:"))
        self.speed_layout.addWidget(self.speed_slider)
        self.speed_layout.addWidget(self.speed_label)
        self.layout.addLayout(self.speed_layout)

    def _init_downsample_slider(self):
        self.downsample_layout = QHBoxLayout()
        self.downsample_label = QLabel("Quality: normal")
        self.downsample_label.setFixedWidth(150)

        self.downsample_slider = QSlider(Qt.Orientation.Horizontal)
        self.downsample_slider.setMinimum(1000)
        self.downsample_slider.setMaximum(44100)
        self.downsample_slider.setValue(44100)
        self.downsample_slider.valueChanged.connect(self.update_downsample)
        self.downsample_slider.sliderReleased.connect(lambda: self.start_playback(keep_position=True))

        self.downsample_layout.addWidget(QLabel("downsampling:"))
        self.downsample_layout.addWidget(self.downsample_slider)
        self.downsample_layout.addWidget(self.downsample_label)
        self.layout.addLayout(self.downsample_layout)
        return
    def update_downsample(self, value):
        text = "Clean" if value > 44000 else f"{value} Hz"
        self.downsample_label.setText(f"Quality: {text}")

    def update_speed(self, value):
        base_bpm = self.bpm_input.value()
        ratio = value / 100.0
        effective_bpm = int(base_bpm * ratio)
        cents = 1200 * np.log2(ratio)
        self.speed_label.setText(f"Speed: {value}% ({effective_bpm} BPM)  {cents:+.0f} cents")

    def update_player_rate(self):
        value = self.speed_slider.value()
        speed_percent = value / 100.0
        new_rate = int(44100 * speed_percent)

        self.player.update_rate(new_rate)



    def update_volume(self, value):
        self.volume_label.setText(f"{value}%")
        volume_float = value / 100.0
        self.player.set_volume(volume_float)

    def update_plot(self):
        chunk, cursor, buffer_len = self.player.get_state()
        self.graph.clear()
        self.graph.plot(chunk, pen='#fc1c6e')


        if buffer_len == 0: return

        progress = (cursor / buffer_len) * 100
        index = cursor // self.samples_per_chord if self.samples_per_chord > 0 else 0

        if index < len(self.chord_data):
            chord = self.chord_data[index]
            root, third, fifth = find_note(chord['root']), find_note(chord['third']), find_note(chord['fifth'])
            base = self.info_label.text().split("|")[0].strip()
            self.info_label.setText(
                f"{base} | {progress:.0f}% | {chord['note_name']} {chord['quality']} ({root},{third},{fifth})")
        else:
            self.info_label.setText("doneeee")