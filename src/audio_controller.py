from dataclasses import dataclass
from pathlib import Path
from tkinter.filedialog import askopenfilename

from audio_loader import load_wav_file
from audio_engine import chord_player, apply_downsample, apply_flanger


@dataclass
class PlaybackResult:
    """the singular playback buffer and its infos"""
    audio_buffer: object
    chord_data: list
    samples_per_chord: int
    info_text: str


class PlaybackController:
    def __init__(self, main_window):
        self.view = main_window
        self.current_filepath = None

    def select_file(self):
        filename = askopenfilename(filetypes=[("WAV files", "*.wav")])
        if not filename:
            return

        self.current_filepath = filename
        combo = self.view.wave_combo
        index = combo.findText("play file")
        if index >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

        self.view.info_label.setText(f"File Ready: {Path(filename).stem}")
        self.view.force_play()

    def build_playback(self, keep_position):
        """Generating or loading the audio for the current settings but liek it  doesnt
        touch the player or view states"""
        bpm = self.view.bpm_input.value()
        root = self.view.root_combo.currentIndex()
        scale = self.view.scale_combo.currentText()
        wave = self.view.wave_combo.currentText()

        slider = self.view.downsample_slider.value()
        downsample_rate = None if slider > 44000 else slider

        if wave == "play file":
            if self.current_filepath is None:
                self.select_file()
                if self.current_filepath is None:
                    return None

            audio_buffer, chord_data = load_wav_file(self.current_filepath)
            if downsample_rate:
                audio_buffer = apply_downsample(audio_buffer, downsample_rate)

            samples_per_chord = len(audio_buffer)
            info_text = f"Playing File: {Path(self.current_filepath).stem}"
        else:
            self.current_filepath = None
            audio_buffer, chord_data = chord_player(
                32, bpm, root, scale, wave,
                downsample_rate=downsample_rate
            )
            samples_per_chord = int((60.0 / bpm) * 44100)

            quality_text = "Clean" if downsample_rate is None else f"{downsample_rate}Hz"
            key_name = f"{self.view.root_combo.currentText()} {scale}"
            info_text = f"Playing {key_name} | {wave} | {quality_text}"

        if self.view.flanger_button.isChecked():
            current_rate = self.view.flanger_rate_slider.value() / 10.0
            current_depth = self.view.flanger_depth_slider.value() / 1000.0
            audio_buffer = apply_flanger(audio_buffer, lfo_rate=current_rate, depth=current_depth)

        return PlaybackResult(audio_buffer, chord_data, samples_per_chord, info_text)

    def start_playback(self, keep_position=False):
        result = self.build_playback(keep_position)
        if result is None:
            return

        self.view.chord_data = result.chord_data
        self.view.samples_per_chord = result.samples_per_chord
        self.view.info_label.setText(result.info_text)
        if keep_position and self.view.player.buffer_length > 0:
            self.view.player.update_buffer(result.audio_buffer)
        else:
            self.view.player.play(result.audio_buffer)