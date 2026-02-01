import numpy as np
from scipy import signal
import random

"""
dealing with some DSP on this file
"""
PLAYBACK_RATE = 44100


def white_noise(frequency, duration, amplitude=0.3, sample_rate=PLAYBACK_RATE):
    n_samples = int(duration * sample_rate)
    noise = np.random.uniform(-1, 1, n_samples)
    noise *= amplitude
    return noise

def sine_tone(frequency, duration, amplitude=0.3, sample_rate=PLAYBACK_RATE):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t) * amplitude


def square_tone(frequency, duration, amplitude=0.3, sample_rate=PLAYBACK_RATE):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sign(np.sin(2 * np.pi * frequency * t)) * amplitude


def triangle_tone(frequency, duration, amplitude=0.3, sample_rate=PLAYBACK_RATE):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return signal.sawtooth(2 * np.pi * frequency * t, 0.5) * amplitude


def saw_tone(frequency, duration, amplitude=0.3, sample_rate=PLAYBACK_RATE):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return signal.sawtooth(2 * np.pi * frequency * t, 1) * amplitude


def get_scale(root_index, scale_type):
    start_note = 48 + root_index # c3 IS 48

    # major is WWHWWH minor is WHWWHWW
    if scale_type == "Major":
        intervals = [0, 2, 4, 5, 7, 9, 11]
    elif scale_type == "Minor":
        intervals = [0, 2, 3, 5, 7, 8, 10]

    scale = []
    for octave in range(4):
        for interval in intervals:
            note = start_note + (octave * 12) + interval
            scale.append(note)

    return np.array(scale)


def midi_to_frequency(midi_number):
    return 440.0 * (2.0 ** ((midi_number - 69.0) / 12.0))


def find_note(frequency):
    if frequency == 0: return "???"
    midi = 69 + 12 * np.log2(frequency / 440.0)
    midi = int(round(midi))
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi // 12) - 1
    note_index = midi % 12
    return f"{note_names[note_index]}{octave}"

def get_tone(wave_choice):
    if wave_choice == "Random (All)":
        pool = [sine_tone, square_tone, triangle_tone, saw_tone]
    elif wave_choice == "Sine":
        pool = [sine_tone]
    elif wave_choice == "Square":
        pool = [square_tone]
    elif wave_choice == "Triangle":
        pool = [triangle_tone]
    elif wave_choice == "Saw":
        pool = [saw_tone]
    elif wave_choice == "Sine + Triangle":
        pool = [sine_tone, triangle_tone]
    elif wave_choice == "Square + Saw":
        pool = [square_tone, saw_tone]
    elif wave_choice == "White Noise":
        pool = [white_noise]
    else:
        pool = [white_noise]
    return pool

def chord_player(n, bpm, root_index, scale_type, wave_choice, downsample_rate):
    chunk_parts = []
    chord_data = []
    pool = get_tone(wave_choice)
    scale = get_scale(root_index, scale_type)
    playable_indices = np.arange(0, len(scale) - 5)
    duration = 60 / bpm

    generation_rate = downsample_rate if downsample_rate else PLAYBACK_RATE
    print(f"Generating {n} chords ({wave_choice}) in {scale_type} at {bpm} BPM...")

    for i in range(n):
        root_index_scale = np.random.choice(playable_indices)
        third_index_scale = root_index_scale + 2
        fifth_index_scale = root_index_scale + 4

        root_midi = scale[root_index_scale]
        third_midi = scale[third_index_scale]
        fifth_midi = scale[fifth_index_scale]

        distance_third = third_midi - root_midi
        distance_fifth = fifth_midi - root_midi

        quality = "???"
        if distance_third == 4 and distance_fifth == 7:
            quality = "Maj"
        elif distance_third == 3 and distance_fifth == 7:
            quality = "Min"
        elif distance_third == 3 and distance_fifth == 6:
            quality = "Dim"
        elif distance_third == 4 and distance_fifth == 8:
            quality = "Aug"

        root_frequency = midi_to_frequency(root_midi)
        third_frequency = midi_to_frequency(third_midi)
        fifth_frequency = midi_to_frequency(fifth_midi)

        root_wave = random.choice(pool)(root_frequency, duration, sample_rate=generation_rate)
        third_wave = random.choice(pool)(third_frequency, duration, sample_rate=generation_rate)
        fifth_wave = random.choice(pool)(fifth_frequency, duration, sample_rate=generation_rate)

        chord_data.append({
            "root": root_frequency,
            "third": third_frequency,
            "fifth": fifth_frequency,
            "quality": quality,
            "note_name": find_note(root_frequency)
        })

        chord = (root_wave + third_wave + fifth_wave) * 0.3

        fade_len = min(100, len(chord) // 2)
        chord[:fade_len] *= np.linspace(0, 1, fade_len)
        chord[-fade_len:] *= np.linspace(1, 0, fade_len)

        if downsample_rate:
            # each sample gotta be repeating a (sample/ downsample) amount of times
            target_length = int(duration * PLAYBACK_RATE)
            step = PLAYBACK_RATE / downsample_rate
            indexes = np.arange(target_length) / step
            indexes = np.clip(indexes, 0, len(chord) - 1) # to prevent out of bound stuff
            chord = chord[indexes.astype(int)]

        chunk_parts.append(chord)

    full_song = np.concatenate(chunk_parts)
    return full_song, chord_data


"""
I used nearest neighbour downsampling for this again 
get a steps size then just take the first value in the array at each step
then from there just make all values within that step that value causing blocking need in wave form
it is gonna have some aliasing but that is intendd
"""

def apply_downsample(buffer, target_sample_rate, original_rate=44100):
    if not target_sample_rate or target_sample_rate >= original_rate:
        return buffer
    step_size = original_rate / target_sample_rate
    sample_indexes = np.arange(len(buffer))
    indexes = (np.floor(sample_indexes / step_size) * step_size).astype(int)
    indexes = np.clip(indexes, 0, len(buffer) - 1)
    return buffer[indexes]