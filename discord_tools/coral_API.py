import requests
import time

from discord_tools.logs import Logs, Color
from discord_tools.sql_db import get_database, set_database_not_async as set_database

logger = Logs(warnings=True)


class Coral_API:
    def __init__(self, api_key=None, email=None, password=None, proxies=None):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        # self.api_key = self.get_api_key()
        self.proxies = proxies
        self.email = email
        self.password = password
        # self.access_token, self.user_id = self.get_access_token_on_start()
        if not api_key and (email and password):
            self.access_token, self.user_id = self.get_access_token_on_start()
            self.api_keys = [self.get_api_key()]
        elif api_key:
            if isinstance(api_key, list):
                self.api_keys = api_key
            elif isinstance(api_key, str):
                self.api_keys = [api_key]
            else:
                raise Exception("API KEY должен быть str или list")
        else:
            raise Exception("Нет способа получения ключа")

    def login(self):
        import requests

        url = "https://production.api.os.cohere.ai/rpc/BlobheartAPI/AuthV2"

        payload = {
            "email": self.email,
            "password": self.password
        }

        headers = {
            "authority": "production.api.os.cohere.ai",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "authorization": "",
            "content-type": "application/json",
            "request-source": "playground",
            "user-agent": self.user_agent
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

        response_json = response.json()

        access_token = response_json['bearerTokens']['accessToken']
        user_id = response_json['bearerTokens']['userID']

        set_database("default", "coral_access_token", access_token)
        set_database("default", "coral_user_id", user_id)

        logger.logging("Logged in coral!", color=Color.PURPLE)

        return access_token, user_id

    def get_access_token_on_start(self):
        access_token = get_database("default", "coral_access_token")
        user_id = get_database("default", "coral_user_id")
        if access_token == "None" or user_id == "None":
            return self.login()
        else:
            return access_token, user_id

    def get_api_key(self):
        url = "https://production.api.os.cohere.ai/rpc/BlobheartAPI/GetOrCreateDefaultAPIKey"

        payload = {}
        headers = {
            "authority": "production.api.os.cohere.ai",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
            "origin": "https://coral.cohere.com",
            "referer": "https://coral.cohere.com/",
            "request-source": "coral",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.user_agent
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

        if response.status_code == 401:
            logger.logging("Ошибка с авторизацией!", color=Color.RED)
            self.access_token, self.user_id = self.login()
            return self.get_api_key()

        return response.json()['rawKey']

    def generate(self, messages, gpt_role="Ты полезный ассистент и даёшь только полезную информацию", delay_for_gpt=1,
                 temperature=0.3,
                 model="command-r-plus", web_access=False, error=True):
        changed_messages = messages
        if not self.api_keys:
            logger.logging("coral_API: No keys")
            time.sleep(delay_for_gpt)
            return

        response_text = "[not got response]"
        response_json = "[no json]"
        try:

            transformed_messages = []
            prompt = None

            if web_access:
                connectors = [{"id": "web-search"}]
            else:
                connectors = []

            for i, msg in enumerate(changed_messages):
                if 'system' in msg['role']:
                    continue
                role = "User" if msg['role'] == "user" else "Chatbot"
                message = msg['content']
                if i == len(changed_messages) - 1:
                    prompt = message
                else:
                    transformed_messages.append({"role": role, "message": message})

            if not prompt:
                raise Exception("Неправильный формат сообщений!")

            url = "https://api.cohere.ai/v1/chat"

            payload = {
                "message": prompt,
                "temperature": temperature,
                "chat_history": transformed_messages,
                "model": model,
                "preamble": gpt_role,
                "connectors": connectors,
                "stream": False,
                "prompt_truncation": "AUTO"
            }

            headers = {
                "authority": "api.cohere.ai",
                "accept": "*/*",
                "accept-language": "ru,en;q=0.9",
                "authorization": f"Bearer {self.api_keys[0]}",
                "content-type": "application/json; charset=utf-8",
                "user-agent": self.user_agent
            }

            response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)
            if response.status_code == 429:
                if not error and self.api_keys:
                    self.api_keys = self.api_keys[1:]
                    return self.generate(messages=messages, gpt_role=gpt_role, delay_for_gpt=delay_for_gpt,
                                         temperature=temperature, model=model, web_access=web_access, error=True)
                else:
                    raise Exception("Не подошло 2 ключа. Прерван.")

            response_text = response.text
            response_json = response.json()
            return response_json['text']
        except Exception as e:
            logger.logging("Error in coral_API:", e, response_json, response_text, color=Color.RED)
            time.sleep(delay_for_gpt)
