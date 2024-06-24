import execjs
import json
import math
import os
import random
import requests
import traceback
from datetime import datetime

from discord_tools.logs import Logs
from discord_tools.str_tools import get_cookie_dict_from_response, extract_urls, create_cookies_dict, image_to_base64
from discord_tools.temp_gmail_test import MailTM, random_string

logger = Logs(warnings=True)
JSON_ACCOUNT_SAVE = "deep_ai_account.json"


class DeepAIError(Exception):
    """Ошибка DeepAIError"""
    text = "Ошибка DeepAIError"


class DeepAILimitError(Exception):
    """Ошибка DeepAIError"""
    text = "Достигнут лимит"


class DeepAI_autoreg():
    def __init__(self, proxies=None):
        self.proxies = proxies
        self.username = random_string()
        self.address = None
        self.account = None
        self.password = None
        self.api_key = None
        self._cookies = None
    def login(self):
        headers = {
            'accept': '*/*',
            'accept-language': 'ru,en;q=0.9',
            'origin': 'https://deepai.org',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36',
        }

        files = {
            'username': (None, self.address),
            'password': (None, self.password),
        }

        response = requests.post('https://api.deepai.org/daily-time-sync/login/', headers=headers,
                                 files=files)

        self._cookies = get_cookie_dict_from_response(response)
    def send_message_on_email(self):
        url = 'https://api.deepai.org/daily-time-sync/registration/'
        headers = {
            'accept': '*/*',
            'accept-language': 'ru,en;q=0.9',
            'origin': 'https://deepai.org',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36'
        }

        files = {
            'email': (None, self.address),
            'username': (None, self.address),
            'password1': (None, self.password),
            'password2': (None, self.password)
        }

        response = requests.post(url, headers=headers, files=files, proxies=self.proxies)
        if not response.status_code == 204:
            error = DeepAIError()
            error.text += f" при регистрации: {response.text}"
            raise error

        print("send_message_on_email", response.text, response.status_code)

    def get_user_info(self):
        url = "https://api.deepai.org/daily-time-sync/user"

        payload = ""
        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "origin": "https://deepai.org",
            "priority": "u=1, i",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, cookies=self._cookies, proxies=self.proxies)

        print(response.status_code)
        print("get_user_info", response.json())
        self.api_key = response.json()['userprofile']['api_key']

    def register_account(self):
        mail_tm = MailTM()
        domains = mail_tm.get_domains()
        available_domains = [domain['domain'] for domain in domains['hydra:member']]
        self.address = f"{random_string()}@{available_domains[0]}"
        self.account = mail_tm.get_account(address=self.address)
        self.password = random_string(length=30)

        self.send_message_on_email()

        self.login()

        # self.get_user_info()

        # print(f"Login: {self.address}\nPassword: {self.password}")



