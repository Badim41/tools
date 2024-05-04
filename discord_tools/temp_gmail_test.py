import json
import re
import requests
import time
from requests import Session
import random
import string

from discord_tools.astica_API import Astica_Free_API_key
from discord_tools.logs import Logs

logger = Logs(warnings=True)


#

class MailTMInvalidResponse(Exception):
    """Raised when the response from the MailTM API is not valid."""
    pass


def random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def validate_response(response) -> bool:
    if response.status_code in [200, 201, 204]:
        return True
    else:
        return False


def extract_urls(text):
    # Регулярное выражение для поиска URL в тексте
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    # Используем регулярное выражение для поиска всех URL в тексте
    urls = re.findall(url_pattern, text)

    return urls


class MailTM:
    API_URL = "https://api.mail.tm"

    def __init__(self, session: Session = None):
        self.session = session or Session()

    def get_account_token(self, address, password):
        """
        https://docs.mail.tm/#authentication
        """
        headers = {
            "accept": "application/ld+json",
            "Content-Type": "application/json"
        }
        response = self.session.post(f"{self.API_URL}/token", data=json.dumps({
            "address": address,
            "password": password
        }), headers=headers)
        logger.logging(f'Response for {self.API_URL}/token: {response.status_code}, {response.text}, ')
        if validate_response(response):
            return response.json()
        logger.logging(f'Error response for {self.API_URL}/token: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def get_domains(self):
        """
        https://docs.mail.tm/#get-domains
        """
        response = self.session.get(f"{self.API_URL}/domains")
        logger.logging(f'Response for {self.API_URL}/domains: {response.status_code}, {response.text}, ')
        if validate_response(response):
            return response.json()
        logger.logging(f'Error response for {self.API_URL}/domains: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def get_account(self, address=None, password=None):
        # return {'@context': '/contexts/Account', '@id': '/accounts/6628c1fd5767af2c3e012014', '@type': 'Account', 'id': '6628c1fd5767af2c3e012014', 'address': '59k4zwm0@fthcapital.com', 'quota': 40000000, 'used': 0, 'isDisabled': False, 'isDeleted': False, 'createdAt': '2024-04-24T08:25:33+00:00', 'updatedAt': '2024-04-24T08:25:33+00:00', 'token': {'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE3MTM5NDcxMzMsInJvbGVzIjpbIlJPTEVfVVNFUiJdLCJhZGRyZXNzIjoiNTlrNHp3bTBAZnRoY2FwaXRhbC5jb20iLCJpZCI6IjY2MjhjMWZkNTc2N2FmMmMzZTAxMjAxNCIsIm1lcmN1cmUiOnsic3Vic2NyaWJlIjpbIi9hY2NvdW50cy82NjI4YzFmZDU3NjdhZjJjM2UwMTIwMTQiXX19.UGPTqSC5sd7kankvYgfSsTu4DxHzQqzFLniSMCiIu9HB3gpU1qxbKEFcUGe_LFbhIM3dzVYTzMbyFz-aIkg__g', '@id': '/accounts/6628c1fd5767af2c3e012014', 'id': '6628c1fd5767af2c3e012014'}}
        """
        https://docs.mail.tm/#post-accounts
        """
        if address is None:
            domains = self.get_domains()
            domain = domains['hydra:member'][0]['domain']
            address = f"{random_string()}@{domain}"
        if password is None:
            password = random_string()
        payload = {
            "address": address,
            "password": password
        }
        logger.logging(f'Create account with payload: {payload}')
        response = self.session.post(f"{self.API_URL}/accounts", json=payload)
        logger.logging(f'Response for {self.API_URL}/accounts: {response.status_code}, {response.text}, ')
        if validate_response(response):
            response = response.json()
            token = self.get_account_token(address=address, password=password)
            response['token'] = token
            return response
        logger.logging(f'Error response for {self.API_URL}/accounts: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def get_account_by_id(self, account_id, token):
        """
        https://docs.mail.tm/#get-accountsid
        """
        response = self.session.get(f"{self.API_URL}/accounts/{account_id}",
                                    headers={"Authorization": f"Bearer {token}"})
        logger.logging(f'Response for {self.API_URL}/accounts/{account_id}: {response.status_code}, {response.text}, ')
        if validate_response(response):
            return response.json()
        logger.logging(
            f'Error response for {self.API_URL}/accounts/{account_id}: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def delete_account_by_id(self, account_id, token):
        """
        https://docs.mail.tm/#delete-accountsid
        """
        response = self.session.delete(f"{self.API_URL}/accounts/{account_id}",
                                       headers={'Authorization': f'Bearer {token}'})
        logger.logging(f'Response for {self.API_URL}/accounts/{account_id}: {response.status_code}, {response.text}, ')
        if validate_response(response):
            return response.status_code == 204
        logger.logging(
            f'Error response for {self.API_URL}/accounts/{account_id}: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def get_messages(self, token, page=1):
        """
        https://docs.mail.tm/#get-messages
        """
        response = self.session.get(f"{self.API_URL}/messages?page={page}",
                                    headers={'Authorization': f'Bearer {token}'})
        logger.logging(f'Response for {self.API_URL}/messages: {response.status_code}, {response.text}, ')
        if validate_response(response):
            return response.json()
        logger.logging(f'Error response for {self.API_URL}/messages: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def get_message_source_by_id(self, message_id, token):
        """
        Получает источник сообщения по его идентификатору.

        Параметры:
        message_id (str): Идентификатор сообщения.
        token (str): Токен авторизации.

        Возвращает:
        dict: Источник сообщения в формате JSON.

        Исключения:
        MailTMInvalidResponse: Если ответ от API недействителен.
        """
        response = self.session.get(f"{self.API_URL}/messages/{message_id}",
                                    headers={'Authorization': f'Bearer {token}'})
        print(f"{self.API_URL}/messages/{message_id}")
        logger.logging(
            f'Response for {self.API_URL}/messages/{message_id}/source: {response.status_code}, {response.text}, ')
        if validate_response(response):
            return response.json()
        logger.logging(
            f'Error response for {self.API_URL}/messages/{message_id}/source: {response.status_code}, {response.text}, ')
        raise MailTMInvalidResponse

    def wait_untill_send_message(self, sender_email, token, attemps=120):
        for i in range(attemps):
            # Получение списка сообщений для аккаунта
            messages = self.get_messages(token=token)
            message_ids = [m['id'] for m in messages['hydra:member']]
            print(f"Список сообщений: {message_ids}")

            # содержимое
            for message_id in message_ids:
                message_source = self.get_message_source_by_id(message_id, token=token)
                if sender_email in message_source['from']['address']:
                    return message_source['text']
            time.sleep(1)


class Temp_Gmail_API:
    def __init__(self, capcha_code=None, proxies=None):
        if not capcha_code:
            capcha_code = "03AFcWeA6ibuyjAK5sX-b5iPi0kyrIV8RT0KW54_YBKYahASdBLypnhg7v4yKjncXl1tw6lmOjPb1JexbYaO8D-7wOK6xYyzOC3T60Xg9NoYYkb4rhX7M4c_IUGNlPmPC9coUmh3L2Ldwpa0HPi62ifZAqmuPtLgC0Dggsm_1j-Ryhk7wj-Q5iZyL4SR6NmHu-3yUnh7q9S9dTlHqngDrcPWZzF7W6ARjMVwy0UEBJ4ymVwiIwTdxzKn2BPzAigY5bErIhwLoH4bXH5-DAuc3x_CSsFgZSgDSPrt0DA83rzh7sCIITnnUo7kfyRcc80Fqv7dhstVdIgxfMW6LN-ADtyLPMBHTHO9vIqqwYK-FRF70jYiO9ErGrLEtp7TFp2doTcOrcmLiO4sEUj95kF7i2y3ZFAwICPJyKm5BrQhcOuGp17TpjuTwiy7puzLz6uqbYT8-S6YcyHXQ-hqzshGMy-T69VkoLhkVHN82gugfyEpnKPbz7BsZGUrdC7Q0O2dZxBM-0RMlWFliUgq-cWxxukdJt8Id9SFWkkE8w289wWbn_yZqVgwhmpHpi_UkytTCTrkmqcZ2RvNMMYB7vVHlb2qUzLEkA3qYFVNJ_KqLTJGuc-3UySPWhuXpM6G_Gr8vRTgTrpLrFFlEAy4Wn-k-WsBUVAfX936oU0ZDxV__ua-F0LuzSm1uDMJ7iquT2poxl5FkpBcFrSMY6MDSGPBoXfsG-DUCZtWpD4Q"
        self.capcha_code = capcha_code
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        self.proxies = proxies
        self.xsrf_token, self.sonjj_session = None, None
        self.base_page_html = self.get_base_page_html()
        self.site_key = Astica_Free_API_key.find_key(self.base_page_html, r'sitekey="([\w-]+)"')
        self.rapid_api_key = None

    def update_cookies(self, response):
        time.sleep(3)
        cookies = response.cookies.get_dict()
        return cookies['XSRF-TOKEN'], cookies['sonjj_session']

    def get_base_page_html(self):
        url = "https://smailpro.com/temp-gmail"

        payload = ""
        headers = {
            "authority": "smailpro.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": self.user_agent
        }

        response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)

        self.xsrf_token, self.sonjj_session = self.update_cookies(response)

        return response.text

    def get_rapidapi_key(self):
        endpoints = [
            'vendors~smailpro_v2_email~smailpro_v2_history~smailpro_v2_inbox',
            'adsense_lazy',
            'modal',
            'smailpro_v2_control',
            'smailpro_v2_email',
            'smailpro_v2_history',
            'smailpro_v2_identity2',
            'smailpro_v2_inbox',
            'vendors~smailpro_v2_identity2',
            'ychecker_v2'
        ]

        ids = [
            'dc69ae7652c94ae0a508',
            '3792ae0e084ec623a8fe',
            'bb993956dff5d01a5730',
            'd949b31695e8500fa0f3',
            '865c551fa579e8e25484',
            '60348fbb156e627647ef',
            'ce459cb1c1d015591afb',
            'e82838f209dbf846a706',
            '60d91fc8b182015d7fec',
            '34b2d583128d5898cd28'
        ]

        order = [1, 8, 6, 3, 0, 7, 4, 2, 5]

        result_html = ""
        for key in order:
            endpoint = endpoints[key]
            id = ids[key]

            url = f"https://smailpro.com/js/chunks/{endpoint}.js"

            querystring = {"id": id}

            payload = ""
            headers = {
                "Referer": "https://smailpro.com/temp-gmail",
                "sec-ch-ua-mobile": "?0",
                "User-Agent": self.user_agent
            }

            response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

            if endpoint == "smailpro_v2_email":
                result_html = response.text

            print(endpoint, ":", response.status_code)
            time.sleep(0.5)

        if not result_html:
            raise Exception("Not found result_html")

        repid_api_key = Astica_Free_API_key.find_key(result_html, r'rapidapi_key:"([\w-]+)"')
        print("repid_api_key", repid_api_key)
        return repid_api_key

    def get_gmail_get_key(self):
        url = "https://smailpro.com/app/key"

        payload = {
            "domain": "gmail.com",
            "username": "random",
            "server": "server-1",
            "type": "alias"
        }

        headers = {
            "cookie": f"XSRF-TOKEN={self.xsrf_token}; sonjj_session={self.sonjj_session}",
            "authority": "smailpro.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://smailpro.com",
            "referer": "https://smailpro.com/temp-gmail",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
            "x-g-token": self.capcha_code,
            "x-xsrf-token": self.xsrf_token.replace("%3D", "=")
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        self.xsrf_token, self.sonjj_session = self.update_cookies(response)

        print("get_gmail_get_key", response.text)

        return response.json()['items']

    def get_gmail(self):
        url = "https://api.sonjj.com/email/gm/get"

        if not self.rapid_api_key:
            self.rapid_api_key = self.get_rapidapi_key()

        querystring = {
            "key": self.get_gmail_get_key(),
            "rapidapi-key": self.rapid_api_key, "domain": "gmail.com",
            "username": "random", "server": "server-1", "type": "alias"}

        payload = ""
        headers = {
            "authority": "api.sonjj.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "origin": "https://smailpro.com",
            "referer": "https://smailpro.com/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.user_agent,
            "x-rapidapi-ua": "RapidAPI-Playground"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        print("get_gmail", response.text)

        response_json = response.json()
        return response_json['items']['email'], response_json['items']['timestamp']

    def get_gmail_auth_key(self, gmail_address, timestamp):
        url = "https://smailpro.com/app/key"

        payload = {
            "email": gmail_address,
            "timestamp": timestamp
        }

        headers = {
            "cookie": f"XSRF-TOKEN={self.xsrf_token}; sonjj_session={self.sonjj_session}",
            "authority": "smailpro.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://smailpro.com",
            "referer": "https://smailpro.com/temp-gmail",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
            "x-g-token": self.capcha_code,
            "x-xsrf-token": self.xsrf_token.replace("%3D", "=")
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        print("get_gmail_auth_key", response.text)
        time.sleep(1)

        return response.json()['items']

    def get_key_to_messages(self, gmail_address, message_id):
        url = "https://smailpro.com/app/key"

        payload = {
            "email": gmail_address,
            "message_id": message_id
        }

        headers = {
            "cookie": f"XSRF-TOKEN={self.xsrf_token}; sonjj_session={self.sonjj_session}",
            "authority": "smailpro.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://smailpro.com",
            "referer": "https://smailpro.com/temp-gmail",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
            "x-g-token": self.capcha_code,
            "x-xsrf-token": self.xsrf_token.replace("%3D", "=")
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        print("get_key_to_messages", response.text)
        time.sleep(2)

        return response.json()['items']

    def get_message(self, gmail_address, message_id):
        url = "https://api.sonjj.com/email/gm/read"

        querystring = {
            "key": self.get_key_to_messages(gmail_address=gmail_address, message_id=message_id),
            "rapidapi-key": self.rapid_api_key,
            "email": gmail_address, "message_id": message_id}

        payload = ""
        headers = {
            "authority": "api.sonjj.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "origin": "https://smailpro.com",
            "referer": "https://smailpro.com/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.user_agent,
            "x-rapidapi-ua": "RapidAPI-Playground"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        print("get_message", response.text)
        return response.json()['items']['body']

    def wait_untill_send_message(self, gmail_address, timestamp, sender_name, attempts=10):
        for i in range(attempts):
            time.sleep(15)
            messages = self.get_messages(gmail_address, timestamp)
            for message in messages:
                if sender_name in message['textFrom']:
                    return self.get_message(gmail_address, message['mid'])
                print("gmail message from:", message['textFrom'])

    def get_messages(self, gmail_address, timestamp):
        url = "https://api.sonjj.com/email/gm/check"

        querystring = {
            "key": self.get_gmail_auth_key(gmail_address=gmail_address, timestamp=timestamp),
            "rapidapi-key": self.rapid_api_key,
            "email": gmail_address, "timestamp": timestamp}

        payload = ""
        headers = {
            "authority": "api.sonjj.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "origin": "https://smailpro.com",
            "referer": "https://smailpro.com/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
            "x-rapidapi-ua": "RapidAPI-Playground"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        print("get_messages", response.text)

        return response.json()['items']


def get_temp_gmail_message(sender_name, capcha_code=None):
    api = Temp_Gmail_API()
    gmail_address, timestamp = api.get_gmail()
    message_row = api.wait_untill_send_message(gmail_address=gmail_address, timestamp=timestamp,
                                               sender_name=sender_name)
    return message_row


def get_temp_email_message(sender_email, password=None):
    mail_tm = MailTM()
    # # Получение список доменов
    domains = mail_tm.get_domains()
    available_domains = [domain['domain'] for domain in domains['hydra:member']]
    # print(f"Доступные домены: {available_domains}")
    # Создание нового аккаунта
    account = mail_tm.get_account(password=password)
    token = account['token']['token']
    message_row = mail_tm.wait_untill_send_message(sender_email=sender_email, token=token)
    return message_row


if __name__ == "__main__":
    message_row = get_temp_email_message("stab")
    urls = extract_urls(message_row)
    print(urls)
    for url in urls:
        if url.startswith("https://dashboard.cohere.com/confirm-email"):
            print(url)
