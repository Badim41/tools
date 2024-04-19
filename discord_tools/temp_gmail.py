import re
import requests
import time

import json

import html

import urllib
from datetime import date

JSON_ACCOUNT_SAVE = "accounts.json"

class Temp_Email_API:
    def __init__(self):
        response = requests.request("GET", "https://www.emailnator.com/", data="", headers={})
        self.xsrf_token, self.session_id = self.get_tokens(response)

    def get_tokens(self, response):
        cookies_dict = response.cookies.get_dict()
        # print("Updated cookie")
        return cookies_dict['XSRF-TOKEN'], cookies_dict['gmailnator_session']

    def get_email(self):
        # print("get gmail")
        url = "https://www.emailnator.com/generate-email"

        payload = {"email": ["dotGmail"]}

        headers = {
            "cookie": f"XSRF-TOKEN={self.xsrf_token}; gmailnator_session={self.session_id}",
            "authority": "www.emailnator.com",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "x-xsrf-token": self.xsrf_token.replace("%3D", "=")
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        self.xsrf_token, self.session_id = self.get_tokens(response)

        return response.json()['email'][0]

    @staticmethod
    def get_message(email, sender, xsrf_token, session_id, message_id=None, attempts=50):
        for i in range(attempts):
            try:
                # print("get messages")
                url = "https://www.emailnator.com/message-list"

                if message_id:
                    payload = {
                        "email": email,
                        "messageID": message_id
                    }
                else:
                    payload = {
                        "email": email
                    }

                headers = {
                    "cookie": f"XSRF-TOKEN={xsrf_token}; gmailnator_session={session_id}",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
                    "x-requested-with": "XMLHttpRequest",
                    "x-xsrf-token": xsrf_token.replace("%3D", "=")
                }

                response = requests.request("POST", url, json=payload, headers=headers)

                print(response.text)

                if not message_id:
                    message_ids = []
                    for message in response.json()["messageData"]:
                        if message["from"] == sender:
                            message_ids.append(message["messageID"])

                    if not message_ids:
                        time.sleep(3)
                        continue
                    return Temp_Email_API.get_message(email=email, xsrf_token=xsrf_token, session_id=session_id,
                                                      message_id=message_ids[-1], sender=sender)
                else:
                    return response.text
            except Exception as e:
                print("Warn", e)
                time.sleep(10)
        raise Exception(f"Не получено сообщение от отправителя {sender}!")


def correct_link(text):
    # Находим индекс начала ссылки
    start_index = text.find("https://")

    # Находим индекс конца ссылки
    end_index = text.find("'", start_index)

    # Получаем исходную ссылку
    original_link = text[start_index:end_index]

    # Заменяем &amp; на &
    corrected_link = original_link.replace("&amp;", "&")

    return corrected_link


class ChatGPT_4_Account:
    def __init__(self, email=None, cookies=None, kind=None, id_token=None, refresh_token=None, local_id=None, last_used=None):
        self.email = email
        self.cookies = cookies
        self.kind = kind
        self.idToken = id_token
        self.refreshToken = refresh_token
        self.localId = local_id
        self.last_used = last_used

    def create_account(self):
        self.sender = "noreply@auth.chatgate.ai"
        self.api_chatgpt = ChatGPT_4_Site()
        self.api_gmail = Temp_Email_API()
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
        self.save_to_json(last_used="JUST CREATED")

    def ask_gpt(self, prompt):
        return self.api_chatgpt.generate(prompt=prompt, cookies=self.cookies)

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
            last_used = date.today()

        instances = []

        instances.append(self.to_dict(last_used=last_used))

        with open(JSON_ACCOUNT_SAVE, 'w', encoding='utf-8') as f:
            json.dump(instances, f, ensure_ascii=False, indent=4)

    @classmethod
    def load_from_json(cls):
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
                last_used=date.fromisoformat(instance_data.get("last_used"))  # Преобразуем строку обратно в дату
            )
            instances.append(instance)

        today = date.today()
        for instance in instances:
            if instance.last_used != today:
                return instance

        return None