class DeepAI_API():
    def __init__(self, proxies=None, cookies=None, create_new=True, last_used=None, email=None, password=None, attempts=3):
        self.proxies = proxies
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.6.0.0 Safari/537.37'
        self.attempts = attempts

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
                    print("cookies:", self.cookies)
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
        autoreg = DeepAI_autoreg(proxies=self.proxies)

        autoreg.register_account()

        self.cookies = autoreg._cookies
        self.cookies = "; ".join([f"{key}={value}" for key, value in self.cookies.items()]) + "; _ga=GA1.1.1345731647.1719186490; consentUUID=ae450b60-77db-4bae-880f-6b438a0e4272_33; consentDate=2024-06-23T23:49:01.645Z; usnatUUID=a628bcb3-34d9-4c48-a634-f2135efe478b; _cc_id=a3d6e999f27c429a7ab4f684e8e0e7f1; panoramaId_expiry=1719791344906; panoramaId=1675f966d4f1aee7abd825befccc185ca02ca7dd512bb10a6d5ff65bd0dbe6b0; panoramaIdType=panoDevice; __qca=P0-278961403-1719186542213; bounceClientVisit6726v=N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgCYCmpEAhgJYB0A9gE4DmRIANCIzCGRTQxYcQ1FAH1m9MSlIoU1egDsYAM0pgZnURIjTZ8pavWaQM5jADaAXQC+QA; __idcontext=eyJjb29raWVJRCI6IjJpSW5lSHJUTFFLRm9iN3ZxYnRRUmphR0E3eSIsImRldmljZUlEIjoiMmlJbmVKc1hIS29BcDdjTFdmZDJlZGRSTGpuIiwiaXYiOiIiLCJ2IjoiIn0%3D; user_sees_ads=true; __gads=ID=cdb2c4129f90042b:T=1719186544:RT=1719187206:S=ALNI_MYKC43pvQCUNthSLrSKXdz3gbaZxA; __gpi=UID=00000e635f0c3cf0:T=1719186544:RT=1719187206:S=ALNI_MYWZLrDQ0JIbK-GrJx6GIBsGAWWZA; __eoi=ID=4cfbe10503afe7ce:T=1719186544:RT=1719187206:S=AA-Afjap5yPh6OH2A_svC6rW8uwr; bounceClientVisit6726=N4IgJglmIFwgHATgIwBYDsisAYBsiAmA+AZkRJORABoQA3KWZdZFedbAVgM8+21K0AZnQAuTFm3QFUqWgEMA9rGy0ANgAdYIABajRGgM4BSEgEFjBAGKWrYAKb2N8iADpFAJwDmtmiHmGKrR0GnSwnLTQcNC0HtoOTi7u3n4AxmISrMjsXAS0howwBKogXqlxMIglALZBIGoZMMxZ7DJy4F5WEB6GogAyivJRoh4Arva0OvIeYACSACLaBBCzAHb2ABIeACp9AIoA0laKAEbodACOJ6J7AEoAVvIA4mboAJ5+hopCogtLK+sAFKGAAaGwOijMGnQqT6AHUhGACPYwGBbn17qsQABfIA; _ga_GY2GHX2J9Y=GS1.1.1719186489.1.1.1719187275.23.0.0"
        self.email = autoreg.address #                                                           _ga=GA1.1.1345731647.1719186490; consentUUID=ae450b60-77db-4bae-880f-6b438a0e4272_33; consentDate=2024-06-23T23:49:01.645Z; usnatUUID=a628bcb3-34d9-4c48-a634-f2135efe478b; _cc_id=a3d6e999f27c429a7ab4f684e8e0e7f1; panoramaId_expiry=1719791344906; panoramaId=1675f966d4f1aee7abd825befccc185ca02ca7dd512bb10a6d5ff65bd0dbe6b0; panoramaIdType=panoDevice; __qca=P0-278961403-1719186542213; __idcontext=eyJjb29raWVJRCI6IjJpSW5lSHJUTFFLRm9iN3ZxYnRRUmphR0E3eSIsImRldmljZUlEIjoiMmlJbmVKc1hIS29BcDdjTFdmZDJlZGRSTGpuIiwiaXYiOiIiLCJ2IjoiIn0%3D; __gads=ID=cdb2c4129f90042b:T=1719186544:RT=1719194581:S=ALNI_MYKC43pvQCUNthSLrSKXdz3gbaZxA; __gpi=UID=00000e635f0c3cf0:T=1719186544:RT=1719194581:S=ALNI_MYWZLrDQ0JIbK-GrJx6GIBsGAWWZA; __eoi=ID=4cfbe10503afe7ce:T=1719186544:RT=1719194581:S=AA-Afjap5yPh6OH2A_svC6rW8uwr; bounceClientVisit6726v=N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgCYCmpEAhgJYB0A9gE4DmRAtpQMZzUB2pAWjClKjXn2YC29MmCIJSADwS5qbZiAA0IRjBBkKNBiy0hqKAPrN6FlKRQpq9XjABmlMHe3mrEW-cdnNw8vEDsNaABtAF0AXyA; bounceClientVisit6726=N4IgJglmIFwgHATgIwBYDsisAYBsiAmA+AZkRJORABoQA3KWZdZFRVAVkQ4-RKUS0AZnQAuTFinjpiyWgEMA9rGy0ANgAdYIABajRGgM4BSEgEFjBAGKWrYAKb2N8iADpFAJwDmtgLbyAYx0IADt7AFo1e3kPENCvcN9FBzVbUXsAD1ECCF8vGhB5QxVaOg06JlpoOGhaD20HJxd3bwKAsQlWVk5uWkNGGFRaLwD6mERVEF8SkDUOmGYu9i4OKq8rCA9DUQAZRXlq0Q8AV3taHRiwAEkAEW0cq7CACQ8AFR2ARQBpK0UAI3QdAAjn9RB8AEoAK3kAHEzOgAJ4FQyKISiW73CCPewAKUMAA0nl9FGYNOgAjsAOpCMAEexgMDgnaQkIgAC+QA; _ga_GY2GHX2J9Y=GS1.1.1719194583.2.1.1719194614.29.0.0
        self.password = autoreg.password #                                                       _ga=GA1.1.1345731647.1719186490; consentUUID=ae450b60-77db-4bae-880f-6b438a0e4272_33; consentDate=2024-06-23T23:49:01.645Z; usnatUUID=a628bcb3-34d9-4c48-a634-f2135efe478b; _cc_id=a3d6e999f27c429a7ab4f684e8e0e7f1; panoramaId_expiry=1719791344906; panoramaId=1675f966d4f1aee7abd825befccc185ca02ca7dd512bb10a6d5ff65bd0dbe6b0; panoramaIdType=panoDevice; __qca=P0-278961403-1719186542213; __idcontext=eyJjb29raWVJRCI6IjJpSW5lSHJUTFFLRm9iN3ZxYnRRUmphR0E3eSIsImRldmljZUlEIjoiMmlJbmVKc1hIS29BcDdjTFdmZDJlZGRSTGpuIiwiaXYiOiIiLCJ2IjoiIn0%3D; __gads=ID=cdb2c4129f90042b:T=1719186544:RT=1719194581:S=ALNI_MYKC43pvQCUNthSLrSKXdz3gbaZxA; __gpi=UID=00000e635f0c3cf0:T=1719186544:RT=1719194581:S=ALNI_MYWZLrDQ0JIbK-GrJx6GIBsGAWWZA; __eoi=ID=4cfbe10503afe7ce:T=1719186544:RT=1719194581:S=AA-Afjap5yPh6OH2A_svC6rW8uwr; bounceClientVisit6726v=N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgCYCmpEAhgJYB0A9gE4DmRAtpQMZzUB2pAWjClKjXn2YC29MmCIJSADwS5qbZiAA0IRjBBkKNBiy0hqKAPrN6FlKRQpq9XjABmlMHe3mrEW-cdnNw8vEDsNaABtAF0AXyA; bounceClientVisit6726=N4IgJglmIFwgHATgIwBYDsisAYBsiAmA+AZkRJORABoQA3KWZdZFRVAVkQ4-RKUS0AZnQAuTFinjpiyWgEMA9rGy0ANgAdYIABajRGgM4BSEgEFjBAGKWrYAKb2N8iADpFAJwDmtgLbyAYx0IADt7AFo1e3kPENCvcN9FBzVbUXsAD1ECCF8vGhB5QxVaOg06WA5aaDhoWg9tBycXd28CgLEJVlZOblpDRhgCVRAvAIaYRBHfEpA1TphmbvYp+GqvKwgPQ1EAGUV5GtEPAFd7Wh0YsABJABFtHOuwgAkPABVdgEUAaStFACN0HQAI7-USfABKACt5ABxMzoACeBUMiiEojuDwgT3sAClDAANZ7fRRmDToAK7ADqQjABHsYDAEN2UJCIAAvkA; _ga_GY2GHX2J9Y=GS1.1.1719194583.2.1.1719194908.53.0.0

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

    def generate_api_key(self):
        js_code = f'var userAgent = "{self.user_agent}";' + """
                            p = Math.round(1E11 * Math.random()) + "";
                            var q = function() {
                                for (var A = [], F = 0; 64 > F; )
                                    A[F] = 0 | 4294967296 * Math.sin(++F % Math.PI);
                                return function(B) {
                                    var G, K, L, ba = [G = 1732584193, K = 4023233417, ~G, ~K], V = [], x = unescape(encodeURI(B)) + "\u0080", v = x.length;
                                    B = --v / 4 + 2 | 15;
                                    for (V[--B] = 8 * v; ~v; )
                                        V[v >> 2] |= x.charCodeAt(v) << 8 * v--;
                                    for (F = x = 0; F < B; F += 16) {
                                        for (v = ba; 64 > x; v = [L = v[3], G + ((L = v[0] + [G & K | ~G & L, L & G | ~L & K, G ^ K ^ L, K ^ (G | ~L)][v = x >> 4] + A[x] + ~~V[F | [x, 5 * x + 1, 3 * x + 5, 7 * x][v] & 15]) << (v = [7, 12, 17, 22, 5, 9, 14, 20, 4, 11, 16, 23, 6, 10, 15, 21][4 * v + x++ % 4]) | L >>> -v), G, K])
                                            G = v[1] | 0,
                                            K = v[2];
                                        for (x = 4; x; )
                                            ba[--x] += v[x]
                                    }
                                    for (B = ""; 32 > x; )
                                        B += (ba[x >> 3] >> 4 * (1 ^ x++) & 15).toString(16);
                                    return B.split("").reverse().join("")
                                }
                            }();
                            var w = "tryit-" + p + "-" + q(userAgent + q(userAgent + q(userAgent + p + "x")));
                            w;
                            """

        # Создаем контекст выполнения JavaScript
        ctx = execjs.compile(js_code)

        # Выполняем код и получаем результат
        return str(ctx.eval('w'))

    def check_valid_response(self, response):
        if response.text == '{"status": "signed in try-it quota exceeded"}':
            print("change account deep ai", response.text)
            self.save_to_json()
            self.update_class()
            return False
        return True

    def generate_image(self, prompt, image_generator_version="hd", output_path="image.png"):
        for i in range(self.attempts):
            headers = {
                'accept': '*/*',
                'accept-language': 'ru,en;q=0.9',
                'api-key': self.generate_api_key(),
                'origin': 'https://deepai.org',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': self.user_agent
            }

            files = {
                'text': (None, prompt),
                'image_generator_version': (None, image_generator_version),
            }

            print("send cookies:", self.cookies)

            response = requests.post('https://api.deepai.org/api/text2img', cookies=create_cookies_dict(self.cookies), headers=headers, files=files, proxies=self.proxies)

            if not self.check_valid_response(response):
                continue

            print(response.text, response.status_code)
            print(response.json())
            # TODO SAVE IMAGE
    def generate_text(self, chat_history):
        for i in range(self.attempts):
            try:

                url = 'https://api.deepai.org/hacking_is_a_serious_crime'
                headers = {
                    'accept': '*/*',
                    'accept-language': 'ru,en;q=0.9',
                    'api-key': self.generate_api_key(),
                    'origin': 'https://deepai.org',
                    'priority': 'u=1, i',
                    'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': self.user_agent
                }

                files = {
                    'chat_style': (None, 'chat'),
                    'chatHistory': (None, str(chat_history).replace("\'","\""))
                }

                response = requests.post(url, headers=headers, files=files, proxies=self.proxies)

                if not self.check_valid_response(response):
                    continue

                return response.text
            except Exception as e:
                logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))
                return

    def generate_video(self, prompt, output_file="video.mp4"):
        for i in range(self.attempts):
            headers = {
                'accept': '*/*',
                'accept-language': 'ru,en;q=0.9',
                'api-key': self.generate_api_key(),
                'origin': 'https://deepai.org',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': self.user_agent
            }

            files = {
                'textPrompt': (None, prompt),
                'dimensions': (None, '{"width":1024,"height":1024}'),
            }

            response = requests.post('https://api.deepai.org/generate_video', cookies=create_cookies_dict(self.cookies), headers=headers, files=files, proxies=self.proxies, timeout=180)

            if not self.check_valid_response(response):
                continue

            print(response.text)

            # Проверяем успешность запроса
            response = requests.get(response.json()['videoPresignedUrl'], stream=True)

            if response.status_code == 200:
                with open(output_file, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                print(f"Видео успешно сохранено как {output_file}")
                return output_file
            else:
                print("Ошибка при скачивании видео:", response.status_code)
    def generate_audio(self, prompt, output_file="audio.mp3"):
        for i in range(self.attempts):
            headers = {
                'accept': '*/*',
                'accept-language': 'ru,en;q=0.9',
                'api-key': self.generate_api_key(),
                'content-type': 'application/json',
                'origin': 'https://deepai.org',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Chromium";v="124", "YaBrowser";v="24.6", "Not-A.Brand";v="99", "Yowser";v="2.5"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': self.user_agent
            }

            json_data = {
                'text': prompt,
            }

            response = requests.post('https://api.deepai.org/audio_response', cookies=create_cookies_dict(self.cookies), headers=headers,
                                     json=json_data, proxies=self.proxies)

            if not self.check_valid_response(response):
                continue

            with open(output_file, "wb") as file:
                file.write(response.content)
            return output_file

if __name__ == '__main__':
    # autoreg = DeepAI_autoreg()
    # autoreg.register_account()
    # print("_cookies")
    # exit()
    proxy = "socks5://localhost:5052"

    proxies = {"http": proxy, "https": proxy}
    deep_ai_api = DeepAI_API(proxies=proxies, attempts=1, create_new=True)

    try:
        for i in range(1000):
            # chat_history = [{"role":"user","content":"В комнате было 10 книг, 2 я прочитал. Сколько книг осталось в комнате?"}]
            # result = deep_ai_api.generate_text(chat_history)
            # print(f"result-text-{i}", result)

            result = deep_ai_api.generate_image("cat run on street")
            print(f"result-image-{i}", result)

            # result = deep_ai_api.generate_video("cat run on street")
            # print(f"result-video-{i}", result)

            # result = deep_ai_api.generate_audio('piano, minecraft soundtrack')
            # print(f"result-audio-{i}", result)
    except DeepAIError as e:
        logger.logging("DeepAIError:", e.text)
    except Exception as e:
        logger.logging("Неизвестная ошибка:", e)
