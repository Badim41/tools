import json
import os
import re
import requests
import traceback
from datetime import datetime

from discord_tools.logs import Logs
from discord_tools.str_tools import create_cookies_dict
from discord_tools.temp_gmail_test import MailTM, random_string

logger = Logs(warnings=True)
JSON_ACCOUNT_SAVE = "exactly_ai_account.json"


class ExactlyAIError(Exception):
    """Ошибка ExactlyAI"""
    text = "Ошибка ExactlyAI"


class ExactlyAILimitError(Exception):
    """Ошибка ExactlyAI"""
    text = "Достигнут лимит"


class ExactlyAI_autoreg():
    def __init__(self, proxies=None):
        self.proxies = proxies
        self.username = random_string()
        self.address = None
        self.account = None
        self.password = None
        self.cookies = None

    def send_message_on_email(self):
        url = "https://api.exactly.ai/v0/auth/signup"
        payload = {
            "email": self.address,
            "name": self.username
        }
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://app.exactly.ai",
            "priority": "u=1, i",
            "referer": "https://app.exactly.ai/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if not response.json()['message'] == "Submission registered.":
            error = ExactlyAIError()
            error.text += f" при регистрации: {response.text}"
            raise error

    def set_password_on_site(self, password, access_token):
        url = f"https://api.exactly.ai/v0/auth/signup/set-password/{access_token}"

        payload = {"password": password}

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://app.exactly.ai",
            "priority": "u=1, i",
            "referer": "https://app.exactly.ai/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        print("set_password_on_site", response.cookies)
        if not response.json()['message'] == "Password has been set successfully.":
            error = ExactlyAIError()
            error.text += f" при смене пароля: {response.text}"
            raise error

    def register_account(self):

        mail_tm = MailTM()
        domains = mail_tm.get_domains()
        available_domains = [domain['domain'] for domain in domains['hydra:member']]
        self.address = f"{random_string()}@{available_domains[0]}"
        self.account = mail_tm.get_account(address=self.address)

        self.send_message_on_email()

        message_row = mail_tm.wait_untill_send_message(sender_email="support@exactly.ai",
                                                       token=self.account['token']['token'])

        match = re.search(r"token=([a-f0-9]+)", message_row)

        if match:
            access_token = match.group(1)
        else:
            error = ExactlyAIError()
            error.text += f": Не найден токен"
            raise error

        self.password = random_string(length=30)

        print(f"Login: {self.address}\nPassword: {self.password}")

        self.set_password_on_site(password=self.password, access_token=access_token)

        self.cookies = None


