import logging
import os
import requests
import threading

from discord_tools.sql_db import get_database, set_database, set_database_not_async

from discord_tools.str_tools import get_cookie_dict_from_response


class MediaType:
    pdf = "pdf"
    image = "image"
    video = "video"


class ConfigKeysReka:
    reka = "reka"
    app_session = "app_session"


class Reka_API:
    def __init__(self, app_session=None, proxies=None):
        """
        :app_session: AppSession в Request cookie в запросе "auth/firebase_token"
        """
        self.proxies = proxies

        got_keys = self.get_key()

        if got_keys:
            print("Use existing app_session")
        else:
            self.app_session = app_session
            self.auth_key = self.get_access_key()

    def get_key(self):
        try:
            self.app_session = get_database(ConfigKeysReka.reka, ConfigKeysReka.reka)
            self.auth_key = self.get_access_key()
            if self.auth_key:
                return True
        except Exception as e:
            print("Error in get_key reka:", e)

    def save_key(self, response):
        cookie_dict = get_cookie_dict_from_response(response)
        if 'appSession' in cookie_dict:
            self.app_session = cookie_dict['appSession']
            if self.app_session:
                set_database_not_async(ConfigKeysReka.reka, ConfigKeysReka.reka, self.app_session)
            print("New app_session:", self.app_session)
        else:
            print("No app_session in cookies")

    def update_app_session_thread(self):
        self.auth_key = self.get_access_key()

    # def get_me(self):
    #     url = "https://chat.reka.ai/bff/auth/me"
    #
    #     payload = ""
    #     headers = {
    #         "cookie": f"appSession={self.app_session}",
    #     }
    #
    #     response = requests.request("GET", url, data=payload, headers=headers)
    #
    #     cookie_dict = get_cookie_dict_from_response(response)
    #
    #     print(cookie_dict)
    #     print("appSession", cookie_dict['appSession'])

    def get_access_key(self):
        try:
            import requests

            url = "https://chat.reka.ai/chat/orEE2JVvbdOq9NkkIzL2"

            payload = ""
            headers = {
                "authority": "chat.reka.ai",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "cookie": f"appSession={self.app_session}",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36"
            }

            response = requests.request("GET", url, data=payload, headers=headers)

            print("chat", response.text)

            url = "https://chat.reka.ai/bff/auth/firebase_token"

            payload = ""
            headers = {
                "cookie": f"appSession={self.app_session}",
            }

            response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)

            self.save_key(response)

            url = "https://chat.reka.ai/bff/auth/access_token"

            payload = ""
            headers = {
                "cookie": f"appSession={self.app_session}",
            }

            response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)
            return response.json()['accessToken']
        except Exception as e:
            print("Error in get access key:", e)

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            raise Exception("Файл не существует")

        with open(file_path, 'rb') as file:
            files = {'image': file}

            url = "https://chat.reka.ai/api/upload-image"

            payload = ""
            headers = {
                "authorization": f"Bearer {self.auth_key}",
            }
            response = requests.request("POST", url, data=payload, headers=headers, files=files, proxies=self.proxies)

            return response.json()['image_url']

    def generate(self, messages, file_path=None, media_type=None):
        """
        Не поддерживается история с файлом
        """
        if not self.auth_key:
            return None

        try:
            if file_path:
                if not media_type:
                    raise Exception("Не указан media_type: video, image, pdf")
                file_url = self.upload_file(file_path)
            url = "https://chat.reka.ai/api/chat"

            # {"conversation_history": [{"type": "human", "text": "Подробно опиши изображение",
            #                            "image_url": "https://reka-prod-user-images.s3.amazonaws.com/auth0|662aab5b33f9a1464e96b4e2/vlm/Xt6xtjj6OZdFIv34FCBke9g8ZZT9J9myuB4UZcjLE0HBEVSoWamlp46jcgfabXAtlQLTazgZ04100V-VsJM6pg==",
            #                            "media_type": "image"}], "stream": true, "use_search_engine": true,
            #  "use_code_interpreter": true, "model_name": "reka-core", "random_seed": 1714789076709}
            transformed_messages = []

            for i, msg in enumerate(messages):
                message = msg['content']

                if 'system' in msg['role']:
                    transformed_messages.append({"type": "human", "text": message})
                    transformed_messages.append({"type": "model", "text": "."})
                    continue

                role = "human" if msg['role'] == "user" else "model"
                if i == len(messages) - 1 and file_path:
                    transformed_messages = [{
                        "type": "human",
                        "text": message,
                        "image_url": file_url,
                        "media_type": media_type
                    }]
                else:
                    transformed_messages.append({"type": role, "text": message})
            # print("MESSAGES:", transformed_messages)
            payload = {
                "conversation_history": transformed_messages,
                "stream": False,
                "model_name": "reka-core",
                "random_seed": 1714772311371
            }

            headers = {
                "authority": "chat.reka.ai",
                "authorization": f"Bearer {self.auth_key}",
            }

            response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

            # self.save_key(response)
            threading.Thread(target=self.update_app_session_thread).start()
            return response.json()['text']
        except Exception as e:
            print("Error in generate (reka):", e)

prompt = """Что здесь изображено?
Выведи текст с изображения в формате JSON. На капче 4 цифры чёрного цвета.
{
"text":int
}"""

if __name__ == "__main__":
    api = Reka_API(app_session="^_^")
    print("access key", api.auth_key)

    answer = api.generate(messages=[{"role": "user", "content": prompt}],
                          file_path=r"C:\Users\as280\Downloads\capha2.png", media_type=MediaType.image)

    print(answer)
