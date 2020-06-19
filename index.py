import librosa
import numpy as np
from pydub import AudioSegment
from os import scandir
import os.path
from os import path
import shutil
import os
import requests

extension_file_wav = '.wav'
pending_path = 'audios/pending/'
cut_path = 'audios/cut/'
decibels = 15
limit_min_second = 240
limit_max_second = 300
limit_second = 330
extension_file_audio = '.MP3'
extension_file_video = '.MP4'
api_url = 'http://localhost:5000/'


def read_audios(path):
    return [obj.name for obj in scandir(path) if obj.is_file()]


def convert(input, output):
    os.system('ffmpeg -i ' + input + ' ' + output)


def move_file(file, original_extension):
    global pending_path, cut_path
    shutil.move(pending_path + file + original_extension, cut_path + file + original_extension)


def extract_code_support(file_name):
    return file_name[8:10]


def extract_audio_detail(path, file):
    # Extrayendo información del audio
    temporal_name, extension = file.split('.')
    name, status, type = temporal_name.split('_')
    file_name = path + file
    song = AudioSegment.from_wav(file_name)
    audio, sr = librosa.load(file_name)
    duration_total_audio = librosa.core.get_duration(filename=file_name)
    code = extract_code_support(name)
    # Se retorna el detalle del audio
    return [name, extension, song, audio, sr, duration_total_audio, code, status, type]


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


def create_directory(directory_name):
    global cut_path
    directory = cut_path + directory_name
    if (os.path.isdir(directory) == False):
        os.mkdir(directory)
    return directory


def cut_audio(song, silence, base_name_file, path, original_extension, duration, code, hour_broadcast, status, type):
    global extension_file_wav
    file_exist = get_by_file_name(base_name_file)
    print("=========================BASE_NAME_FILE=====================")
    print(file_exist)
    print("============================================================")
    if file_exist['success'] == False:

        file_name_wav = path + '/' + base_name_file + extension_file_wav
        new_file_name = path + '/' + base_name_file + original_extension

        print("===========================FILE_NAME================================")
        print(file_name_wav)
        print("======================================================================")

        song[silence['start'] * 1000:silence['end'] * 1000].export(file_name_wav, format='wav')
        data = {
            'file': base_name_file,
            'extension': original_extension,
            'duration': int(duration),
            'type': type,
            'code': code,
            'hour_broadcast': hour_broadcast,
            'status': status
        }
        print("=======================REGISTER AUDIT==============================")
        print(register_audit(data))
        print("====================================================================")
        # convert(file_name_wav, new_file_name)
        # os.remove(file_name_wav)
    else:
        print("=============================FILE EXIST==============================")
        print(file_exist['message'])
        print("======================================================================")


def management_cut_audios(song, directory_name, base_name_file, silences, original_extension, status, code, type,
                          hour_broadcast):
    global extension_file_wav, cut_path
    path = create_directory(directory_name)
    # move_file(name, original_extension)
    i = 1
    for silence in silences:
        duration = int(silence['end']) - int(silence['start'])
        new_name_file = base_name_file + '-' + str(duration)
        if (i < len(silences)):
            cut_audio(song, silence, new_name_file, path, original_extension, duration, code, hour_broadcast, status, type)
        else:
            if status == 'COMPLETO':
                cut_audio(song, silence, new_name_file, path, original_extension, duration, code, hour_broadcast,
                          status, type)
            # os.remove('audios/pending/' + name + extension_file_wav)
        i += 1


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


def generate_wav_files():
    global pending_path
    files = read_audios(pending_path)
    for file in files:

        if file.find(extension_file_audio) != -1 or file.find(extension_file_video):
            name, extension = file.split('.')
            file_name = pending_path + file
            type
            new_file_name = pending_path + name + extension_file_wav
            convert(file_name, new_file_name)


def execute_post_request(url, data):
    response = requests.post(url=url, json=data)
    return response.json()


def execute_get_request(url):
    response = requests.get(url=url)
    return response.json()


def register_audit(data):
    global api_url
    url = api_url + 'audits/create'
    return execute_post_request(url, data)


def build_file_name(file, type, hour_broadcast):
    parse_hour_broadcast = hour_broadcast.replace(':', '-')
    file_name = file + type + '-' + parse_hour_broadcast
    return file_name


def get_support_by_code_and_type(code, type):
    global api_url
    url = api_url + 'audits/support/code/' + code + '/type/' + type
    return execute_get_request(url)


def get_by_file_name(file_name):
    global api_url
    url = api_url + 'audits/file_name/' + file_name
    return execute_get_request(url)


def run():
    global extension_file_wav, pending_path, limit_min_second, limit_max_second, limit_second, extension_file_video, extension_file_audio
    # generate_wav_files()
    files = read_audios(pending_path)
    for file in files:
        # Si el fichero es .wav entonces ejecuto la sentencia
        if file.find(extension_file_wav) != -1:
            name, extension, song, audio, sr, duration_total_audio, code, status, type = extract_audio_detail(
                pending_path, file)

            get_support = get_support_by_code_and_type(code, type)
            if (get_support['success'] == True):
                support = get_support['content']
            else:
                print('El soporte ' + code + ' no existe')
                continue

            original_extension = extension_file_audio
            if path.exists(pending_path + name + extension_file_video):
                original_extension = extension_file_video

            silences = build_silences(audio, sr, duration_total_audio)
            print("========================================================================")
            print("La extension original del fichero es " + original_extension)
            print('los bloques de silencios a cortar son los siguientes ', silences)
            directory_name = name
            base_name_file = build_file_name(name, type, support['TINI'])
            management_cut_audios(song, directory_name, base_name_file, silences, original_extension, status, code,
                                  type, support['TINI'])


run()
