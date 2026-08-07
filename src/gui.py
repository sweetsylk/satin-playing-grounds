from enum import Enum, auto

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QLabel, QPushButton, QComboBox, QSpinBox, QSlider,
                             QTabWidget, QGroupBox)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence

import theme
from audio_engine import find_note
from audio_player import AudioPlayer
from audio_controller import PlaybackController


"""
This just deals with the visual elements of all this
"""


class PlayState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class DragValueBox(QLabel):
    valueChanged = pyqtSignal(int)
    sliderReleased = pyqtSignal()

    def __init__(self, min_val, max_val, default_val, snap_step=None, snap_threshold=0):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = default_val


        self.snap_step = snap_step
        self.snap_threshold = snap_threshold

        self.drag_start_y = 0
        self.drag_start_value = default_val

        self.setStyleSheet(theme.DRAG_VALUE_BOX_STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setToolTip("Drag up/down or scroll to change value")

    def set_value(self, val):
        clamped = max(self.min_val, min(self.max_val, val))
        if self.snap_step:
            nearest_step = round(clamped / self.snap_step) * self.snap_step
            if abs(clamped - nearest_step) <= self.snap_threshold:
                clamped = nearest_step
        if clamped != self.current_value:
            self.current_value = clamped
            self.valueChanged.emit(self.current_value)

    def value(self):
        return self.current_value

    def setValue(self, val):
        self.set_value(val)

    def wheelEvent(self, event):
        delta = event.angleDelta().y() // 120
        self.set_value(self.current_value + delta * 10)
        self.sliderReleased.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_y = event.pos().y()
            self.drag_start_value = self.current_value

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta_y = self.drag_start_y - event.pos().y()
            self.set_value(self.drag_start_value + delta_y * 2)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.sliderReleased.emit()


class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio thing")
        self.resize(920, 700)
        self.setMinimumSize(760, 560)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(10)

        self.player = AudioPlayer()
        self.chord_data = []
        self.samples_per_chord = 0
        self.current_filename = None
        self.state = PlayState.STOPPED

        self.info_label = QLabel("Ready")
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        self.layout.addWidget(self.info_label)


        self._init_transport_bar()


        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(theme.TAB_WIDGET_STYLE)

        self.tab_main = QWidget()
        self.tab_fx = QWidget()

        self.tabs.addTab(self.tab_main, "Main Controls")
        self.tabs.addTab(self.tab_fx, "Effects")

        self.main_tab_layout = QVBoxLayout(self.tab_main)
        self.main_tab_layout.setSpacing(10)
        self.fx_tab_layout = QVBoxLayout(self.tab_fx)
        self.fx_tab_layout.setSpacing(10)

        self.layout.addWidget(self.tabs)

        self.graph = pg.PlotWidget()
        self.graph.setYRange(-1, 1)
        self.graph.showAxis('left', False)
        self.graph.showAxis('bottom', False)
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.layout.addWidget(self.graph, stretch=1)

        self._init_source_controls()
        self._init_speed_controls()
        self._init_downsample_controls()
        self._init_flanger_controls()

        self.controller = PlaybackController(self)
        self.play_button.clicked.connect(self.handle_play_pause)
        self.wave_combo.currentIndexChanged.connect(self.force_play)
        self.downsample_slider.sliderReleased.connect(lambda: self.controller.start_playback(keep_position=True))
        self.select_file_btn.clicked.connect(self.controller.select_file)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self).activated.connect(self.handle_play_pause)

        self.timer = QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def _init_transport_bar(self):
        self.top_transport_layout = QHBoxLayout()
        self.top_transport_layout.setSpacing(10)

        self.play_button = QPushButton("go for it")
        self.play_button.setMinimumHeight(40)
        self.play_button.setMinimumWidth(120)
        self.play_button.setStyleSheet(theme.play_button_style(is_active=False))
        self.play_button.setToolTip("Play / Pause  (Space)")
        self.top_transport_layout.addWidget(self.play_button)

        self.loop_button = QPushButton("Loop: OFF")
        self.loop_button.setMinimumHeight(40)
        self.loop_button.setCheckable(True)
        self.loop_button.setStyleSheet(theme.toggle_style(is_on=False))
        self.loop_button.clicked.connect(self.toggle_loop)
        self.top_transport_layout.addWidget(self.loop_button)

        self.top_transport_layout.addStretch()

        vol_icon = QLabel("Vol")
        vol_icon.setStyleSheet("color: #aaa; font-size: 13px;")
        self.top_transport_layout.addWidget(vol_icon)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(140)
        self.volume_slider.valueChanged.connect(self.update_volume)
        self.top_transport_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("50%")
        self.volume_label.setFixedWidth(38)
        self.top_transport_layout.addWidget(self.volume_label)

        self.layout.addLayout(self.top_transport_layout)

    def _init_source_controls(self):
        group = QGroupBox("Source")
        row = QHBoxLayout()
        row.setSpacing(10)

        self.bpm_input = QSpinBox()
        self.bpm_input.setRange(40, 300)
        self.bpm_input.setValue(120)
        self.bpm_input.valueChanged.connect(lambda: self.update_speed(self.speed_slider.value()))
        row.addWidget(QLabel("BPM:"))
        row.addWidget(self.bpm_input)

        self.root_combo = QComboBox()
        self.root_combo.addItems(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        row.addWidget(QLabel("Key:"))
        row.addWidget(self.root_combo)

        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Major", "Minor"])
        row.addWidget(self.scale_combo)

        self.wave_combo = QComboBox()
        self.wave_combo.addItems([
            "Random (All)", "Sine", "Square", "Triangle", "Saw",
            "Sine + Triangle", "Square + Saw", "White Noise",
            "play file"
        ])
        row.addWidget(QLabel("Wave:"))
        row.addWidget(self.wave_combo)

        row.addStretch()

        self.select_file_btn = QPushButton("Load File...")
        self.select_file_btn.setToolTip("Pick a .wav file and switch to it")
        row.addWidget(self.select_file_btn)

        group.setLayout(row)
        self.main_tab_layout.addWidget(group)

    def _init_speed_controls(self):
        group = QGroupBox("Speed && Pitch")
        row = QHBoxLayout()
        row.setSpacing(10)

        self.speed_slider = DragValueBox(100, 2000, 1000)
        self.speed_slider.setToolTip("Drag up/down or scroll to change speed")
        self.speed_slider.valueChanged.connect(self.update_speed)
        self.speed_slider.valueChanged.connect(self.update_player_rate)

        self.cents_slider = DragValueBox(-4000, 1200, 0, snap_step=100, snap_threshold=8)
        self.cents_slider.setToolTip(
            "Drag up/down or scroll to change pitch in cents\n"
            "(snaps near exact semitones)")
        self.cents_slider.valueChanged.connect(self.update_from_cents)

        self.effective_bpm_label = QLabel("")
        self.effective_bpm_label.setStyleSheet("color: #aaa; font-size: 12px;")

        row.addWidget(QLabel("Speed:"))
        row.addWidget(self.speed_slider)
        row.addWidget(QLabel("Pitch:"))
        row.addWidget(self.cents_slider)
        row.addWidget(self.effective_bpm_label)
        row.addStretch()

        group.setLayout(row)
        self.main_tab_layout.addWidget(group)
        self.main_tab_layout.addStretch()
        self.update_speed(1000)

    def _init_downsample_controls(self):
        group = QGroupBox("Bitcrush / Downsample")
        row = QHBoxLayout()
        row.setSpacing(10)

        self.downsample_label = QLabel("Quality: normal")
        self.downsample_label.setFixedWidth(120)

        self.downsample_slider = QSlider(Qt.Orientation.Horizontal)
        self.downsample_slider.setMinimum(1)
        self.downsample_slider.setMaximum(44100)
        self.downsample_slider.setValue(44100)
        self.downsample_slider.setToolTip("Lower = more lo-fi / aliased")
        self.downsample_slider.valueChanged.connect(self.update_downsample)
        self.downsample_slider.sliderReleased.connect(lambda: self.controller.start_playback(keep_position=True))

        row.addWidget(self.downsample_slider)
        row.addWidget(self.downsample_label)

        group.setLayout(row)
        self.fx_tab_layout.addWidget(group)

    def _init_flanger_controls(self):
        group = QGroupBox("Flanger")
        outer = QVBoxLayout()
        outer.setSpacing(8)

        self.flanger_button = QPushButton("Flanger: OFF")
        self.flanger_button.setMinimumHeight(36)
        self.flanger_button.setCheckable(True)
        self.flanger_button.setStyleSheet(theme.toggle_style(is_on=False) + " padding: 0px 15px;")
        self.flanger_button.clicked.connect(self.toggle_flanger)
        outer.addWidget(self.flanger_button)

        sliders = QHBoxLayout()
        sliders.setSpacing(10)

        self.flanger_rate_label = QLabel("Rate: 0.5 Hz")
        self.flanger_rate_label.setFixedWidth(110)

        self.flanger_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.flanger_rate_slider.setMinimum(1)
        self.flanger_rate_slider.setMaximum(100)
        self.flanger_rate_slider.setValue(5)
        self.flanger_rate_slider.valueChanged.connect(self.update_flanger_rate)
        self.flanger_rate_slider.sliderReleased.connect(lambda: self.controller.start_playback(keep_position=True))

        self.flanger_depth_label = QLabel("Depth: 4 ms")
        self.flanger_depth_label.setFixedWidth(90)
        self.flanger_depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.flanger_depth_slider.setMinimum(1)
        self.flanger_depth_slider.setMaximum(20)
        self.flanger_depth_slider.setValue(4)
        self.flanger_depth_slider.valueChanged.connect(self.update_flanger_depth)
        self.flanger_depth_slider.sliderReleased.connect(lambda: self.controller.start_playback(keep_position=True))

        sliders.addWidget(QLabel("LFO"))
        sliders.addWidget(self.flanger_rate_slider)
        sliders.addWidget(self.flanger_rate_label)
        sliders.addWidget(self.flanger_depth_slider)
        sliders.addWidget(self.flanger_depth_label)
        outer.addLayout(sliders)

        group.setLayout(outer)
        self.fx_tab_layout.addWidget(group)
        self.fx_tab_layout.addStretch()

    def update_flanger_rate(self, value):
        self.flanger_rate_label.setText(f"Rate: {value / 10.0:.1f} Hz")

    def update_flanger_depth(self, value):
        self.flanger_depth_label.setText(f"Depth: {value} ms")

    def update_downsample(self, value):
        text = "Clean" if value > 44000 else f"{value} Hz"
        self.downsample_label.setText(f"Quality: {text}")

    def update_speed(self, value):
        float_percent = value / 10.0
        ratio = float_percent / 100.0
        cents = int(1200 * np.log2(ratio))
        effective_bpm = int(self.bpm_input.value() * ratio)

        self.speed_slider.setText(f"{float_percent:.1f}%")
        self.effective_bpm_label.setText(f"({effective_bpm} BPM)")

        self.cents_slider.blockSignals(True)
        self.cents_slider.setValue(cents)
        sign = "+" if cents >= 0 else ""
        self.cents_slider.setText(f"{sign}{cents}\u00a2")
        self.cents_slider.blockSignals(False)

    def update_from_cents(self, cents):
        ratio = 2 ** (cents / 1200.0)
        percent = ratio * 100.0
        percent = max(10.0, min(200.0, percent))
        slider_val = int(percent * 10)

        sign = "+" if cents >= 0 else ""
        self.cents_slider.setText(f"{sign}{cents}\u00a2")

        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(slider_val)
        self.speed_slider.setText(f"{percent:.1f}%")
        self.speed_slider.blockSignals(False)

        effective_bpm = int(self.bpm_input.value() * (percent / 100.0))
        self.effective_bpm_label.setText(f"({effective_bpm} BPM)")
        self.update_player_rate()

    def update_player_rate(self):
        value = self.speed_slider.value()
        speed_ratio = (value / 10.0) / 100.0
        self.player.update_rate(speed_ratio)

    def update_volume(self, value):
        self.volume_label.setText(f"{value}%")
        volume_float = value / 100.0
        self.player.set_volume(volume_float)

    def update_plot(self):
        chunk, cursor, buffer_len = self.player.get_state()
        self.graph.clear()
        self.graph.plot(chunk, pen=theme.PINK)

        if buffer_len == 0:
            return

        progress = (cursor / buffer_len) * 100
        index = int(cursor // self.samples_per_chord) if self.samples_per_chord > 0 else 0

        if index < len(self.chord_data):
            chord = self.chord_data[index]
            root, third, fifth = find_note(chord['root']), find_note(chord['third']), find_note(chord['fifth'])
            base = self.info_label.text().split("|")[0].strip()
            self.info_label.setText(
                f"{base} | {progress:.0f}% | {chord['note_name']} {chord['quality']} ({root},{third},{fifth})")
        else:
            self.info_label.setText("doneeee")
            # only reset to the "fresh start" look if playback ran out on its
            # own - if the user paused, we want to stay in the paused state
            if not self.player.is_playing and self.state != PlayState.PAUSED:
                self._set_state(PlayState.STOPPED)

    def toggle_loop(self, checked):
        self.player.looping = checked
        self.loop_button.setText("Loop: Yes" if checked else "Loop: Nah")
        self.loop_button.setStyleSheet(theme.toggle_style(is_on=checked))

    def toggle_flanger(self, checked):
        self.flanger_button.setText("flanger: ON" if checked else "flanger: OFF")
        self.flanger_button.setStyleSheet(theme.toggle_style(is_on=checked) + " padding: 0px 15px;")
        self.controller.start_playback(keep_position=True)

    def _set_state(self, new_state: PlayState):
        self.state = new_state
        if new_state == PlayState.PLAYING:
            self.play_button.setText("Pause")
            self.play_button.setStyleSheet(theme.play_button_style(is_active=True))
        elif new_state == PlayState.PAUSED:
            self.play_button.setText("Resume")
            self.play_button.setStyleSheet(theme.play_button_style(is_active=False))
        else:
            self.play_button.setText("go for it")
            self.play_button.setStyleSheet(theme.play_button_style(is_active=False))

    def handle_play_pause(self):
        if self.state == PlayState.PLAYING:
            self.player.is_playing = False
            self._set_state(PlayState.PAUSED)
        elif self.state == PlayState.PAUSED and self.player.buffer_length > 0:
            self.player.is_playing = True
            self._set_state(PlayState.PLAYING)
        else:
            self.controller.start_playback(keep_position=False)
            self._set_state(PlayState.PLAYING)

    def force_play(self):
        """switches whatever is playing rn if pauses switch but stay paused"""
        was_paused = self.state == PlayState.PAUSED
        self.controller.start_playback(keep_position=False)

        if was_paused:
            self.player.is_playing = False
            self._set_state(PlayState.PAUSED)
        else:
            self._set_state(PlayState.PLAYING)