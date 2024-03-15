import concurrent.futures
import os
import requests
import shutil
import subprocess
import time
import traceback
import uuid
from fake_useragent import UserAgent
from pydub import AudioSegment
from urllib.parse import urlparse

from discord_tools.logs import Logs, Color
from discord_tools.slicer import slice_file, join_files
from discord_tools.timer import Time_Count
from discord_tools.yt_downloader import get_youtube_video_id, yt_download

logger = Logs(warnings=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAVE_DIR = "audio_files"
RESULT_DIR = "results"

if not os.path.exists(RESULT_DIR):
    os.mkdir(RESULT_DIR)
if not os.path.exists(SAVE_DIR):
    os.mkdir(SAVE_DIR)


class LalalAIModes:
    Vocal_and_Instrumental = "Vocal and Instrumental"
    Drums = "Drums"
    Bass = "Bass"
    Voice_and_Noise = "Voice and Noise"
    Electric_guitar = "Electric guitar"
    Acoustic_guitar = "Acoustic guitar"
    Piano = "Piano"
    Synthesizer = "Synthesizer"
    Strings = "Strings"
    Wind = "Wind"

    @staticmethod
    def get_mode(mode_key):
        mode_key = mode_key.replace(" ", "_")
        modes_dict = {
            "vocal_and_instrumental": ("vocals", "orion"),
            "drums": ("drum", "orion"),
            "bass": ("bass", "orion"),
            "voice_and_noise": ("voice", "orion"),
            "electric_guitar": ("electric_guitar", "orion"),
            "acoustic_guitar": ("acoustic_guitar", "orion"),
            "piano": ("piano", "orion"),
            "synthesizer": ("synthesizer", "phoenix"),
            "strings": ("strings", "phoenix"),
            "wind": ("wind", "phoenix")
        }

        return modes_dict[mode_key.lower()]

    # def go_to_site(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def agree_cookie(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def upload_file(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def get_network(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def wait_for_response(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def find_item_by_text(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def back_to_menu(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def get_modes(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def change_mode(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)
    #
    # def download_file(self):
    #     logger.logging("THIS METHOD IS OLD AND IGNORED", color=Color.RED)


class LalalAI:
    def __init__(self, mode: tuple, testing=False):

        self.session = requests.Session()
        self.csrftoken_token = uuid.uuid1().hex
        self.user_agent = UserAgent().random
        self.testing = testing
        self.mode = mode
        self.uuid = None
        self.temp_files = []

    def upload(self, file_path):
        if self.testing:
            logger.logging("UPLOAD")

        url = "https://www.lalal.ai/api/upload/"

        if not os.path.exists(file_path):
            raise Exception(f"Не найден файл {file_path}")

        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{os.path.basename(file_path)}",
            "Content-Type": "binary/octet-stream",
            "user-agent": self.user_agent,
            "x-csrftoken": self.csrftoken_token
        }

        with open(file_path, "rb") as file:
            file_content = file.read()

        response = requests.post(url, data=file_content, headers=headers)

        self.uuid = response.json()['id']

        if self.testing:
            logger.logging(response, response.text)
            logger.logging(self.uuid)
            logger.logging("UPLOAD END")

    def preview(self):
        if self.testing:
            logger.logging("PREVIEW", self.mode[0], self.mode[1])

        url = "https://www.lalal.ai/api/preview/"

        payload = f"------WebKitFormBoundaryjMbrck4eZnhvT9mC\r\nContent-Disposition: form-data; name=\"id\"\r\n\r\n{self.uuid}\r\n------WebKitFormBoundaryjMbrck4eZnhvT9mC\r\nContent-Disposition: form-data; name=\"filter\"\r\n\r\n1\r\n------WebKitFormBoundaryjMbrck4eZnhvT9mC\r\nContent-Disposition: form-data; name=\"stem\"\r\n\r\n{self.mode[0]}\r\n------WebKitFormBoundaryjMbrck4eZnhvT9mC\r\nContent-Disposition: form-data; name=\"splitter\"\r\n\r\n{self.mode[1]}\r\n------WebKitFormBoundaryjMbrck4eZnhvT9mC\r\nContent-Disposition: form-data; name=\"dereverb_enabled\"\r\n\r\nfalse\r\n------WebKitFormBoundaryjMbrck4eZnhvT9mC--\r\n"

        headers = {
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryjMbrck4eZnhvT9mC",
            "user-agent": self.user_agent,
            "x-csrftoken": self.csrftoken_token
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        if self.testing:
            logger.logging(response, response.text)
            logger.logging("PREVIEW END")

    def check(self):
        if self.testing:
            logger.logging("CHECK")

        url = "https://www.lalal.ai/api/check/"

        headers = {
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundary1dIVPH7jlxDN9TeD",
            "user-agent": self.user_agent,
            "x-csrftoken": self.csrftoken_token
        }

        data = f'------WebKitFormBoundary1dIVPH7jlxDN9TeD\r\nContent-Disposition: form-data; name="id"\r\n\r\n{self.uuid}\r\n------WebKitFormBoundary1dIVPH7jlxDN9TeD--\r\n'
        response = self.session.post(url, headers=headers, data=data)

        self.ready_id = response.json()['result'][self.uuid]['task']['id'][2]
        resul_url_1 = f"https://d.lalal.ai/media/preview/{self.uuid}/{self.ready_id}/{self.mode[0]}"
        resul_url_2 = f"https://d.lalal.ai/media/preview/{self.uuid}/{self.ready_id}/no_{self.mode[0]}"

        if self.testing:
            logger.logging(response, response.text)
            logger.logging("RESULT", resul_url_1, "\n", resul_url_2, color=Color.GREEN)
            logger.logging("CHECK END")

        return resul_url_1, resul_url_2

    def download_file(self, url, file_name):
        # Скачиваем, пока не скачается
        while True:
            try:
                logger.logging(f"save as {file_name}", color=Color.GRAY)
                response = requests.get(url)
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                AudioSegment.from_file(file_name)
                return file_name
            except:
                logger.logging("Cant decode file, download again")
                time.sleep(0.5)
                self.temp_files.append(file_name)
                return self.download_file(url, f"{file_name[:-4]}-{file_name[-4:]}")

    def delete_temp_files(self):
        for file_path in self.temp_files:
            try:
                os.remove(file_path)
                self.temp_files.remove(file_path)
            except Exception as e:
                logger.logging(f"Error in delete file {file_path} {e}")


def process_one_piece(file, mode, testing, random_factor, i):
    lalala = LalalAI(testing=testing, mode=LalalAIModes.get_mode(mode))
    lalala.upload(file)
    lalala.preview()
    urls = lalala.check()

    first_path, second_path = None, None
    for number, url in enumerate(urls):
        if number == 0:
            file_name = os.path.join(SAVE_DIR, random_factor + f"{mode}_first_path{i}.mp3")
            file_name = lalala.download_file(url, file_name=file_name)
            first_path = file_name
        elif number == 1:
            file_name = os.path.join(SAVE_DIR, random_factor + f"{mode}_second_path{i}.mp3")
            file_name = lalala.download_file(url, file_name=file_name)
            second_path = file_name
        else:
            raise Exception("Найдено более двух файлов")

    try:
        os.remove(file)
    except Exception as e:
        logger.logging("ERROR IN REMOVE FILE:", e)

    lalala.delete_temp_files()

    return i, first_path, second_path


def process_file_pipeline(large_file_name: str, mode, testing=False, random_factor="", file_format="mp3"):
    if file_format not in ["mp3", "wav"]:
        raise Exception("Формат не поддерживается. Доступные форматы: mp3, wav")

    crashed = False
    first_paths = []
    second_paths = []
    try:

        files = slice_file(large_file_name, random_factor=random_factor, file_format=file_format)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_file = {executor.submit(process_one_piece, file, mode, testing, random_factor, i): i for i, file
                              in enumerate(files)}

            first_paths = [None] * len(files)
            second_paths = [None] * len(files)

            for future in concurrent.futures.as_completed(future_to_file):
                try:
                    index, first_path, second_path = future.result()
                    first_paths[index] = first_path
                    second_paths[index] = second_path
                except Exception as e:
                    logger.logging("Error processing file:", e)

    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.logging("ERROR ID:2", str(traceback_str))
        crashed = True

    # Правильные имена файлов. Например:
    # Voice.wav, Instrumental.wav
    # Without_Bass.wav, Bass.wav

    if mode.count(" ") >= 2:
        mode_words = mode.split(" ")
        first_result = random_factor + f"{mode_words[0]}.{file_format}"
        second_result = random_factor + f"{mode_words[-1]}.{file_format}"
    else:
        first_result = random_factor + f"{mode}.{file_format}"
        second_result = random_factor + f"Without_{mode}.{file_format}"
    # объединяем файлы
    first_result = join_files(first_paths, first_result, file_format=file_format, delete_paths=True)
    second_result = join_files(second_paths, second_result, file_format=file_format, delete_paths=True)
    return crashed, first_result, second_result


def full_process_file_pipeline(input_text: str, random_factor="", modes=None,
                               delete_file=False, wav_always=None, testing=False):
    timer = Time_Count()

    if not modes:
        modes = [LalalAIModes.Vocal_and_Instrumental,
                 LalalAIModes.Drums,
                 LalalAIModes.Bass,
                 LalalAIModes.Electric_guitar,
                 LalalAIModes.Acoustic_guitar,
                 LalalAIModes.Piano,
                 LalalAIModes.Synthesizer,
                 LalalAIModes.Strings,
                 LalalAIModes.Wind]

    elif not isinstance(modes, list):
        raise Exception("Modes должно быть list")

    all_results = []

    try:
        logger.logging("Обработка:", input_text, color=Color.GRAY)

        audio_path = None
        downloaded_video = None
        if os.path.exists(input_text):
            audio_path = input_text
            downloaded_video = False
            logger.logging("Найден файл", color=Color.GRAY)
        elif 'https' in input_text:
            if urlparse(input_text).scheme == 'https':
                song_id = get_youtube_video_id(input_text)

                if song_id is None:
                    raise Exception("Нет song id")

                song_link = input_text.split('&')[0]
                audio_path = yt_download(song_link, max_duration=3600)
                downloaded_video = True

        if not audio_path:
            raise Exception("Укажите ссылку на ютуб или аудиофайл")

        file_format = audio_path[-3:]
        if file_format == "mp3":
            if wav_always:
                wav_path = audio_path[:-4] + ".wav"
                subprocess.run(
                    ["ffmpeg", "-i", audio_path, "-codec:a", "pcm_s16le", "-ar", "44100", "-ac", "2", wav_path,
                     "-y"],
                    check=True)
                audio_path = wav_path
                file_format = "wav"
        elif file_format == "wav":
            pass
        else:
            raise Exception(f"Формат {file_format} не поддерживается. Доступные форматы: mp3, wav")

        process_file = f'{SAVE_DIR}/{random_factor}input.{file_format}'
        shutil.copy(audio_path, process_file)

        for mode in modes:
            logger.logging("Start process:", process_file, color=Color.GREEN)
            results = process_file_pipeline(process_file,
                                            mode=mode,
                                            random_factor=random_factor,
                                            file_format=file_format, testing=testing)
            all_results.append(results[1])
            process_file = results[2]

        not_recognized = f"{RESULT_DIR}/{random_factor}_Else.{file_format}"
        os.rename(process_file, not_recognized)

        all_results.append(not_recognized)

        if downloaded_video or delete_file:
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.logging("Error in delete file:", e)
    except:
        traceback_str = traceback.format_exc()
        logger.logging("ERROR ID:1", str(traceback_str))

    logger.logging("ПОТРАЧЕНО:", timer.count_time(), color=Color.PURPLE)
    return all_results