class ChatGPT_4_Site:
    def __init__(self):
        self.apiKey = self.get_api_key()
        self.firebase_key = self.get_firebase_login_key()
        self.bot_info = self.get_bot_info_json()

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

    def print_cookie(self, response, type=""):
        cookies_dict = response.cookies.get_dict()
        print("cookies", type, cookies_dict)

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
                                    params=querystring)
        theme_json = ChatGPT_4_Site.get_json_from_response(response.text, "firebaseOptions")
        print("API key", theme_json['apiKey'])
        return theme_json['apiKey']

    def email_send_code(self, email):
        url = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"

        querystring = {"key": self.apiKey}

        payload = {
            "requestType": "EMAIL_SIGNIN",
            "email": email,
            "continueUrl": "https://chatgate.ai/login?redirect_tohttps%3A%2F%2Fchatgate.ai%2F&ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN&ui_sd0",
            #              "https://chatgate.ai/login?redirect_to=https%3A%2F%2Fchatgate.ai%2F&ui_sid=hlaHgIwNEtBns6JAxpc9vnd879JbNezh&ui_sd=0"
            #           GOT:https://chatgate.ai/login?redirect_to%3Dhttps%253A%252F%252Fchatgate.ai%252F%26ui_sid%3DhlaHgIwNEtBns6JAxpc9vnd879JbNezh%26ui_sd%3D0
            #              "identitytoolkit#CreateAuthUriResponse"
            #              "LDBP4nAaSZHx09gWLnZFGHhR6SQ"
            "canHandleCodeInApp": True
        }

        headers = {"origin": "https://chatgate.ai"}

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

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

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
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

    # print(response.text)
    # self.print_cookie(response, "Register")

    def get_bot_info_json(self):
        url = "https://chatgate.ai/gpt4"

        payload = ""
        headers = {
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

        response = requests.request("GET", url, data=payload, headers=headers)

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

        response = requests.request("GET", "https://chatgate.ai/login", data="", headers=headers, params="")

        firebase_json = ChatGPT_4_Site.get_json_from_response(response.text, "firebaseWordpress")
        # print("firebaseLoginKey", firebase_json, firebase_json['firebaseLoginKey'])
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

        response = requests.request("POST", url, json=payload, headers=headers)

        print(response.text)
        self.print_cookie(response, "LOGGED")
        return response.cookies.get_dict()

    def generate(self, prompt, cookies, chat_id="eev1322xkeg", bot_id="chatbot-tydbjd"):
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
            "newFileId": None,
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
            "x-wp-nonce": self.bot_info["restNonce"]
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        print(response.text)


api = ChatGPT_4_Site()
print(api.bot_info)
# chat_gpt4 = ChatGPT_4_Account()
# print()

# input("press enter")
# result = Temp_Email_API.get_message(email=gmail_adress, sender="noreply@auth.chatgate.ai",
#                                     xsrf_token=email_api.xsrf_token, session_id=email_api.session_id)
# print(result)
# chat_gpt_4.get_account_info(id_token=idToken)

# # eneter
# eyJpdiI6IlY5blBCRWdncXpoOG9HTnlRRHlNcEE9PSIsInZhbHVlIjoiTVdJQko4dXlMNXpzbDNFYmpNQU5qMGZuRFk5T3hZaGk3M0szN0RJbXh5V1BwL0ZPeGs0RStNQXB3NEYxMi9aUjdMZ2FwcTd2d3A1MTdqMjIwbFVDdlVvRURkQmxINDZwRVpPemZ4TjZCYkxwRmVxeE0wSGw0cmwwaTVjRHZabEwiLCJtYWMiOiJkYjdkODQyMzc4MTgwNTBkNWM0ZDI3NTZkMWJlNmU4ZGM1YjllM2I0M2FiNDM5MGI5NDk4NDBlYTdmZjE3M2YyIiwidGFnIjoiIn0
# eyJpdiI6InZ2UktTblBnTWs3Yk45dDJLYWtuZEE9PSIsInZhbHVlIjoicndlWjA1TGF0a2RnZ2E2WGF4Ujl0QjVBMU90V3llSllReFlLZk1BY05BaUVvNHR4eWRPY1N4UkhiMGtLendWWEY0Nm1ndStsaTdUOGYwWnQ1VHNFYVkwZEFPK1hxWGV4K1BnZWJ2MHBRbjFYOGwrNzhMU0E5Z0JuWERiOGVqbjUiLCJtYWMiOiI4ZTMwMzg2NWU2MjQ5MjQ0MTViZmE5MjdiNWZjMzFiZDk5YjlkZGVlYzc5M2I4M2JkMDgyMjI3OWU4MjZkZWUyIiwidGFnIjoiIn0

# # generate
# eyJpdiI6ImNOZlcwMlk4WHREUjRsU2o2T21VS3c9PSIsInZhbHVlIjoidVppUnBPd1o3RXg0T0JxUjZwbnlpaWpzUFBIc09XVENadUNWa2tzUzdMN3c4RmNCU3NZUFJSaURKc3p0UE1EWDUvM2x3MjJkeDdpUjc4MEw3OVRwcTNxNEpXQk1HQU43Y2UxNGpQY01DTmswbXluSURyVkk5dlNORTR1aERTVzkiLCJtYWMiOiI4ZjI0MGQxMmZmNjVhZTkyMjU2MzQyMmJhYTdiMzkyNDY1OWViOTI2YzVkODdjOGFkOGFjZjEwNmJmMjFjYjYxIiwidGFnIjoiIn0
# eyJpdiI6IlMyeUxnUUZ1T1JrWTdvWDFaUzZTY0E9PSIsInZhbHVlIjoiZ3RHWnFJclk2L2Z5WWNwME9tWGJYQWtzbFpJZ1ZjYURzRElyTWNFVGdCc3NRLzBTNjllbXk0OXdOWE0yQ3dwS3RHd0hYbU1jdG5XQlRuU3Z1anpETzhRVkpVZmZNaGlqRTlnNXozN3JBVDBLOEgrUFBoemxEUGdYK2hIQzRlc28iLCJtYWMiOiI0N2IzMzcwZDg4ZGRiZThlMjU5NzFkZGM0YzNjOTk4OWI1OGU2MmNlOGQ4YmQ5MjRiYzE3MmQ2NjJjMWFkM2QxIiwidGFnIjoiIn0

# # message list
# eyJpdiI6IjlPTkRrY0o2bkJCYXhIRVZEUWJlMmc9PSIsInZhbHVlIjoiQmhxNkpaT1djVVJpQis5UmtXaWtoSStQSTNzdnJ2dFpveDJLM21lYUhYV2RiS295RlBJUGlQSTVoUThwTXpRZUl3bS83Nm9DRHlTWDNwQ0d3azlYaFhRL2Y4NVcwdVJFZStpMFBkRFJUMjVxTVAzRXducWhIc1MrQ1dpZWxMaUEiLCJtYWMiOiJmMTVkNmY2YmQ3ODEzNGU0NTcxNzhmYzM5YzBlOTEzYzVmMmFkMmQxODA0NTcwZmRkNDlhNjZjYmFkZTAxZjI4IiwidGFnIjoiIn0
# eyJpdiI6ImRNZFE1enp1U3dKbUlpZ2RwaFhrWmc9PSIsInZhbHVlIjoienh2SE9KVGR5d3MvNVZqaVBtV1l2TGY4OGNHV1JCeW8vZzJzRTlEY3U0bkFNQXd5K0FpNjF6MWs3b29PWnFNMytBdU0xT3JONlFVQ2lVZnliYTF3Q2Z6OTY2VWlPc0NyM3pRSEd5REdWL2JBWUNnU0R0UGxwZzdiZzdZMjJPRnQiLCJtYWMiOiIxZWUzOGZjZjZhYmViY2ZhMjBkNWI5ODU0ZGU4MjA3NmMwMTUyNmEwZTVlOTI1NjU3NTU3MzVhMjYwOGYzOGFjIiwidGFnIjoiIn0

# # list 2
# eyJpdiI6IjVjVlNoSWF6b1Axa2dqdHc3SjF1QlE9PSIsInZhbHVlIjoiZGJQRHkwTUlGSTY1Q1I5SDU2NVA5YzUvZ3hFYWUxODBSR0ErNHc3djdFZkluRUtpS1hta1FINVNPTEVWUXd1bExFRXo5N2J1RUZjc0JaQk1KS1ZweGszT0VIVW5LQjlDVTZpV3RpU3VuN21wUEFFNkZ6aVpySWNQVTV0d1FWRDciLCJtYWMiOiJmNDAwNzMyM2FhYWQ1OTA0MTk2MzkxNWVmZjFkNGEwZDUxMjVhZDc1MzZhN2UyNjFiOWMwNTJjNDE4YzE3YjNiIiwidGFnIjoiIn0
# eyJpdiI6IldBK2ZBSDNBa2dOL3Q5MUsrTVRUcFE9PSIsInZhbHVlIjoiTzNUWVdBNDlZZFd5RlNmcEFEM1RUN0h4eVZIaDNia0tkem14SFpqTW9nY2tTUEozbVJUUmQ2SFZFL3Rlak5wcS9SajFEalJqQStOSkNZTEdGUEEzWFdYV0JKYVB4cEpET1Z1dnliaC9lSjk3U1AzSG85Y3NuVE5IMzhvamo1ekciLCJtYWMiOiJiOWFjMzVlYjA1NThlYWYwMTQ2MDk3ZGIwYWZmMDFlYjk5MWMyNjM2ODQ5ZjE4NmU3NmJmZjg3NzkyOTc0ZjdlIiwidGFnIjoiIn0


# https://auth.chatgate.ai/__/auth/action?apiKey=AIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20&mode=signIn&oobCode=RVQNjsMpPHiZs6hcOExIVosOJfBvoH4EE23MFBC6l-4AAAGO8FO94Q&continueUrl=https://chatgate.ai/login?redirect_to%3Dhttps%253A%252F%252Fchatgate.ai%252F%26ui_sid%3DikJUJfS96kDI9IkZgNBJnDBwFpKnTy3n%26ui_sd%3D0&lang=en
# https://auth.chatgate.ai/__/auth/action?apiKey=AIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20&amp;mode=signIn&amp;oobCode=RVQNjsMpPHiZs6hcOExIVosOJfBvoH4EE23MFBC6l-4AAAGO8FO94Q&amp;continueUrl=https://chatgate.ai/login?redirect_to%3Dhttps%253A%252F%252Fchatgate.ai%252F%26ui_sid%3DikJUJfS96kDI9IkZgNBJnDBwFpKnTy3n%26ui_sd%3D0&amp;lang=en

# site
# mwai_session_id=6621f804ceac4
# mwai_session_id=6621f9e02e07a

# all
# mwai_session_id=6621f804ceac4; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2024-04-19%2004%3A50%3A13%7C%7C%7Cep%3Dhttps%3A%2F%2Fchatgate.ai%2F%7C%7C%7Crf%3D%28none%29; sbjs_first_add=fd%3D2024-04-19%2004%3A50%3A13%7C%7C%7Cep%3Dhttps%3A%2F%2Fchatgate.ai%2F%7C%7C%7Crf%3D%28none%29; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F120.0.0.0%20YaBrowser%2F24.1.0.0%20Safari%2F537.36; sbjs_session=pgs%3D1%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fchatgate.ai%2F; _gid=GA1.2.1912586035.1713502214; _gcl_au=1.1.497207883.1713502214; _ga_TTDKRN293K=GS1.1.1713500610.1.1.1713502213.0.0.0; _ga=GA1.1.164357830.1713502214; _ga_EBNTF2FDZV=GS1.1.1713500610.1.1.1713502214.0.0.0; tk_ai=EGA%2FTATSayo8sHMyn5BSeQPd
# mwai_session_id=6621f804ceac4; sbjs_migrations=1418474375998%3D1; sbjs_session=pgs%3D1%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fchatgate.ai%2F; tk_ai=EGA%2FTATSayo8sHMyn5BSeQPd

# login
# {
#   "kind": "identitytoolkit#CreateAuthUriResponse",
#   "sessionId": "NHxl0YS3MMWvcCJQqSLWOeSVxvI"
# }


# confirm
# {
#   "kind": "identitytoolkit#GetOobConfirmationCodeResponse",
#   "email": "e.ma.y.aanand.2.64@gmail.com"
# }

# wordpress_logged_in_9a8088c047aa8a4d022063748baad4c8=e.ma.y.aanand.2.64%7C1714713210%7C0U94JnaTWMDEmqNPKbar0SyHKCQguznbY5R5thZNWhY%7C5f083a095176ef4179a5c4596bc1ed7a1c659d118e3e352b6797f0283fc5e2b8
# wordpress_logged_in_9a8088c047aa8a4d022063748baad4c8=k.en.sal.es.te%7C1714713536%7CQPVxBYm04y0rAilptjkiL83Ssy1140b14lYbVXOzgel%7Cec4e2e163600af71a67039c74d65c4dd9371bd85ffbbf0e43a2d259773b5da5a

# sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2024-04-19%2005%3A17%3A43%7C%7C%7Cep%3Dhttps%3A%2F%2Fchatgate.ai%2Flogin%3Fredirect_tohttps%253A%252F%252Fchatgate.ai%252F%26ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN%26ui_sd0%26apiKey%3DAIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20%26oobCode%3DUGAnCGZ8XAkKmK0jULZhEU14lMNfmvsmTxtrm1eojjkAAAGO9Mf3eQ%26mode%3DsignIn%26lang%3Den%7C%7C%7Crf%3Dhttps%3A%2F%2Fauth.chatgate.ai%2F; sbjs_first_add=fd%3D2024-04-19%2005%3A17%3A43%7C%7C%7Cep%3Dhttps%3A%2F%2Fchatgate.ai%2Flogin%3Fredirect_tohttps%253A%252F%252Fchatgate.ai%252F%26ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN%26ui_sd0%26apiKey%3DAIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20%26oobCode%3DUGAnCGZ8XAkKmK0jULZhEU14lMNfmvsmTxtrm1eojjkAAAGO9Mf3eQ%26mode%3DsignIn%26lang%3Den%7C%7C%7Crf%3Dhttps%3A%2F%2Fauth.chatgate.ai%2F; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; _gcl_au=1.1.683717577.1713503865; _ga=GA1.2.1647161728.1713503865; _gid=GA1.2.947416281.1713503865; _ga_TTDKRN293K=GS1.1.1713503864.1.0.1713503937.0.0.0; _ga_EBNTF2FDZV=GS1.1.1713503865.1.0.1713503937.0.0.0; sbjs_udata=vst%3D2%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F120.0.0.0%20YaBrowser%2F24.1.0.0%20Safari%2F537.36; sbjs_session=pgs%3D9%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fchatgate.ai%2F; tk_ai=8EA7Ed4U5v0mlCnbc%2FNNsmVL

# tk_ai = HmVD8Y5qhJGe816MPd046%2FCV
# session = 662215b2b4219

# sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2024-04-19%2007%3A19%3A55%7C%7C%7Cep%3Dhttps%3A%2F%2Fchatgate.ai%2Flogin%3Fredirect_tohttps%253A%252F%252Fchatgate.ai%252F%26ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN%26ui_sd0%26apiKey%3DAIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20%26oobCode%3Dyfekwcpd95vXjxZi_2SUsziWYLFWZRgfzWqRNBftDfwAAAGO9TjGJA%26mode%3DsignIn%26lang%3Den%7C%7C%7Crf%3Dhttps%3A%2F%2Fauth.chatgate.ai%2F; sbjs_first_add=fd%3D2024-04-19%2007%3A19%3A55%7C%7C%7Cep%3Dhttps%3A%2F%2Fchatgate.ai%2Flogin%3Fredirect_tohttps%253A%252F%252Fchatgate.ai%252F%26ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN%26ui_sd0%26apiKey%3DAIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20%26oobCode%3Dyfekwcpd95vXjxZi_2SUsziWYLFWZRgfzWqRNBftDfwAAAGO9TjGJA%26mode%3DsignIn%26lang%3Den%7C%7C%7Crf%3Dhttps%3A%2F%2Fauth.chatgate.ai%2F; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F120.0.0.0%20YaBrowser%2F24.1.0.0%20Safari%2F537.36; _gid=GA1.2.1820683679.1713511196; _gcl_au=1.1.804137524.1713511196; mwai_session_id=66221c744caad; sbjs_session=pgs%3D4%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fchatgate.ai%2Flogin%3Fredirect_tohttps%253A%252F%252Fchatgate.ai%252F%26ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN%26ui_sd0%26apiKey%3DAIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20%26oobCode%3Dzl3ZCrvvQx-1r8HFjdx1v6_jYtZ1cnvq8gnjFqPXOBMAAAGO9T8zrw%26mode%3DsignIn%26lang%3Den; _gat_gtag_UA_268460175_1=1; _ga_TTDKRN293K=GS1.1.1713509813.1.1.1713511570.0.0.0; _ga=GA1.1.323329798.1713511196; _ga_EBNTF2FDZV=GS1.1.1713509813.1.1.1713511571.0.0.0; tk_ai=OvLlDKP1FFgtW12nTyDkg4SA
