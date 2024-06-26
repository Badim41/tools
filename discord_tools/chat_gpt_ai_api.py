import datetime
import html
import json
import os.path
import re
import requests
import threading
import time
from datetime import datetime

from discord_tools.logs import Logs, Color
from discord_tools.str_tools import create_query_dict_from_url, create_cookies_dict
from discord_tools.temp_gmail_test import Temp_Gmail_API

logger = Logs(warnings=True)

JSON_ACCOUNT_SAVE = "accounts.json"


class NoRestNonce(Exception):
    """NoRestNonce"""


class DailyLimitException(Exception):
    """Reached your daily limit"""


class CookieCheckException(Exception):
    """Cookie check failed"""


class QueryRejectedException(Exception):
    """Sorry, your query has been rejected."""


class MessageModeratedException(Exception):
    """'Sorry, your message has been rejected by moderation'"""


class NotLoggedException(Exception):
    """<a href=\"https:\/\/chatgate.ai\/login\" style=\"color: #fff; text-decoration: underline; font-weight: bold;\">Click to Login<\/a> and continue."""


class GPT_Models:
    gpt_4 = "gpt_4"  # tydbjd
    gpt_4o = "gpt_4o"  # 3siv3p
    dalle_e_3 = "dalle-e-3"  # 5rwkvr
    claude_opus = "chat-claude-opus"  # zdmvyq

    @staticmethod
    def get_id(model_name):
        secret_ids = {
            GPT_Models.gpt_4: "chatbot-tydbjd",
            GPT_Models.dalle_e_3: "chatbot-5rwkvr",
            GPT_Models.claude_opus: "chatbot-zdmvyq",
            GPT_Models.gpt_4o: "chatbot-3siv3p"
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
            try:
                self.update_class()
            except Exception as e:
                logger.logging("Cannot create class ChatGPT4-account:", e)
        else:
            self.email = email
            self.cookies = cookies
            self.kind = kind
            self.idToken = id_token
            self.refreshToken = refresh_token
            self.localId = local_id
            self.last_used = last_used

    def update_class(self, force_reload=False):
        if force_reload:
            logger.logging("Force register new account for chatgate")

        account = ChatGPT_4_Account.load()
        if account and not force_reload:
            self.__dict__.update(account.__dict__)
        else:
            # raise Exception("Not found account")
            for i in range(3):
                try:
                    self.create_account()
                    return
                except Exception as e:
                    logger.logging("Error in create account:", e)

            raise Exception("Timeout in login account")

    def print_instance_vars(self):
        logger.logging("Значения переменных экземпляра:", color=Color.GRAY)
        for attr, value in self.__dict__.items():
            logger.logging(f"{attr}: {value}", color=Color.GRAY)

    def init_api(self):
        return ChatGPT_4_Site(proxies=self.proxies), Temp_Gmail_API()

    def create_account(self):
        if not self.api_chatgpt or not self.api_gmail:
            self.api_chatgpt, self.api_gmail = self.init_api()

        self.email, timestamp = self.api_gmail.get_gmail()
        self.api_chatgpt.email_send_code(self.email)

        result = self.api_gmail.wait_untill_send_message(gmail_address=self.email, timestamp=timestamp,
                                                         sender_name="chatgate.ai")
        query_dict = create_query_dict_from_url((correct_link(result)))
        self.kind, self.idToken, self.refreshToken, self.localId = self.api_chatgpt.sign_in_with_email_link(
            email=self.email,
            oob_code=query_dict['oobCode'])
        self.cookies = self.api_chatgpt.auto_register(local_id=self.localId, email=self.email)
        self.cookies = "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        self.save_to_json(last_used=1)
        self.bot_info = None

    def ask_gpt(self, prompt, model=GPT_Models.gpt_4o, attempts=4, image_path=None, chat_history=None,
                replace_prompt="??? ^", return_image_url=False):
        print("Модель GPT_ai:", model)
        try:
            if not chat_history:
                chat_history = []

            for i in range(attempts):

                if not self.api_chatgpt:
                    self.api_chatgpt = ChatGPT_4_Site()
                if not self.bot_info:
                    self.bot_info = self.api_chatgpt.get_bot_info_json(self.cookies)

                try:
                    if not self.bot_info["restNonce"]:
                        raise NoRestNonce

                    threading.Thread(target=self.recover_account).start()

                    answer = self.api_chatgpt.generate(prompt=prompt, cookies=self.cookies, bot_info=self.bot_info,
                                                       model=model, image_path=image_path, chat_history=chat_history,
                                                       replace_prompt=replace_prompt)

                    return answer

                except (DailyLimitException, CookieCheckException):
                    print("Reset account")
                    self.save_to_json()
                except (NotLoggedException, NoRestNonce):
                    print("Delete account chatgate ai")
                    self.save_to_json(last_used=20340420)

                # обновляем аккаунт
                self.update_class(force_reload=attempts - 2 == i)
        except Exception as e:
            logger.logging("Error in generate GHATGPT-4:", e)

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

    def save_to_json(self, last_used=None, refresh=False):
        if last_used is None:
            last_used = int(datetime.today().strftime("%Y%m%d"))

        try:
            with open(JSON_ACCOUNT_SAVE, 'r', encoding='utf-8') as f:
                instances = json.load(f)
        except FileNotFoundError:
            instances = []

        found_instance = False
        new_instances = []
        for instance in instances:
            if instance['email'] == self.email:
                if refresh:
                    instance['refreshToken'] = self.refreshToken
                    instance['idToken'] = self.idToken
                else:
                    instance['last_used'] = last_used
                found_instance = True
            new_instances.append(instance)

        if not found_instance:
            new_instances.append(self.to_dict(last_used=last_used))

        with open(JSON_ACCOUNT_SAVE, 'w', encoding='utf-8') as f:
            json.dump(new_instances, f, ensure_ascii=False, indent=4)

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

        today = datetime.today()
        for instance in instances:
            this_account_last_used = str(instance.last_used)
            if len(this_account_last_used) == 1:
                this_account_last_used = "20200101"

            last_used_date = datetime.strptime(this_account_last_used, "%Y%m%d")
            if (today - last_used_date).days >= 1:
                print("select:", instance.email)
                return instance

    def recover_account(self):
        url = "https://securetoken.googleapis.com/v1/token"

        querystring = {"key": self.api_chatgpt.apiKey}

        payload = f"grant_type=refresh_token&refresh_token={self.refreshToken}"

        headers = {
            "authority": "securetoken.googleapis.com",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://chatgate.ai",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "x-client-version": "Chrome/JsCore/9.6.6/FirebaseCore-web",
        }

        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

        response_json = response.json()

        self.refreshToken = response_json['refresh_token']
        self.idToken = response_json['id_token']

        url = "https://identitytoolkit.googleapis.com/v1/accounts:lookup"

        querystring = {"key": self.api_chatgpt.apiKey}

        payload = {"idToken": self.idToken}

        headers = {
            "authority": "identitytoolkit.googleapis.com",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://chatgate.ai",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "x-client-version": "Chrome/JsCore/9.6.6/FirebaseCore-web",
            "x-firebase-gmpid": "1:430595938852:web:a8639030eeddf71e9d16b1"
        }

        requests.request("POST", url, json=payload, headers=headers, params=querystring)
        # print("refresh")
        self.save_to_json(refresh=True)


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
    def print_cookie(response, type=""):
        cookies_dict = response.cookies.get_dict()
        logger.logging("cookies", type, cookies_dict, color=Color.GRAY)

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
        # print("RESPONCE TEXT:", response.text)
        theme_json = ChatGPT_4_Site.get_json_from_response(response.text, "firebaseOptions")
        logger.logging("API key", theme_json['apiKey'], color=Color.GRAY)
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
        kind = "-"
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
        url = f"https://chatgate.ai/gpt-4o"

        payload = ""
        headers = {
            "authority": "chatgate.ai",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, cookies=create_cookies_dict(cookies), proxies=self.proxies)

        result = re.search(r"data-system='(.*?)'", response.text)

        print("restNonce", json.loads(html.unescape(result.group(1)))["restNonce"])

        if result:
            return json.loads(html.unescape(result.group(1)))
        else:
            raise Exception("NO NONCE")

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
        logger.logging("firebaseLoginKey", firebase_json, firebase_json['firebaseLoginKey'], color=Color.GRAY)
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

        logger.logging(response.text)
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
            'x-wp-nonce': str(bot_info["restNonce"])
        }

        files = {
            'file': (image_path, open(image_path, 'rb'), 'image/png'),
        }
        data = {
            'type': 'image',
            'purpose': model,
        }

        response = requests.post(url, headers=headers, files=files, data=data)

        logger.logging(response.text, color=Color.GRAY)
        response_json = response.json()
        # print("uploaded image:", response_json)
        if response_json['success']:
            return response_json['data']['id']
        else:
            raise Exception("No success")

    def generate(self, prompt, cookies, bot_info, model, image_path=None, chat_id="eev1322xkeg", chat_history=None,
                 replace_prompt="??? ^"):
        if image_path:
            image_id = self.upload_file(image_path=image_path, cookies=cookies, bot_info=bot_info, model=model)
        else:
            image_id = None

        if not chat_history:
            chat_history = []
        chat_history_temp = chat_history

        role = ""
        if len(chat_history_temp) > 1:
            if chat_history_temp[0]['role'] == 'system':
                role = chat_history_temp[0]['content']
                role = "" if role == "Ты полезный ассистент и даёшь только полезную информацию" else role

        # абуз бага. Сайт не принимает более 1000 символов, но запрос загружается в историю
        if len(prompt) + len(role) > 800:
            if role:
                chat_history_temp.append({"role": "user", "content": f"Role: {role}\n\n\n{prompt}"})
            else:
                chat_history_temp.append({"role": "user", "content": prompt})
            chat_history_temp.append({"role": "assistant", "content": "."})
            prompt = replace_prompt
        elif role:
            prompt = f"Role: {role}\n\n\n{prompt}"

        # print(chat_history)
        # return
        bot_id = GPT_Models.get_id(model_name=model)
        url = "https://chatgate.ai/wp-json/mwai-ui/v1/chats/submit"

        payload = {
            "botId": bot_id,
            "customId": None,
            "session": "N/A",
            "chatId": chat_id,
            "contextId": 66740,
            "messages": chat_history_temp,
            "newMessage": prompt,
            "newFileId": image_id,
            "stream": False
        }
        headers = {
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
            "x-wp-nonce": str(bot_info["restNonce"])
        }

        # logger.logging("REST:", bot_info["restNonce"], bot_info)

        response = requests.request("POST", url, json=payload, headers=headers, cookies=create_cookies_dict(cookies), proxies=self.proxies)
        last_line = response.text.split("data: ")[-1]
        logger.logging(last_line, color=Color.GRAY)

        if "Reached your daily limit" in response.text:
            raise DailyLimitException
        elif 'Cookie check failed' in response.text:
            raise CookieCheckException
        elif 'Sorry, your query has been rejected.' in response.text:
            raise QueryRejectedException
        elif 'Sorry, your message has been rejected by moderation' in response.text:
            raise MessageModeratedException
        elif 'Click to Login' in response.text:
            raise NotLoggedException

        answer = json.loads(last_line)['reply']

        return answer


def clear_email_list(filename):
    with open(filename, "r", encoding="utf-8") as reader:
        json_data = json.load(reader)

    logger.logging("ACCOUNTS:", len(json_data), color=Color.GREEN)

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
    # arguments = sys.argv
    # if len(arguments) > 1:
    #     JSON_ACCOUNT_SAVE = arguments[1]
    #     logger.logging("name:", JSON_ACCOUNT_SAVE)

    # clear_email_list(JSON_ACCOUNT_SAVE)

    proxy = "socks5://localhost:5051"  # Здесь указываем порт 5051, как в вашей команде SSH

    proxies = {
        'http': proxy,
        'https': proxy
    }
    # account.api_chatgpt, account.api_gmail = account.init_api()
    # print(account.api_chatgpt.auto_register(local_id=account.localId, email=account.email))

    #
    # print(account.ask_gpt(prompt="Какая ты модель GPT?"))  # _vision, image_path=r"C:\Users\as280\Downloads\temp.png"
    for i in range(50):
        account = ChatGPT_4_Account()
        for i in range(10):
            try:
                account.create_account()
                time.sleep(60)
            except Exception as e:
                logger.logging(e)
