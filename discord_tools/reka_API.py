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
    api = Reka_API(app_session="eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwidWF0IjoxNzE1NzQ4NzIyLCJpYXQiOjE3MTU3NDg3MDYsImV4cCI6MTcxNjAwNzkyMn0..B9LsRo7KlN9xzUQ5.7xIbei4o5lHxhdix_ul_B1QJqGf7f87FMpaz6zO1KIeLuUuK7Mwk8Ka3fphvenJEvI4pzgmFWkzeKX61a8wo7EKcV7nTD7On5MFfyJQZuUmQWkAasVctH9y1lkfeZuYlwGIwgt274WBzHqFNXM6dEI3eCyAznusTOkXJu4MxO2Ij7YObQgd_Fodcc_bPxzeDjMLNLeeLErlu4lUpkTHTnck6bCYeWHs2YlCJbuodcJrMVNvQKf9QKTy7I0zHwdYZVPoT6WUxcI_Lr2VpPjYNgW83IekdSngnEv5NatFte87Cd5RImiV71JDL5oMLETFJzl7TT0Shh5WtC31elmOcTeAZ50obVgK8UV1faUj2kWi1bMYhXtvmEv7cl-0P8Mz4KVRgofRNQbozBnB3h8Woq6Sz7Rp5DvMRtg5BDCkFbKiy1z0qaIhoNx_fEGqY2r4dEpw6JnE5Z4-pGk5YPOBYq97uJkHNNAiqx71A2BdcvVpk647qQVq8Bhyy1GWmzKIp70Twj2zE0fy43US2gjiDB9oxH6urWmpYFKKOzDsZBA_QW7XxjyQ2J-2aNEkX0h2es5Sn5BR84IPLTqw6o3YbD2fLwzVlL_4EVnC4AKyuAETvEaqM2bpaTF3CfDIUMM_BJqA2wSXLYZSjhlq0xEUgV0aBRj9uw4jfl_vwWfZGaEIVMzK31yvPGlHnpbBBXHo9dZI1gYdjql9atqgqMks83aD-KziGDLj2EmY1Nzm5enad4iXlILxxrEHOKXjflweF2hzlGlArD9Ov72QMkc7tIi4QDQ4__JWw3v4rOhJV8v0sQZaPVrEdq5VN6mO6L6-D7e51jTFp3Q0kJjdPDcTv5SG1a8-slNJLmAauiUgARSqvD-tindg6D0CJeOPXPdUeE3q4_h-_yz5D2ek49NXULunYvhy6qzDq-epA9JyJiiDmb-HF9etWdwlKvA77E6ALAo5__GnNpZKKC6mBxhH-Jo-l2NS8DRFoHDZDftYvmOJvrKtSDj4kzmoKkrsKYZ0VtbndF8aYUrPDccA6TTOxID_49vI2x56L6JXGLz0890owEm58Ck5Cz2zrkJ4Z0BqScC-BphD99iWsCmUOGgx4zgMGdne4XWNJBs7_4kUrmx50WsiLHEhCYX7DRz0Or8lLRbkZgHuveFgaGaIJOZj30p_wyfZQD8o9XxAI-D8tZ0l-hWV5Qb8xkCJEMtBB-fi_ETMNusQMUXkzueKW8_XjlvM6DWFbiwfR44JVFxm9SdLOzeqU567izyPQBTbZZVFZc9ZUeCAty5_7U5pbQiz9NPXWz7XDlNALT4lACV2ICwa7-SPjguMJWrkwK4TNuPUhbcatf3zqE7YTbVKkdpS3iJTNwtvcYuiQKkPyhFaIcEPZHEkqDIaeI9xfeOqu7zY6KPRvglUaefarPEjwQquURVUSJ5dkr7nO_y2LsDw-EMXAE_KTdcRyG7A51eFuWaNoA5vNytoPERQOWl_lIrWVvzX-QQcQcDFwLZiYlpkbEDDAU_O29PkbcZAxesr1l6Xh_otfiPUo6F6H4BzWvsp5f0Nhswo2rqbYQ-tThYLgyg9X9IVz7XOXbRe3ecENKQtJ3Kk-1_Sfw7hqzOvjvZ2z6cz1XSHluBOiGgt4l1MaTh96ap81pxL-bgLITpk1jD5W60wjrJApSrR-Q1HUmmBKjUXAVDiBcQeKtqGVEqux0NbgMHUmpiV9ICpACnQxk1tkdReeXBuR83nTa1pyO_a_Y-Msfo1dJclGCL87wDLJU-BQuLOhMa1gyjt6VbCldIhy3rcFJ9Q9rIIgj21aCwX4r_IJfXabYixkpho64nhWj6ca7YNE9hrPNhLmOmi96xFuSXJ6RoiMCaLjVxGANNYJ7c1SzplR7bz-uyInn21In__Dks3qhsKBpnX54TR0APJj3LtNQS93QJ_5M4Txe7OntvncjZiVawpgulUKfyLDhu7cX2ENxPGFj_0-MUqTNJ-uQYFoPr_MEEKsSGD6IEz_VMvj_mmvsGZTf82JSLWh5C0bJkc6_6lHrEYvjD5fJ8PxADZGH3I7I6Ob5LMh1MT7stvperDBWAagF6ZDgLRnRJSoYmhaqZh4ynkG44hfV8DeZjeVxUUzq8qiAsRf7qKyWvxih0ecmvtxSu0_Ln-LfVfrdcDQsHsMADg1ET3ZsBMDFVIePvFOSw2Fs2huyLlGVFUEOzUY7yUasptQpOHAX8a2ahoCZbrB86YKrkPe_hUxezgqzKQKcQznV1gIBnrYWp2bkDZK6PTSVymKajDUmJW-MgbIV__HnmC4SEAwUtWmcMaYQS2arbuFKmsTi1h2wbS956T-8rMhCBwxGUFtaW-_JaXUd0yrh-fINPOtgY_JUk5RBvKFfHJq4nG3uSNO3r_f4DtrmJ1fhh6eFkrnMT8_4JurTV2PiU-AHagZGT9CUEhcOEW5u4GilK58K1CbhfTyEbDyYiVgY06KphSD1uya6R-4jYeYNSre7HGsxGC58jrN8C_kW885HwFAEa5r-5s1nNvRkgNGfXq29E9pMAxv0jv_e1TU8LnhZBzUvRYoaWqNSPlW8A-L5hK68ADfdlxvDftKQvIoAGUCd5izor2Taux0iLsjtuSs7xyZq6bhTFvjDdG1RvhzDrrnlC-ARyInGNngTzrTDhPLbwhb3X9S-HvW0VWI5LnZv1AEzaNRu4d0VsMrSDAQjB5wX4BVB3iRzaXaqcFC_oaOsCTOphFc85kEXY6iILpca7du6wBQxiVsmUp62A0Ocs1HxzzhFnLEbdlZ-9d2UtGEudSTtDyCiWcK57qmzJ71a4R31Xo13MHcL-t68bePhu67F50jq_qmqZkx_-ywhNtUuZnCOa-G-gU8hEEGOys7hdbxe1FJ6iqS6At2FN-c0DZZl7RM3V_7PgDLmHk4B_gvXy98IsZoQz_kfDf0T9dk5VrRJUFrHU0g2NRQj83rmyivGz1YpRxlDMbS5D_PdMxT03jjdlIxS1EBy3esMWc9mGMVm1_YQGBOTvzashLjRoBlrjUO5lIq2cQ2LCPWknFlX_1TzUE4IL1DdoeQudQQyw39F1SUfcwsPKEoSdq_E1Yg5-LQn4thRi4JLQcs-2JNfbs8J3YcoLk0c2vGHTIQuD-7wOqiz2EyT-sqZYlTgH_z8fiW7yHWR5yttoGj_nY2TvJLZfEiJ9REPslg6ek4epOGuqmVZPVX_9b9A8fwbTDVY9K027Kossv6JpC_dqtTcQDT_aCyjLM2sJ-RpnQHoN12VQWIECRKHTjA9HDm5WVFznAJWo5exMR7TumqbNcmDiXigYeQjCB1b7PhyITgmtX7k7EHFU71Pb4.cWAE9C1HVpV67lox0x0ReA")
    print("access key", api.auth_key)

    answer = api.generate(messages=[{"role": "user", "content": "Какая игра на видео?"}],
                          file_path=r"C:\Users\as280\Pictures\mine-imator\falling.mp4", media_type=MediaType.video)

    print(answer)
