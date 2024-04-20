import html
import json
import os.path
import re
import requests
import sys
import urllib
from datetime import date

from discord_tools.logs import Logs
from discord_tools.temp_gmail import Temp_Email_API

logger = Logs(warnings=True)

JSON_ACCOUNT_SAVE = "accounts.json"

class GPT_Models:
    gpt_4 = "gpt4"  # tydbjd
    gpt_4_vision = "vision"  # kvic0w
    dalle_e_3 = "dalle-e-3"  # 5rwkvr
    claude_opus = "chat-claude-opus"  # zdmvyq
    claude_vision = "chat-claude-vision"  # 12oenm

    @staticmethod
    def get_id(model_name):
        secret_ids = {
            GPT_Models.gpt_4: "chatbot-tydbjd",
            GPT_Models.gpt_4_vision: "chatbot-kvic0w",
            GPT_Models.dalle_e_3: "chatbot-5rwkvr",
            GPT_Models.claude_opus: "chatbot-zdmvyq",
            GPT_Models.claude_vision: "chatbot-12oenm"
        }
        if model_name not in secret_ids:
            raise Exception("Не найден ID для модели", model_name)
        return secret_ids.get(model_name)


def correct_link(text):
    start_index = text.find("https://")
    end_index = text.find("'", start_index)
    original_link = text[start_index:end_index]
    corrected_link = original_link.replace("&amp;", "&")
    return corrected_link


