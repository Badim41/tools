import os
from pydub import AudioSegment

SAVE_DIR = "audio_files"
RESULT_DIR = "results"


def join_files(audio_paths, output_path, file_format: str, delete_paths=False):
    joined_audio = AudioSegment.empty()

    for audio_path in audio_paths:
        # print("JOIN", audio_path)
        audio = AudioSegment.from_file(audio_path)
        joined_audio = joined_audio.append(audio, crossfade=0)
        if delete_paths:
            os.remove(audio_path)

    result_path = os.path.join(RESULT_DIR, output_path)
    joined_audio.export(result_path, format=file_format)
    return result_path


def find_min_volume_timecodes(audio, start_duration=15, end_duration=29):
    audio_duration = len(audio)

    start_duration = start_duration*1000
    end_duration = end_duration*1000
    segment_duration = 500

    if audio_duration < end_duration:
        return audio_duration

    min_loud_piece = (start_duration, audio[start_duration:start_duration + segment_duration].dBFS)
    for current_time in range(end_duration, start_duration, -segment_duration):
        audio_segment = audio[current_time - segment_duration:current_time]
        avg_volume = audio_segment.dBFS
        if min_loud_piece[1] > avg_volume:
            min_loud_piece = (current_time, avg_volume)
        # print("Loud:", avg_volume, current_time)

    # print("RESULT", min_loud_piece)
    return min_loud_piece[0]


def slice_audio_file(audio, output_file1, file_format: str, slice_duration_ms=None):
    if slice_duration_ms is None:
        slice_duration_ms = find_min_volume_timecodes(audio)

    audio_duration = len(audio)

    if slice_duration_ms == audio_duration:
        audio.export(os.path.join(SAVE_DIR, output_file1), format=file_format)
        return None, None
    elif slice_duration_ms <= 0 or slice_duration_ms > audio_duration:
        raise Exception("Недопустимая длительность среза")

    slice_1 = audio[:slice_duration_ms]
    slice_2 = audio[slice_duration_ms:]

    return slice_1, slice_2

def slice_file(audio_file_path, file_format: str, random_factor=""):
    audio = AudioSegment.from_file(audio_file_path)
    i = 0
    while True:
        slice_1, slice_2 = slice_audio_file(audio=audio,
                                          output_file1=random_factor + f"input_{i}.{file_format}",
                                          file_format=file_format)
        if slice_2 is None:
            i += 1
            break
        else:
            slice_1.export(os.path.join(SAVE_DIR, random_factor + f"input_{i}.{file_format}"), format=file_format)
            print("Sliced:", random_factor + f"input_{i}.{file_format}")
            audio = slice_2
            i += 1

    files = [os.path.join(SAVE_DIR, random_factor + f"input_{j}.{file_format}") for j in range(i)]
    for file in files:
        if not os.path.exists(file):
            raise Exception(file + " not exist!")

    return files
