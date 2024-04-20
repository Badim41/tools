import requests
import time

class Temp_Email_API:
    def __init__(self, proxies=None):
        self.proxies = proxies
        response = requests.request("GET", "https://www.emailnator.com/", data="", headers={'cookie': cf_clearance}, proxies=self.proxies)
        self.xsrf_token, self.session_id = self.get_tokens(response)

    def get_tokens(self, response):
        print(response.text)
        cookies_dict = response.cookies.get_dict()
        print("TOKENS", cookies_dict)
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

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)
        self.xsrf_token, self.session_id = self.get_tokens(response)

        return response.json()['email'][0]

    @staticmethod
    def get_message(email, sender, xsrf_token, session_id, message_id=None, attempts=10, proxies=None):
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

                response = requests.request("POST", url, json=payload, headers=headers, proxies=proxies)

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
                time.sleep(3)
        raise Exception(f"Не получено сообщение от отправителя {sender}!")
