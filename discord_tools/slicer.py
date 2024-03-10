import os
from pydub import AudioSegment

SAVE_DIR = "audio_files"
RESULT_DIR = "results"


def join_files(audio_paths, output_path, file_format: str, delete_paths=False):
    joined_audio = AudioSegment.empty()

    for audio_path in audio_paths:
        print("JOIN", audio_path)
        audio = AudioSegment.from_file(audio_path)
        joined_audio = joined_audio.append(audio, crossfade=0)
        if delete_paths:
            os.remove(audio_path)

    result_path = os.path.join(RESULT_DIR, output_path)
    joined_audio.export(result_path, format=file_format)
    return result_path


def slice_audio_file(input_file_path, slice_duration_ms, output_file1, output_file2, file_format: str):
    audio = AudioSegment.from_file(input_file_path)
    audio_duration = len(audio)
    # print(slice_duration_ms, audio_duration)

    if slice_duration_ms == audio_duration:
        audio.export(os.path.join(SAVE_DIR, output_file1), format=file_format)
        os.remove(output_file2)
        return True
    elif slice_duration_ms <= 0 or slice_duration_ms > audio_duration:
        raise Exception("Недопустимая длительность среза")

    slice_1 = audio[:slice_duration_ms]
    slice_2 = audio[slice_duration_ms:]
    slice_1.export(os.path.join(SAVE_DIR, output_file1), format=file_format)
    slice_2.export(os.path.join(output_file2), format=file_format)


def find_min_volume_timecodes(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)
    audio_duration = len(audio)
    print("Audio len:", audio_duration)

    start_duration = 15000
    end_duration = 29000
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


def slice_file(audio_file_path, file_format: str, random_factor=""):
    i = 0
    while True:
        # Получаем таймкод минимальной громкости
        timecode = find_min_volume_timecodes(audio_file_path)

        end_generation = slice_audio_file(input_file_path=audio_file_path, slice_duration_ms=timecode,
                                          output_file1=random_factor + f"input_{i}.{file_format}",
                                          output_file2=audio_file_path, file_format=file_format)
        i += 1
        if end_generation:
            # print("Done!")
            break

        # print(f"Min volume at {timecode} milliseconds")

    files = [os.path.join(SAVE_DIR, random_factor + f"input_{j}.{file_format}") for j in range(i)]
    for file in files:
        if not os.path.exists(file):
            raise Exception(file + " not exist!")

    return files
