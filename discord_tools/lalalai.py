import json
import os
import random
import requests
import shutil
import threading
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse

from discord_tools.logs import Color, Logs
from discord_tools.slicer import slice_file, join_files
from discord_tools.timer import Time_Count
from discord_tools.yt_downloader import get_youtube_video_id, yt_download

logger = Logs(warnings=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAVE_DIR = "audio_files"
RESULT_DIR = "results"

JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
      var rect = target.getBoundingClientRect(),
          x = rect.left + (offsetX || (rect.width >> 1)),
          y = rect.top + (offsetY || (rect.height >> 1)),
          dataTransfer = { files: this.files };

      ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
      });

      setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
"""


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


def screen_recorder(driver):
    try:
        i = 0
        while True:
            i += 1
            time.sleep(3)
            print("save screenshot", i)
            driver.save_screenshot(os.path.join(RESULT_DIR, f"LALALAI_TEMP_RECORD{i}.png"))
    except Exception as e:
        print("An error occurred in screen_recorder:", e)


class LalalAI:
    def __init__(self, profile=None, testing=False, low_memory=False, record_screen=False):

        if not os.path.exists(RESULT_DIR):
            os.mkdir(RESULT_DIR)

        if not os.path.exists(SAVE_DIR):
            os.mkdir(SAVE_DIR)

        self.done = False
        chrome_options = webdriver.ChromeOptions()

        if profile:
            chrome_options.add_argument(f'user-data-dir={profile}')

        chrome_options.add_experimental_option('detach', True)
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.javascript": 2
        })
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--headless')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except:
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                           options=chrome_options)

        self.driver.implicitly_wait(10)
        self.responses_was = set()
        self.testing = testing
        self.low_memory = low_memory
        if record_screen:
            thread = threading.Thread(target=screen_recorder, args=(self.driver,))
            thread.start()

        # while not self.driver:
        #     time.sleep(0.5)

    # def initialization(self, profile):
    #     # with SB(uc=True, headed=True, headless=False, devtools=False, user_data_dir=profile,
    #     #         chromium_arg="--enable-logging") as driver:
    #
    #     logger.logging("Loaded browser")
    #     while not self.done:
    #         time.sleep(5)

    def go_to_site(self):
        self.driver.get("https://www.lalal.ai/")
        self.cancel_upload()
        self.agree_cookie()
        self.back_to_menu()
        self.driver.save_screenshot(os.path.join(RESULT_DIR, "lalalAI.png"))
        logger.logging("Loaded broswer")
        # continue_button = self.driver.find_elements(By.CSS_SELECTOR, "button.LgbsSe.LgbsSe-ssJRIf.LgbsSe-KoToPc.mdl-button.mdl-js-button")
        # if continue_button:
        #     self.driver.execute_script("arguments[0].click();", continue_button[0])
        # else:
        #     logger.logging("No continue button")

    def agree_cookie(self):
        if self.testing:
            logger.logging("agree cookie try")

        cookie_element = self.driver.find_elements(By.CSS_SELECTOR, 'button.cookies__submit-button')
        if cookie_element:
            self.driver.execute_script("arguments[0].click();", cookie_element[0])
        else:
            logger.logging("No cookie button found")

    def upload_file(self, file_path):
        if self.testing:
            logger.logging(f"Uploading {file_path}...", color=Color.GRAY)

        for i in range(10):
            try:
                upload_element = self.find_item_by_text(type='label', text='Select Files', attribute='aria-label')
                file_input = self.driver.execute_script(JS_DROP_FILE, upload_element, 0, 0)
            except Exception as e:
                logger.logging("ERROR in upload", i, str(e)[:50])
                self.driver.save_screenshot(os.path.join(RESULT_DIR, f"lalalAI_error{i}.png"))
                self.cancel_upload()
                self.back_to_menu()
                time.sleep(0.5)
        file_input.send_keys(os.path.abspath(file_path))
        # logger.logging("loaded file!")

    def get_network(self):
        return self.driver.get_log("performance")

    def wait_for_response(self):
        if self.testing:
            logger.logging("wait try")

        responses = set()
        while len(responses) < 2:
            time.sleep(3 if self.low_memory else 0.5)
            # input("press enter to continue")
            network_requests = self.get_network()
            for entry in network_requests:
                try:
                    message_obj = json.loads(entry.get("message"))
                    message = message_obj.get("message")

                    response_url = message.get('params', {}).get('response', {}).get('url', '')
                    if 'https://d.lalal.ai/media/preview/' in response_url:
                        if response_url in self.responses_was and response_url:
                            continue
                        else:
                            self.responses_was.add(response_url)

                        if self.testing:
                            logger.logging("Response URL:", response_url, color=Color.GRAY)

                        responses.add(response_url)
                except Exception as e:
                    logger.logging(e)
        # Отсортировать по длине
        return sorted(responses, key=lambda x: (len(x), x))

    def find_item_by_text(self, type: str, text: str, attribute=None):
        elements = self.driver.find_elements(By.XPATH, f"//{type}")
        if attribute:
            for element in elements:
                if element.get_attribute(attribute) == text:
                    return element
        else:
            for element in elements:
                if element.text == text:
                    return element

    def cancel_upload(self):
        if self.testing:
            logger.logging("cancel upload try")

        try:
            cancel_button = self.find_item_by_text(type='span', text='Cancel')
            if cancel_button:
                self.driver.execute_script("arguments[0].click();", cancel_button)
            elif self.testing:
                logger.logging("No cancel button", color=Color.GRAY)
        except Exception as e:
            logger.logging("Error in cansel:", str(e)[:50])

    def back_to_menu(self):
        if self.testing:
            logger.logging("back menu try")

        back_button = self.find_item_by_text(type='button', text='← Back')
        if back_button:
            self.driver.execute_script("arguments[0].click();", back_button)
            self.cancel_upload()  # баг сайта
        elif self.testing:
            logger.logging("no button back", color=Color.GRAY)

    def get_modes(self):
        if self.testing:
            logger.logging("get modes try")

        modes = [{mode.text: mode} for mode in self.driver.find_elements(By.CSS_SELECTOR, 'li.M9vFq1co')]
        return modes

    def change_mode(self, selecting_mode):
        if self.testing:
            logger.logging("change mode try")

        button_mode = self.find_item_by_text(type='button', text='Stem separation type', attribute='aria-label')
        self.driver.execute_script("arguments[0].click();", button_mode)
        modes = self.get_modes()
        for mode in modes:
            for mode_text, mode_element in mode.items():
                # logger.logging(mode_text)
                if selecting_mode == mode_text:
                    self.driver.execute_script("arguments[0].click();", mode_element)
                    return

        raise Exception(
            f'Not found mode. Mode list: {[mode for mode in dir(LalalAIModes) if not mode.startswith("__")]}')

    def download_file(self, url, file_name=f'file_{random.randint(1, 999999)}'):
        logger.logging(f"save as {file_name}", color=Color.GRAY)
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)


def process_file_pipeline(large_file_name: str, mode, lalala=None, random_factor="", file_format="mp3"):
    if file_format not in ["mp3", "wav"]:
        raise Exception("Формат не поддерживается. Доступные форматы: mp3, wav")

    if not lalala:
        lalala = LalalAI()
        lalala.go_to_site()

    crashed = False
    try:
        mode = mode.replace("_", " ")

        if lalala.testing:
            logger.logging("Selected model:", mode, color=Color.BLUE)

        lalala.change_mode(mode)
        # нарезаем файлы
        files = slice_file(large_file_name, random_factor=random_factor, file_format=file_format)
        first_paths = []
        second_paths = []
        for i, file in enumerate(files):
            lalala.upload_file(file)
            urls = lalala.wait_for_response()
            # сохраняем каждую дорожку
            for number, url in enumerate(urls):
                if number == 0:
                    file_name = os.path.join(SAVE_DIR, random_factor + f"{mode}_first_path{i}.mp3")
                    lalala.download_file(url, file_name=file_name)
                    first_paths.append(file_name)
                elif number == 1:
                    file_name = os.path.join(SAVE_DIR, random_factor + f"{mode}_second_path{i}.mp3")
                    lalala.download_file(url, file_name=file_name)
                    second_paths.append(file_name)
                else:
                    raise Exception("Найдено более двух файлов")
            # обратно в меню
            lalala.back_to_menu()
            if lalala.low_memory:
                logger.logging("try refresh")
                lalala.driver.refresh()
                logger.logging("refreshed")
            # удаляем временный файл
            os.remove(file)
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
    lalala.responses_was = set()
    return crashed, first_result, second_result


def full_process_file_pipeline(input_text: str, lalala=None, random_factor="", modes=None, file_format=None, delete_file=False):
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

        if not lalala:
            lalala = LalalAI()
            lalala.go_to_site()

        process_file = f"{random_factor}input.{file_format}"
        shutil.copy(audio_path, f'{SAVE_DIR}/{process_file}')

        for mode in modes:
            logger.logging("Start process:", process_file, color=Color.GREEN)
            results = process_file_pipeline(f"{SAVE_DIR}/{process_file}",
                                            mode=mode,
                                            random_factor=random_factor,
                                            lalala=lalala,
                                            file_format=file_format)
            all_results.append(results[1])
            process_file = results[2]

        not_recognized = f"{RESULT_DIR}/{random_factor}_Else.{file_format}"
        os.rename(process_file, not_recognized)

        all_results.append(not_recognized)
        lalala.driver.quit()

        if downloaded_video or delete_file:
            os.remove(audio_path)
    except:
        traceback_str = traceback.format_exc()
        logger.logging("ERROR ID:1", str(traceback_str))

    logger.logging("ПОТРАЧЕНО:", timer.count_time(), color=Color.PURPLE)
    return all_results
