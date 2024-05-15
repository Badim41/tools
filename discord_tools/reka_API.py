import os
import requests
from discord_tools.sql_db import get_database

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
        self.app_session = get_database(ConfigKeysReka.reka, ConfigKeysReka.reka)
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
            url = "https://chat.reka.ai/bff/auth/firebase_token"

            payload = ""
            headers = {
                "cookie": f"appSession={self.app_session}",
            }

            response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)

            cookie_dict = get_cookie_dict_from_response(response)

            url = "https://chat.reka.ai/bff/auth/access_token"

            payload = ""
            headers = {
                "cookie": f"appSession={cookie_dict['appSession']}",
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

            return response.json()['text']
        except Exception as e:
            print("Error in generate (reka):", e)


if __name__ == "__main__":
    api = Reka_API(app_session="app_session")
    print("access key", api.auth_key)

    answer = api.generate(messages=[{"role": "user", "content": "Какая игра на видео?"}],
                          file_path=r"C:\Users\as280\Pictures\mine-imator\falling.mp4", media_type=MediaType.video)

    print(answer)
