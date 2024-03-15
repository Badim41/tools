import os
import random
import requests
import shutil
import traceback
import uuid
from fake_useragent import UserAgent
from urllib.parse import urlparse

from discord_tools.logs import Logs, Color
from discord_tools.slicer import slice_file, join_files
from discord_tools.timer import Time_Count
from discord_tools.yt_downloader import get_youtube_video_id, yt_download

logger = Logs(warnings=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAVE_DIR = "audio_files"
RESULT_DIR = "results"


class LalalAIModes:
    Vocal_and_Instrumental = ("vocals", "orion")
    Drums = ("drum", "orion")
    Bass = ("bass", "orion")
    Voice_and_Noise = ("voice", "orion")
    Electric_guitar = ("electric_guitar", "orion")
    Acoustic_guitar = ("acoustic_guitar", "orion")
    Piano = ("piano", "orion")
    Synthesizer = ("synthesizer", "phoenix")
    Strings = ("strings", "phoenix")
    Wind = ("wind", "phoenix")

    @staticmethod
    def get_mode(mode_key):
        modes_dict = {
            "vocal_and_instrumental": LalalAIModes.Vocal_and_Instrumental,
            "drums": LalalAIModes.Drums,
            "bass": LalalAIModes.Bass,
            "voice_and_noise": LalalAIModes.Voice_and_Noise,
            "electric_guitar": LalalAIModes.Electric_guitar,
            "acoustic_guitar": LalalAIModes.Acoustic_guitar,
            "piano": LalalAIModes.Piano,
            "synthesizer": LalalAIModes.Synthesizer,
            "strings": LalalAIModes.Strings,
            "wind": LalalAIModes.Wind
        }

        return modes_dict.get(mode_key.lower(), "Mode not found")

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
    def __init__(self, testing=False):
        self.session = requests.Session()
        self.csrftoken_token = uuid.uuid1().hex
        self.user_agent = UserAgent().random
        self.testing = testing
        self.uuid = None
        self.mode = None

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
            logger.logging("PREVIEW")

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
        print("CHECK")
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

    @staticmethod
    def download_file(url, file_name):
        logger.logging(f"save as {file_name}", color=Color.GRAY)
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)


def process_file_pipeline(large_file_name: str, mode, lalala=None, random_factor="", file_format="mp3"):
    if file_format not in ["mp3", "wav"]:
        raise Exception("Формат не поддерживается. Доступные форматы: mp3, wav")

    if not lalala:
        lalala = LalalAI()

    if isinstance(mode, tuple):
        lalala.mode = mode
    elif isinstance(mode, str):
        lalala.mode = LalalAIModes.get_mode("vocal_and_instrumental")

    crashed = False
    first_paths = []
    second_paths = []
    try:

        if lalala.testing:
            logger.logging("Selected model:", lalala.mode[0], color=Color.BLUE)

        files = slice_file(large_file_name, random_factor=random_factor, file_format=file_format)
        for i, file in enumerate(files):
            lalala.upload(file)
            lalala.preview()
            urls = lalala.check()
            # сохраняем каждую дорожку
            for number, url in enumerate(urls):
                if number == 0:
                    file_name = os.path.join(SAVE_DIR, random_factor + f"{lalala.mode[0]}_first_path{i}.mp3")
                    LalalAI.download_file(url, file_name=file_name)
                    first_paths.append(file_name)
                elif number == 1:
                    file_name = os.path.join(SAVE_DIR, random_factor + f"{lalala.mode[0]}_second_path{i}.mp3")
                    LalalAI.download_file(url, file_name=file_name)
                    second_paths.append(file_name)
                else:
                    raise Exception("Найдено более двух файлов")

            try:
                os.remove(file)
            except Exception as e:
                logger.logging("ERROR IN REMOVE FILE:", e)
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


def full_process_file_pipeline(input_text: str, random_factor="", modes=None, file_format=None,
                               delete_file=False):
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

        if not file_format:
            file_format = audio_path[input_text.rfind(".") + 1:]

        if file_format not in ["mp3", "wav"]:
            raise Exception("Формат не поддерживается. Доступные форматы: mp3, wav")

        process_file = f'{SAVE_DIR}/{random_factor}input.{file_format}'
        shutil.copy(audio_path, process_file)

        for mode in modes:
            logger.logging("Start process:", process_file, color=Color.GREEN)
            results = process_file_pipeline(process_file,
                                            mode=mode,
                                            random_factor=random_factor,
                                            file_format=file_format)
            all_results.append(results[1])
            process_file = results[2]

        not_recognized = f"{RESULT_DIR}/{random_factor}_Else.{file_format}"
        os.rename(process_file, not_recognized)

        all_results.append(not_recognized)

        if downloaded_video or delete_file:
            os.remove(audio_path)
    except:
        traceback_str = traceback.format_exc()
        logger.logging("ERROR ID:1", str(traceback_str))

    logger.logging("ПОТРАЧЕНО:", timer.count_time(), color=Color.PURPLE)
    return all_results
