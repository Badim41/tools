import re
import requests
import time

from discord_tools.astica_API import Astica_Free_API_key


class Temp_Email_API:
    def __init__(self):
        response = requests.request("GET", "https://www.emailnator.com/", data="", headers={})
        self.xsrf_token, self.session_id = self.get_tokens(response)

    def get_tokens(self, response):
        cookies_dict = response.cookies.get_dict()
        print("Updated cookie")
        return cookies_dict['XSRF-TOKEN'], cookies_dict['gmailnator_session']

    def get_email(self):
        print("get gmail")
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

    def get_message(self, email, sender, message_id=None, attempts=50):
        for i in range(attempts):
            try:
                print("get messages")
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
                    "cookie": f"XSRF-TOKEN={self.xsrf_token}; gmailnator_session={self.session_id}",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
                    "x-requested-with": "XMLHttpRequest",
                    "x-xsrf-token": self.xsrf_token.replace("%3D", "=")
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
                    return self.get_message(email=email, message_id=message_ids[-1], sender=sender)
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

class ChatGPT_4_Site:
    def __init__(self):
        self.apiKey = self.get_api_key()

    def get_api_key(self):
        import requests

        url = "https://chatgate.ai/login"

        querystring = {"redirect_to": "https://chatgate.ai/"}

        payload = ""
        headers = {
            "authority": "chatgate.ai",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9",
            "cache-control": "max-age=0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        # print(response.text)

        return Astica_Free_API_key.find_key(response.text, r'"apiKey"\s*:\s*"([^"]+)"')

    def login(self, email):
        import requests

        url = "https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri"

        querystring = {"key": self.apiKey}

        payload = {
            "identifier": email,
            "continueUri": "https://chatgate.ai/login?redirect_tohttps%3A%2F%2Fchatgate.ai%2F"
        }
        headers = {
            "origin": "https://chatgate.ai",
            "sec-ch-ua-mobile": "?0"
        }

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

        print(response.text)

        self.login_confirm(email)
    def login_confirm(self, email):
        url = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"

        querystring = {"key": self.apiKey}

        payload = {
            "requestType": "EMAIL_SIGNIN",
            "email": email,
            "continueUrl": "https://chatgate.ai/login?redirect_tohttps%3A%2F%2Fchatgate.ai%2F&ui_sidVipRNOEgz6nEZne9Z6skpwBzcoiQfXhN&ui_sd0",
            "canHandleCodeInApp": True
        }

        headers = {"origin": "https://chatgate.ai"}

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

        print(response.text)

def extract_link_from_html(html_string):
    # Используем регулярное выражение для поиска ссылки внутри тега <a>
    match = re.search(r'href=[\'"]?([^\'" >]+)', html_string)
    if match:
        # Возвращаем найденную ссылку
        return match.group(1)

# exit()
chat_gpt_4 = ChatGPT_4_Site()
print(chat_gpt_4.apiKey)

api = Temp_Email_API()
gmail_adress = api.get_email()
print(gmail_adress)

chat_gpt_4.login(gmail_adress)

result = api.get_message(email=gmail_adress, sender="noreply@auth.chatgate.ai")
print("RESULT", result)

print(correct_link(result))
oob_code = re.search(r'oobCode=([^&]+)', result).group(1)
print(oob_code)
continue_url_match = re.search(r'continueUrl=([^&]+)', result).group(1)
print(continue_url_match)
# # eneter
# eyJpdiI6IlY5blBCRWdncXpoOG9HTnlRRHlNcEE9PSIsInZhbHVlIjoiTVdJQko4dXlMNXpzbDNFYmpNQU5qMGZuRFk5T3hZaGk3M0szN0RJbXh5V1BwL0ZPeGs0RStNQXB3NEYxMi9aUjdMZ2FwcTd2d3A1MTdqMjIwbFVDdlVvRURkQmxINDZwRVpPemZ4TjZCYkxwRmVxeE0wSGw0cmwwaTVjRHZabEwiLCJtYWMiOiJkYjdkODQyMzc4MTgwNTBkNWM0ZDI3NTZkMWJlNmU4ZGM1YjllM2I0M2FiNDM5MGI5NDk4NDBlYTdmZjE3M2YyIiwidGFnIjoiIn0
# eyJpdiI6InZ2UktTblBnTWs3Yk45dDJLYWtuZEE9PSIsInZhbHVlIjoicndlWjA1TGF0a2RnZ2E2WGF4Ujl0QjVBMU90V3llSllReFlLZk1BY05BaUVvNHR4eWRPY1N4UkhiMGtLendWWEY0Nm1ndStsaTdUOGYwWnQ1VHNFYVkwZEFPK1hxWGV4K1BnZWJ2MHBRbjFYOGwrNzhMU0E5Z0JuWERiOGVqbjUiLCJtYWMiOiI4ZTMwMzg2NWU2MjQ5MjQ0MTViZmE5MjdiNWZjMzFiZDk5YjlkZGVlYzc5M2I4M2JkMDgyMjI3OWU4MjZkZWUyIiwidGFnIjoiIn0
#
# # generate
# eyJpdiI6ImNOZlcwMlk4WHREUjRsU2o2T21VS3c9PSIsInZhbHVlIjoidVppUnBPd1o3RXg0T0JxUjZwbnlpaWpzUFBIc09XVENadUNWa2tzUzdMN3c4RmNCU3NZUFJSaURKc3p0UE1EWDUvM2x3MjJkeDdpUjc4MEw3OVRwcTNxNEpXQk1HQU43Y2UxNGpQY01DTmswbXluSURyVkk5dlNORTR1aERTVzkiLCJtYWMiOiI4ZjI0MGQxMmZmNjVhZTkyMjU2MzQyMmJhYTdiMzkyNDY1OWViOTI2YzVkODdjOGFkOGFjZjEwNmJmMjFjYjYxIiwidGFnIjoiIn0
# eyJpdiI6IlMyeUxnUUZ1T1JrWTdvWDFaUzZTY0E9PSIsInZhbHVlIjoiZ3RHWnFJclk2L2Z5WWNwME9tWGJYQWtzbFpJZ1ZjYURzRElyTWNFVGdCc3NRLzBTNjllbXk0OXdOWE0yQ3dwS3RHd0hYbU1jdG5XQlRuU3Z1anpETzhRVkpVZmZNaGlqRTlnNXozN3JBVDBLOEgrUFBoemxEUGdYK2hIQzRlc28iLCJtYWMiOiI0N2IzMzcwZDg4ZGRiZThlMjU5NzFkZGM0YzNjOTk4OWI1OGU2MmNlOGQ4YmQ5MjRiYzE3MmQ2NjJjMWFkM2QxIiwidGFnIjoiIn0
#
# # message list
# eyJpdiI6IjlPTkRrY0o2bkJCYXhIRVZEUWJlMmc9PSIsInZhbHVlIjoiQmhxNkpaT1djVVJpQis5UmtXaWtoSStQSTNzdnJ2dFpveDJLM21lYUhYV2RiS295RlBJUGlQSTVoUThwTXpRZUl3bS83Nm9DRHlTWDNwQ0d3azlYaFhRL2Y4NVcwdVJFZStpMFBkRFJUMjVxTVAzRXducWhIc1MrQ1dpZWxMaUEiLCJtYWMiOiJmMTVkNmY2YmQ3ODEzNGU0NTcxNzhmYzM5YzBlOTEzYzVmMmFkMmQxODA0NTcwZmRkNDlhNjZjYmFkZTAxZjI4IiwidGFnIjoiIn0
# eyJpdiI6ImRNZFE1enp1U3dKbUlpZ2RwaFhrWmc9PSIsInZhbHVlIjoienh2SE9KVGR5d3MvNVZqaVBtV1l2TGY4OGNHV1JCeW8vZzJzRTlEY3U0bkFNQXd5K0FpNjF6MWs3b29PWnFNMytBdU0xT3JONlFVQ2lVZnliYTF3Q2Z6OTY2VWlPc0NyM3pRSEd5REdWL2JBWUNnU0R0UGxwZzdiZzdZMjJPRnQiLCJtYWMiOiIxZWUzOGZjZjZhYmViY2ZhMjBkNWI5ODU0ZGU4MjA3NmMwMTUyNmEwZTVlOTI1NjU3NTU3MzVhMjYwOGYzOGFjIiwidGFnIjoiIn0
#
# # list 2
# eyJpdiI6IjVjVlNoSWF6b1Axa2dqdHc3SjF1QlE9PSIsInZhbHVlIjoiZGJQRHkwTUlGSTY1Q1I5SDU2NVA5YzUvZ3hFYWUxODBSR0ErNHc3djdFZkluRUtpS1hta1FINVNPTEVWUXd1bExFRXo5N2J1RUZjc0JaQk1KS1ZweGszT0VIVW5LQjlDVTZpV3RpU3VuN21wUEFFNkZ6aVpySWNQVTV0d1FWRDciLCJtYWMiOiJmNDAwNzMyM2FhYWQ1OTA0MTk2MzkxNWVmZjFkNGEwZDUxMjVhZDc1MzZhN2UyNjFiOWMwNTJjNDE4YzE3YjNiIiwidGFnIjoiIn0
# eyJpdiI6IldBK2ZBSDNBa2dOL3Q5MUsrTVRUcFE9PSIsInZhbHVlIjoiTzNUWVdBNDlZZFd5RlNmcEFEM1RUN0h4eVZIaDNia0tkem14SFpqTW9nY2tTUEozbVJUUmQ2SFZFL3Rlak5wcS9SajFEalJqQStOSkNZTEdGUEEzWFdYV0JKYVB4cEpET1Z1dnliaC9lSjk3U1AzSG85Y3NuVE5IMzhvamo1ekciLCJtYWMiOiJiOWFjMzVlYjA1NThlYWYwMTQ2MDk3ZGIwYWZmMDFlYjk5MWMyNjM2ODQ5ZjE4NmU3NmJmZjg3NzkyOTc0ZjdlIiwidGFnIjoiIn0


# https://auth.chatgate.ai/__/auth/action?apiKey=AIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20&mode=signIn&oobCode=RVQNjsMpPHiZs6hcOExIVosOJfBvoH4EE23MFBC6l-4AAAGO8FO94Q&continueUrl=https://chatgate.ai/login?redirect_to%3Dhttps%253A%252F%252Fchatgate.ai%252F%26ui_sid%3DikJUJfS96kDI9IkZgNBJnDBwFpKnTy3n%26ui_sd%3D0&lang=en
# https://auth.chatgate.ai/__/auth/action?apiKey=AIzaSyB8QIdDarSEZTwPWF-dauPL6-RHAMYmy20&amp;mode=signIn&amp;oobCode=RVQNjsMpPHiZs6hcOExIVosOJfBvoH4EE23MFBC6l-4AAAGO8FO94Q&amp;continueUrl=https://chatgate.ai/login?redirect_to%3Dhttps%253A%252F%252Fchatgate.ai%252F%26ui_sid%3DikJUJfS96kDI9IkZgNBJnDBwFpKnTy3n%26ui_sd%3D0&amp;lang=en