class ChatGPT_4_Account:
    def __init__(self, email=None, cookies=None, kind=None, id_token=None, refresh_token=None, local_id=None,
                 last_used=None, create_new=True, proxies=None):
        self.proxies = proxies
        self.sender = "noreply@auth.chatgate.ai"
        self.api_chatgpt = None
        self.api_gmail = None
        self.bot_info = None

        if create_new:
            self.update_class()
        else:
            self.email = email
            self.cookies = cookies
            self.kind = kind
            self.idToken = id_token
            self.refreshToken = refresh_token
            self.localId = local_id
            self.last_used = last_used

    def update_class(self):
        account = ChatGPT_4_Account.load()
        if account:
            self.__dict__.update(account.__dict__)
        else:
            for i in range(3):
                try:
                    self.create_account()
                    return
                except Exception as e:
                    logger.logging("Error in create account:", e)

            raise Exception("Timeout in login account")

    def print_instance_vars(self):
        logger.logging("Значения переменных экземпляра:")
        for attr, value in self.__dict__.items():
            logger.logging(f"{attr}: {value}")

    def init_api(self):
        return ChatGPT_4_Site(proxies=self.proxies), Temp_Email_API(proxies=self.proxies)

    def create_account(self):
        if not self.api_chatgpt or not self.api_gmail:
            self.api_chatgpt, self.api_gmail = self.init_api()

        self.email = self.api_gmail.get_email()
        self.api_chatgpt.email_send_code(self.email)
        result = Temp_Email_API.get_message(email=self.email, sender=self.sender,
                                            xsrf_token=self.api_gmail.xsrf_token, session_id=self.api_gmail.session_id)
        query_dict = ChatGPT_4_Site.create_query_dict((correct_link(result)))
        self.kind, self.idToken, self.refreshToken, self.localId = self.api_chatgpt.sign_in_with_email_link(
            email=self.email,
            oob_code=query_dict['oobCode'])
        self.cookies = self.api_chatgpt.auto_register(local_id=self.localId, email=self.email)
        self.cookies = "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        self.save_to_json(last_used=1)
        self.bot_info = None

    def ask_gpt(self, prompt, model=GPT_Models.gpt_4, attempts=3, image_path=None):
        for i in range(attempts):

            if not self.api_chatgpt:
                self.api_chatgpt = ChatGPT_4_Site()
            if not self.bot_info:
                self.bot_info = self.api_chatgpt.get_bot_info_json(self.cookies)

            try:
                return self.api_chatgpt.generate(prompt=prompt, cookies=self.cookies, bot_info=self.bot_info,
                                                 model=model, image_path=image_path)
            except Exception as e:
                if "Reached your daily limit" in str(e):
                    self.save_to_json()
                    self.update_class()
                else:
                    raise e

    def to_dict(self, last_used):
        return {
            "email": self.email,
            "cookies": self.cookies,
            "kind": self.kind,
            "idToken": self.idToken,
            "refreshToken": self.refreshToken,
            "localId": self.localId,
            "last_used": last_used
        }

    def save_to_json(self, last_used=None):
        if last_used is None:
            last_used = int(date.today().strftime("%Y%m%d"))

        try:
            with open(JSON_ACCOUNT_SAVE, 'r', encoding='utf-8') as f:
                instances = json.load(f)
        except FileNotFoundError:
            instances = []

        found_instance = False
        for instance in instances:
            if instance['email'] == self.email:
                found_instance = True
                instance['last_used'] = last_used

        if not found_instance:
            instances.append(self.to_dict(last_used=last_used))

        with open(JSON_ACCOUNT_SAVE, 'w', encoding='utf-8') as f:
            json.dump(instances, f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls):
        if not os.path.exists(JSON_ACCOUNT_SAVE):
            return

        instances = []
        with open(JSON_ACCOUNT_SAVE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for instance_data in data:
            instance = cls(
                email=instance_data.get("email"),
                cookies=instance_data.get("cookies"),
                kind=instance_data.get("kind"),
                id_token=instance_data.get("idToken"),
                refresh_token=instance_data.get("refreshToken"),
                local_id=instance_data.get("localId"),
                last_used=instance_data.get("last_used"),
                create_new=False
            )
            instances.append(instance)

        today = int(date.today().strftime("%Y%m%d"))
        for instance in instances:
            if instance.last_used != today:
                return instance


class ChatGPT_4_Site:
    def __init__(self, proxies=None):
        self.proxies = proxies
        self.apiKey = self.get_api_key()
        self.firebase_key = self.get_firebase_login_key()

    @staticmethod
    def get_json_from_response(text, key):
        pattern = r"var\s+" + key + r"\s*=\s*(\{.* ?\})"
        result = re.search(pattern, text)
        if result:
            result_json = json.loads(html.unescape(result.group(1)))
            return result_json

    @staticmethod
    def create_query_dict(url):
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        query_dict = {}
        for param, value in query_params.items():
            query_dict[param] = value[0]

        return query_dict
    @staticmethod
    def print_cookie(response, type=""):
        cookies_dict = response.cookies.get_dict()
        logger.logging("cookies", type, cookies_dict)

    def get_api_key(self):
        querystring = {"redirect_to": "https://chatgate.ai/"}

        payload = ""
        headers = {
            "authority": "chatgate.ai",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9",
            "cache-control": "max-age=0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        }

        response = requests.request("GET", "https://chatgate.ai/login", data=payload, headers=headers,
                                    params=querystring, proxies=self.proxies)
        theme_json = ChatGPT_4_Site.get_json_from_response(response.text, "firebaseOptions")
        logger.logging("API key", theme_json['apiKey'])
        return theme_json['apiKey']

    def email_send_code(self, email):
        url = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"

        querystring = {"key": self.apiKey}

        payload = {
            "requestType": "EMAIL_SIGNIN",
            "email": email,
            "continueUrl": "https://chatgate.ai/login?redirect_tohttps%3A%2F%2Fchatgate.ai%2F&ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN&ui_sd0",
            "canHandleCodeInApp": True
        }

        headers = {"origin": "https://chatgate.ai"}

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring,
                                    proxies=self.proxies)

    def sign_in_with_email_link(self, email, oob_code):
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithEmailLink"

        querystring = {"key": self.apiKey}

        payload = {
            "email": email,
            "oobCode": oob_code
        }
        headers = {
            "authority": "identitytoolkit.googleapis.com",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://chatgate.ai",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-client-version": "Chrome/JsCore/9.6.6/FirebaseCore-web",
            "x-firebase-locale": "en"
        }

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring,
                                    proxies=self.proxies)
        response_json = response.json()
        kind = response_json['kind']
        idToken = response_json['idToken']
        refreshToken = response_json['refreshToken']
        localId = response_json['localId']
        return kind, idToken, refreshToken, localId

    # def get_account_info(self, id_token):
    #     url = "https://identitytoolkit.googleapis.com/v1/accounts:lookup"
    #
    #     querystring = {"key": self.apiKey}
    #
    #     payload = {"idToken": id_token}
    #
    #     headers = {
    #         "authority": "identitytoolkit.googleapis.com",
    #         "accept": "*/*",
    #         "accept-language": "ru,en;q=0.9",
    #         "content-type": "application/json",
    #         "origin": "https://chatgate.ai",
    #         "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    #         "sec-ch-ua-mobile": "?0",
    #         "sec-ch-ua-platform": '"Windows"',
    #         "sec-fetch-dest": "empty",
    #         "sec-fetch-mode": "cors",
    #         "sec-fetch-site": "cross-site",
    #         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    #         "x-client-version": "Chrome/JsCore/9.6.6/FirebaseCore-web",
    #         "x-firebase-locale": "en"
    #     }
    #
    #     response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

    # logger.logging(response.text)
    # self.print_cookie(response, "Register")

    def get_bot_info_json(self, cookies):
        url = f"https://chatgate.ai/gpt4"

        payload = ""
        headers = {
            "cookie": cookies,
            "authority": "chatgate.ai",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9",
            "referer": "https://chatgate.ai/vision/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)

        result = re.search(r"data-system='(.*?)'", response.text)

        if result:
            return json.loads(html.unescape(result.group(1)))

    def get_firebase_login_key(self):
        headers = {
            "authority": "chatgate.ai",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9",
            "referer": "https://auth.chatgate.ai/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-site",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        }

        response = requests.request("GET", "https://chatgate.ai/login", data="", headers=headers, params="",
                                    proxies=self.proxies)

        firebase_json = ChatGPT_4_Site.get_json_from_response(response.text, "firebaseWordpress")
        logger.logging("firebaseLoginKey", firebase_json, firebase_json['firebaseLoginKey'])
        return firebase_json['firebaseLoginKey']

    def auto_register(self, local_id, email):
        url = "https://chatgate.ai/wp-json/firebase/v2/users/register-autologin"

        payload = {"user": {
            "userId": local_id,
            "password": "3gr9e55obz",
            "email": email,
            "providers": ["password"]
        }}

        headers = {
            "authority": "chatgate.ai",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "ru,en;q=0.9",
            "auth-source": "wordpress",
            "content-type": "application/json",
            "firebase-login-key": self.firebase_key,
            "origin": "https://chatgate.ai",
            "referer": "https://chatgate.ai/login?redirect_tohttps%3A%2F%2Fchatgate.ai%2F&ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN&ui_sd0&lang=en",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

        # logger.logging(response.text)
        # ChatGPT_4_Site.print_cookie(response, "LOGGED")

        if "wordpress_logged_in_9a8088c047aa8a4d022063748baad4c8" not in response.cookies:
            raise Exception("С данного IP временно невозможно регистрировать аккаунты, используйте прокси")

        return response.cookies.get_dict()

    def upload_file(self, image_path, cookies, bot_info, model):
        if not os.path.exists(image_path):
            raise Exception("File not exists")

        url = 'https://chatgate.ai/wp-json/mwai-ui/v1/files/upload'

        headers = {
            'authority': 'chatgate.ai',
            'cookie': cookies,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36',
            'x-wp-nonce': bot_info["restNonce"]
        }

        files = {
            'file': (image_path, open(image_path, 'rb'), 'image/png'),
        }
        data = {
            'type': 'image',
            'purpose': model,
        }

        response = requests.post(url, headers=headers, files=files, data=data)

        logger.logging(response.text)
        response_json = response.json()
        if response_json['success']:
            return response_json['data']['id']
        else:
            raise Exception("No success")

    def generate(self, prompt, cookies, bot_info, model, image_path=None, chat_id="eev1322xkeg"):
        if image_path:
            image_id = self.upload_file(image_path=image_path, cookies=cookies, bot_info=bot_info, model=model)
            if model not in [GPT_Models.gpt_4_vision, GPT_Models.claude_vision]:
                logger.logging(f"Модель {model} не имеет доступа к изображениям. Модель заменена на GPT4-vision")
            model = GPT_Models.gpt_4_vision
        else:
            image_id = None

        bot_id = GPT_Models.get_id(model_name=model)
        url = "https://chatgate.ai/wp-json/mwai-ui/v1/chats/submit"

        payload = {
            "botId": bot_id,
            "customId": None,
            "session": "N/A",
            "chatId": chat_id,
            "contextId": 1048,
            "messages": [
                {
                    "id": "1t2bie5i7fy",
                    "role": "assistant",
                    "content": "Hi! How can I assist you today?",
                    "who": "AI: ",
                    "timestamp": 1713505272724
                }
            ],
            "newMessage": prompt,
            "newFileId": image_id,
            "stream": True
        }
        headers = {
            'cookie': cookies,
            "authority": "chatgate.ai",
            "accept": "text/event-stream",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://chatgate.ai",
            "referer": "https://chatgate.ai/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
            "x-wp-nonce": bot_info["restNonce"]
        }

        # logger.logging("REST:", bot_info["restNonce"], bot_info)

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)
        last_line = response.text.split("data: ")[-1]
        logger.logging(last_line)

        if "Reached your daily limit" in response.text:
            raise Exception("Reached your daily limit")

        answer = json.loads(json.loads(last_line)['data'])['reply']

        return answer


def clear_email_list(filename):
    with open(filename, "r", encoding="utf-8") as reader:
        json_data = json.load(reader)

    logger.logging("ACCOUNTS:", len(json_data))

    filtered_data = [item for item in json_data if
                     "wordpress_logged_in_9a8088c047aa8a4d022063748baad4c8" in item["cookies"]]

    with open(JSON_ACCOUNT_SAVE, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4)


def merge_json_files(directory):
    merged_data = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                data = json.load(file)
                merged_data.extend(data)
    return merged_data


# # Пример использования
# directory_path = '/path/to/directory'
# merged_json = merge_json_files(directory_path)
# logger.logging(json.dumps(merged_json, indent=4))

if __name__ == "__main__":
    arguments = sys.argv
    if len(arguments) > 1:
        JSON_ACCOUNT_SAVE = arguments[1]
        logger.logging("name:", JSON_ACCOUNT_SAVE)

    clear_email_list(JSON_ACCOUNT_SAVE)

    account = ChatGPT_4_Account()
    print(account.ask_gpt(prompt="Что это?", image_path=r"lolo_telegram_2.png"))  # _vision, image_path=r"C:\Users\as280\Downloads\temp.png"
    # for i in range(50):
    #     try:
    #         account.create_account()
    #         time.sleep(20)
    #     except Exception as e:
    #         logger.logging(e)
