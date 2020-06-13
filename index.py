import librosa
import numpy as np
from pydub import AudioSegment
from os import scandir
import shutil
import os

extension_file = '.wav'
path = 'audios/pending/'
decibels = 15
limit_min_second = 270
limit_max_second = 330
limit_second = 360


def read_audios(path):
    return [obj.name for obj in scandir(path) if obj.is_file()]


def move_file(file):
    global path, extension_file
    os.mkdir('audios/cut/' + file)
    shutil.move(path + file + extension_file, 'audios/cut/' + file + '/' + file + extension_file)


def extract_audio_detail(path, file):
    # Extrayendo información del audio
    name, extension = file.split('.')
    file_name = path + file
    song = AudioSegment.from_wav(file_name)
    audio, sr = librosa.load(file_name)
    duration_total_audio = librosa.core.get_duration(filename=file_name)
    # Se retorna el detalle del audio
    return [name, extension, song, audio, sr, duration_total_audio]


def get_intervals_not_silents_in_seconds(audio, sr):
    global decibels
    blocks = librosa.effects.split(audio, top_db=decibels)
    block_seconds = []
    for i in blocks:
        start, end = i
        second_start = round(start / sr, 2)
        second_end = round(end / sr, 2)
        block_seconds.append({'start': second_start, 'end': second_end})
    return block_seconds


def admitted_range(block_silences, start_audio, end, next_start):
    global limit_min_second, limit_max_second
    min_second = limit_min_second
    max_second = limit_max_second
    inside_the_range = False
    end_real = round(end - start_audio, 2)

    if (end_real >= min_second and end_real <= max_second):
        start_silence = round(end + 0.01, 2)
        end_silence = round(next_start - 0.01, 2)
        duration_silence = round(end_silence - start_silence, 2)

        silence = {'start': start_silence, 'end': end_silence, 'duration': duration_silence}
        block_silences.append(silence)

        inside_the_range = True

        print(silence)

    return [block_silences, inside_the_range]


def select_logest_silence(block_silences, silences, start_audio):
    max_silence = max(block_silences, key=lambda silencio: silencio["duration"])
    print("max silence", "----", max_silence)
    end = round(max_silence['start'] + round(max_silence['duration'] / 2, 2), 2)
    last_silence = {'start': start_audio, 'end': end}
    silences.append(last_silence)
    start_audio = end
    block_silences = []
    # print(max(silencio['duration'] for silencio in block_silencios))

    return [block_silences, silences, start_audio, last_silence]


def cut_audios(song, name, silences):
    count = 1
    move_file(name)
    for silence in silences:
        song[silence['start'] * 1000:silence['end'] * 1000].export(
            'audios/cut/' + name + '/' + name + '_00' + str(count) + '.wav', format='wav')
        count += 1


def build_silences(audio, sr, duration_total_audio):
    start_audio = 0
    block_silences = []
    silences = []
    last_silence = {}
    block_seconds = get_intervals_not_silents_in_seconds(audio, sr)  # audio above 20dB
    print(block_seconds)

    # Recorro los bloques de segundos
    for i, block in enumerate(block_seconds):
        print(block_seconds[i]['start'], '----', block_seconds[i]['end'])

        end = block['end']

        next_start = duration_total_audio if i + 1 > len(block_seconds) - 1 else block_seconds[i + 1]['start']

        if (last_silence != {}):
            segundos_restantes = round(duration_total_audio - last_silence['end'], 2)
            print('segundos restantes ', segundos_restantes)
            if (segundos_restantes <= limit_second):
                silences.append({'start': last_silence['end'], 'end': duration_total_audio})
                break

        block_silences, inside_the_range = admitted_range(block_silences, start_audio, end, next_start)
        if (inside_the_range == False and len(block_silences) > 0):
            block_silences, silences, start_audio, last_silence = select_logest_silence(block_silences,
                                                                                        silences, start_audio)
    return silences


def run():
    global extension_file, path, limit_min_second, limit_max_second, limit_second
    files = read_audios(path)
    for file in files:
        # Si el fichero es .wav entonces ejecuto la sentencia
        if file.find(extension_file) != -1:
            name, extension, song, audio, sr, duration_total_audio = extract_audio_detail(path, file)
            silences = build_silences(audio, sr, duration_total_audio)
            print("========================================================================")
            print('los bloques de silencios a cortar son los siguientes ', silences)
            cut_audios(song, name, silences)


run()
