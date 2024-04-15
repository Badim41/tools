import os
import random
import requests
import string
import subprocess
import time
import webbrowser
from aiogram.utils.json import json

from discord_tools.sql_db import get_database, set_database_not_async as set_database


class Lmsys_Text_Models:
    claude_3_haiku_20240307 = "claude-3-haiku-20240307"
    claude_3_sonnet_20240229 = "claude-3-sonnet-20240229"
    claude_3_opus_20240229 = "claude-3-opus-20240229"
    claude_2_1 = "claude-2.1"
    command_r_plus = "command-r-plus"
    command_r = "command-r"
    gemma_1_1_7b_it = "gemma-1.1-7b-it"
    gemma_7b_it = "gemma-7b-it"
    mixtral_8x7b_instruct_v0_1 = "mixtral-8x7b-instruct-v0.1"
    mistral_large_2402 = "mistral-large-2402"
    mistral_medium = "mistral-medium"
    mistral_7b_instruct_v0_2 = "mistral-7b-instruct-v0.2"
    qwen1_5_72b_chat = "qwen1.5-72b-chat"
    qwen1_5_32b_chat = "qwen1.5-32b-chat"
    qwen1_5_14b_chat = "qwen1.5-14b-chat"
    qwen1_5_7b_chat = "qwen1.5-7b-chat"
    qwen1_5_4b_chat = "qwen1.5-4b-chat"
    dbrx_instruct = "dbrx-instruct"
    starling_lm_7b_beta = "starling-lm-7b-beta"
    gemini_pro_dev_api = "gemini-pro-dev-api"
    gpt_4_turbo_2024_04_09 = "gpt-4-turbo-2024-04-09"
    gpt_4_1106_preview = "gpt-4-1106-preview"
    gpt_3_5_turbo_0125 = "gpt-3.5-turbo-0125"
    gpt_3_5_turbo_0613 = "gpt-3.5-turbo-0613"
    llama_2_70b_chat = "llama-2-70b-chat"
    llama_2_13b_chat = "llama-2-13b-chat"
    llama_2_7b_chat = "llama-2-7b-chat"
    olmo_7b_instruct = "olmo-7b-instruct"
    vicuna_33b = "vicuna-33b"
    vicuna_13b = "vicuna-13b"
    yi_34b_chat = "yi-34b-chat"
    codellama_70b_instruct = "codellama-70b-instruct"
    openchat_3_5_0106 = "openchat-3.5-0106"
    deepseek_llm_67b_chat = "deepseek-llm-67b-chat"
    openhermes_2_5_mistral_7b = "openhermes-2.5-mistral-7b"
    zephyr_7b_beta = "zephyr-7b-beta"