class ExactlyAI_API():
    def __init__(self, proxies=None, cookies=None, create_new=True, last_used=None, email=None, password=None):
        self.proxies = proxies

        if create_new:
            try:
                self.update_class()
            except Exception as e:
                logger.logging("Cannot create class ChatGPT4-account:", e)
        else:
            self.last_used = last_used
            self.cookies = cookies
            self.email = email
            self.password = password

    def update_class(self):
        account = self.load()
        if account:
            proxies_temp = self.proxies
            self.__dict__.update(account.__dict__)
            self.proxies = proxies_temp
        else:
            # raise Exception("Not found account")
            for i in range(3):
                try:
                    self.create_account()
                    return
                except Exception as e:
                    logger.logging("Error in create account:", e)

            raise Exception("Timeout in login account")

    def to_dict(self, last_used):
        return {
            "email": self.email,
            "password": self.password,
            "cookies": self.cookies,
            "last_used": last_used
        }

    @classmethod
    def load(cls):
        if not os.path.exists(JSON_ACCOUNT_SAVE):
            return

        instances = []
        with open(JSON_ACCOUNT_SAVE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for instance_data in data:
            instance = cls(
                last_used=instance_data.get("last_used"),
                cookies=instance_data.get("cookies"),
                email=instance_data.get("email"),
                password=instance_data.get("password"),
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

    def create_account(self):
        autoreg = ExactlyAI_autoreg(proxies=self.proxies)

        autoreg.register_account()

        self.cookies = autoreg.cookies
        self.cookies = "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
        self.email = autoreg.address
        self.password = autoreg.password

        self.save_to_json(last_used=1)

    def save_to_json(self, last_used=None):
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
                instance['last_used'] = last_used
                found_instance = True
            new_instances.append(instance)

        if not found_instance:
            new_instances.append(self.to_dict(last_used=last_used))

        with open(JSON_ACCOUNT_SAVE, 'w', encoding='utf-8') as f:
            json.dump(new_instances, f, ensure_ascii=False, indent=4)

    def get_csrftoken(self):
        url = "https://api.exactly.ai/v0/session/csrf"

        payload = ""
        # cookies = {
        #     'sessionid': '9yzzkx34ok9t8w25q1pb69kvbtg4c6ja',
        #     'AMP_164cd6a680': 'JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjJkMDk5MjYwMy1jYWY5LTRkYjAtOGU4Mi05NmUyODUxMzVkMjglMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjJmYTkxNGZmZS0zYjRhLTQ3MTMtYjQ3ZC05NmM2ZDIzZjE4Y2ElMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzE5MDEyNDI5NjQ5JTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTcxOTAxMzg5OTA1OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNjQlMkMlMjJwYWdlQ291bnRlciUyMiUzQTEzJTdE',
        # }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "origin": "https://app.exactly.ai",
            "priority": "u=1, i",
            "referer": "https://app.exactly.ai/",
            "^sec-ch-ua": "^\^Chromium^^;v=^\^124^^, ^\^YaBrowser^^;v=^\^24.6^^, ^\^Not-A.Brand^^;v=^\^99^^, ^\^Yowser^^;v=^\^2.5^^^",
            "sec-ch-ua-mobile": "?0",
            "^sec-ch-ua-platform": "^\^Windows^^^",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, cookies=create_cookies_dict(self.cookies))

        print("get_csrftoken", response.text)

        return response.text.replace("\"", "")

    def generate(self, prompt, weight=512, height=512, n_images=4,
                 model_id="b5a81055-24b8-42a7-a902-b191cffac8ab", frame_id='66760e23a501c27aeceb249f'):
        for i in range(3):
            try:

                headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'ru,en;q=0.9',
                    'content-type': 'application/json',
                    'origin': 'https://app.exactly.ai',
                    'priority': 'u=1, i',
                    'referer': 'https://app.exactly.ai/',
                    'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36',
                    'x-csrftoken': self.get_csrftoken(),
                }

                params = {
                    'exp_flag_grants': '3',
                }

                json_data = {
                    'frame_id': frame_id,
                    'params': {
                        'type': 'create',
                        'model_uid': model_id,
                        'prompt': prompt,
                        'size': [
                            weight,
                            height,
                        ],
                        'n_images': n_images,
                    },
                }

                response = requests.post('https://api.exactly.ai/v2/inference', params=params, headers=headers, json=json_data,
                                         cookies=create_cookies_dict(self.cookies))

                if response.status_code == 403:
                    print(response.text, response.status_code)
                    raise ExactlyAILimitError

                print(response.text, response.status_code)
            except ExactlyAILimitError:
                print("Delete account exactly ai")
                self.save_to_json(last_used=20340420)
                self.update_class()
            except Exception as e:
                logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))
                return


if __name__ == '__main__':
    # autoreg = ExactlyAI_autoreg()
    # autoreg.register_account()
    # exit()

    exactly_ai_api = ExactlyAI_API(cookies=cookies, create_new=False)

    try:
        exactly_ai_api.generate(prompt="")
    except ExactlyAIError as e:
        logger.logging("ExactlyAIError:", e.text)
    except Exception as e:
        logger.logging("Неизвестная ошибка:", e)
