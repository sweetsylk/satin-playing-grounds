from audio_engine import chord_player, apply_downsample
from audio_loader import load_wav_file

class PlaybackController:
    def __init__(self, main_window):
        self.view = main_window
        self.current_filename = None

    def start_playback(self, keep_position=False):
        bpm = self.view.bpm_input.value()
        root = self.view.root_combo.currentIndex()
        scale = self.view.scale_combo.currentText()
        wave = self.view.wave_combo.currentText()

        slider = self.view.downsample_slider.value()
        downsample_rate = None if slider > 44000 else slider

        audio_buffer = []

       # this just makes sure file does change upon effect changes
        if wave == "play file":
            if keep_position and self.current_filename is not None:
                file_to_load = self.current_filename
            else:
                file_to_load = None

            audio_buffer, self.view.chord_data = load_wav_file(file_to_load)

            if downsample_rate:
                audio_buffer = apply_downsample(audio_buffer, downsample_rate)

            if self.view.chord_data:
                self.current_filename = self.view.chord_data[0]['note_name']

            self.view.samples_per_chord = len(audio_buffer)
            self.view.info_label.setText(f"Playing File: {self.current_filename}")

        else:
            self.current_filename = None

            audio_buffer, self.view.chord_data = chord_player(
                32, bpm, root, scale, wave,
                downsample_rate=downsample_rate
            )
            self.view.samples_per_chord = int((60.0 / bpm) * 44100)

            quality_text = "Clean" if downsample_rate is None else f"{downsample_rate}Hz"
            key_name = f"{self.view.root_combo.currentText()} {scale}"
            self.view.info_label.setText(f"Playing {key_name} | {wave} | {quality_text}")
        if keep_position and self.view.player.is_playing:
            self.view.player.update_buffer(audio_buffer)
        else:
            self.view.player.play(audio_buffer)