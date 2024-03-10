import os
import shutil
import traceback
from urllib.parse import urlparse

from discord_tools.lalalai import process_file_pipeline, LalalAI, LalalAIModes
from discord_tools.logs import Color, Logs
from discord_tools.timer import Time_Count
from discord_tools.yt_downloader import get_youtube_video_id, yt_download

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
logger = Logs(warnings=True)


def full_process_file(input_text):
    timer = Time_Count()
    modes = ['Drums', 'Bass', 'Electric guitar', 'Acoustic guitar', 'Piano', 'Synthesizer', 'Strings', 'Wind']
    all_results = []

    try:
        logger.logging("Обработка:", input_text, color=Color.GRAY)

        audio_path = None
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

        shutil.copy(audio_path, 'audio_files/input.mp3')

        profile = os.path.join(BASE_DIR, 'Profile_lalalai')
        lalala = LalalAI(profile)
        lalala.go_to_site()

        results = process_file_pipeline("audio_files/input.mp3",
                                        mode=LalalAIModes.Vocal_and_Instrumental,
                                        random_factor="RANDOM_",
                                        lalala=lalala)
        all_results.append(results)

        instrumental = results[2]
        logger.logging("INSTRUMENTAL:", instrumental, color=Color.GREEN)

        for mode in modes:
            shutil.copy(instrumental, 'audio_files/input.mp3')
            results = process_file_pipeline("audio_files/input.mp3",
                                            mode=mode,
                                            random_factor="RANDOM_",
                                            lalala=lalala)
            all_results.append(results)
            logger.logging("RESULTS:", results, color=Color.GREEN)

        lalala.driver.quit()

        if downloaded_video:
            os.remove(audio_path)
    except:
        traceback_str = traceback.format_exc()
        logger.logging("ERROR ID:1", str(traceback_str))

    logger.logging("ПОТРАЧЕНО:", timer.count_time(), color=Color.PURPLE)
    return all_results


if __name__ == "__main__":
    input_str = input("Введите имя файла или ссылку на ютуб:\n")
    all_processed_files = full_process_file(input_str)
    print("All results:", all_processed_files)