class Lmsys_API:
    def __init__(self, history_id=101, text_model=None, cookie=None):
        if cookie is None:
            self.get_cloudflare_token()
        else:
            self.cookie = cookie
            set_database("default", "cloudflare_token", self.cookie)

        random.seed(history_id)
        self.session_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        self.text_model = text_model
        self.selected_chat_num = None

    def r_join(self, payload):
        url = "https://chat.lmsys.org/queue/join"

        headers = {
            "cookie": self.cookie,
            "authority": "chat.lmsys.org",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://chat.lmsys.org",
            "referer": "https://chat.lmsys.org/",
            "sec-ch-ua-platform-version": "10.0.0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if "Just a moment..." in response.text:
            print("Токен для cloudflare устарел")
            set_database("default", "cloudflare_token", "None")
            self.get_cloudflare_token()

    def get_request_answer(self, return_answer=False):
        url = "https://chat.lmsys.org/queue/data"

        querystring = {"session_hash": self.session_hash}

        payload = ""
        headers = {
            "cookie": self.cookie,
            "accept": "text/event-stream",
            "user-agent": self.user_agent
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        if "RATE LIMIT OF THIS MODEL IS REACHED" in response.text:
            raise Exception("Лимит запросов. Используйте 'text_model=None', чтобы обойти ограничение!")

        response_parts = response.text.split("data: ")
        last_response = response_parts[-1]
        answer = json.loads(last_response)

        if answer['success']:
            if return_answer:
                # print(answer['output']['data'])
                return answer['output']['data']
        else:
            print("Not success")

    def clear_chat(self):
        payload = {
            "data": [],
            "event_data": None,
            "fn_index": 7 if self.text_model is None else 37,
            "trigger_id": 35 if self.text_model is None else 100,
            "session_hash": self.session_hash
        }

        self.r_join(payload)
        print("Chat cleared")

    def get_answer(self, prompt):
        if self.text_model is None:
            payload = {
                "data": [None, None, "", "", prompt],
                "event_data": None,
                "fn_index": 12,
                "trigger_id": 32,
                "session_hash": self.session_hash
            }

            self.r_join(payload)
            self.get_request_answer()

            payload = {
                "data": [None, None, 0.7, 1, 1024],
                "event_data": None,
                "fn_index": 13,
                "trigger_id": 32,
                "session_hash": self.session_hash
            }

            self.r_join(payload)
            answer = self.get_request_answer(return_answer=True)

            payload = {
                "data": [],
                "event_data": None,
                "fn_index": 14,
                "trigger_id": 32,
                "session_hash": self.session_hash
            }

            self.r_join(payload)
            self.get_request_answer()

            if self.selected_chat_num is None:
                return [answer[2][-1][1], answer[3][-1][1]]
            else:
                return [answer[2+self.selected_chat_num][-1][1]]
        else:
            payload = {
                "data": [None, self.text_model, prompt, None],
                "event_data": None,
                "fn_index": 39,
                "trigger_id": 92,
                "session_hash": self.session_hash
            }

            self.r_join(payload)
            self.get_request_answer()

            payload = {
                "data": [None, 0.7, 1, 1024],
                "event_data": None,
                "fn_index": 40,
                "trigger_id": 92,
                "session_hash": self.session_hash
            }

            self.r_join(payload)
            answer = self.get_request_answer(return_answer=True)

            return answer[1][-1][1]

    def find_model(self, req_models: [list, str], attempts=10):
        if isinstance(req_models, str):
            req_models = [req_models]

        for i in range(attempts):
            models = self.get_models()
            print("Found models:", models)
            for req_model in req_models:
                for i, found_model in enumerate(models):
                    if req_model.lower() in found_model.lower():
                        return i, found_model

            if not i == attempts - 1:
                self.clear_chat()
                answer = self.get_answer("2+2= (выведи только число!)")
                print(answer)

        print(f"За {attempts} попыток модель не найдена")
        return None, None
    def choose_chat(self, num):
        self.selected_chat_num = num
    def get_models(self):
        payload = {
            "data": [None, None, "", ""],
            "event_data": None,
            "fn_index": 2,
            "trigger_id": 28,
            "session_hash": self.session_hash
        }

        self.r_join(payload)
        answer = self.get_request_answer(return_answer=True)

        if answer:
            return [answer[0][13:], answer[1][13:]]
        else:
            return []
    def get_cloudflare_token(self):
        db_cookie = get_database("default", "cloudflare_token")
        if not str(db_cookie) == "None":
            self.cookie = db_cookie
            return
        print("Введите cookie со страницы. Не используйте VPN:")
        url = 'https://chat.lmsys.org'
        webbrowser.open(url)

        library_path = os.path.dirname(__file__)
        file_path = f"{library_path}\\examples\\cookie.png"
        subprocess.run(f'start {file_path}', shell=True)
        self.cookie = input()
        set_database("default", "cloudflare_token", self.cookie)
        print("Cookie получены!")
        # print("Нажмите галочку в открывшемся окне")
        # from selenium import webdriver
        # from selenium.webdriver.chrome.service import Service as ChromeService
        # from webdriver_manager.chrome import ChromeDriverManager
        #
        # import seleniumwire.undetected_chromedriver as uc
        #
        # from selenium import webdriver
        # from selenium_stealth import stealth
        # import random
        #
        # options = webdriver.ChromeOptions()
        #
        # # Add user-agent rotation
        # user_agents = [
        #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        #     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        #     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        #     'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        #     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        #     'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        # ]
        # user_agent = random.choice(user_agents)
        # options.add_argument(f"user-agent={user_agent}")
        #
        # # Initialize the WebDriver with options
        # driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
        #
        # # Apply stealth settings to the driver
        # stealth(driver,
        #         languages=["en-US", "en"],
        #         vendor="Google Inc.",
        #         platform="Win32",
        #         webgl_vendor="Intel Inc.",
        #         renderer="Intel Iris OpenGL Engine",
        #         fix_hairline=True,
        #         )
        #
        # driver.get('https://chat.lmsys.org')
        # time.sleep(1000)

        # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        # driver.get('https://chat.lmsys.org')
        #
        # handle = driver.current_window_handle
        # driver.service.stop()
        # time.sleep(6)
        # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        # driver.switch_to.window(handle)
        #
        # time.sleep(1000)