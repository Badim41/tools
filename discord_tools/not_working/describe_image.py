from datetime import datetime
import json
import os
import requests
from base64 import b64encode
from Crypto.Cipher import AES

from discord_tools.logs import Logs

logger = Logs(warnings=True)


class AiDescribePictureAPI():
    def __init__(self, testing):
        self.testing = testing
        self.url = None
        self.file_name_gemini = None

    def upload(self, image_path):
        if self.testing:
            logger.logging("UPLOAD")
        if not os.path.exists(image_path):
            raise Exception(f"Файл {image_path} не существует!")

        self.get_upload_url()

        headers = {
            "authority": "storage.googleapis.com",
            "accept": "*/*",
            "content-length": str(os.path.getsize(image_path)),
            "content-type": "image/png",
        }

        # Чтение изображения из файла
        with open(image_path, "rb") as file:
            image_data = file.read()

        response = requests.put(self.url, headers=headers, data=image_data)

        if self.testing:
            logger.logging(response, response.text)
            logger.logging("END UPLOAD")

    def get_upload_url(self):
        """
        :return:
        NSFW: False - безопасная картинка, True - опасная картинка
        Answer: ответ
        """
        import requests

        url = "https://us-central1-describepicture.cloudfunctions.net/generateSignedUrl"

        querystring = {"filename": "upscaled.png", "contentType": "image/png"}

        payload = ""
        headers = {
            "authority": "us-central1-describepicture.cloudfunctions.net",
            "accept": "*/*"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        if self.testing:
            logger.logging(response, response.text)

        self.url = response.json()['url']
        self.file_name_gemini = response.json()['fileName']

    def get_answer(self, prompt):

        # if response.status_code == 500:
        #     return False, "-"

        # if self.testing:
        #     logger.logging("ANSWER:", response, response.text)
        # result = response.json()['answer']
        # if not result:
        #     logger.logging("RESULT IS EMPTY:", result)
        #     time.sleep(0.5)
        #     return self.get_answer(prompt)
        # else:
        #     return False, result

        def encrypt_data(data, key):
            cipher = AES.new(key, AES.MODE_CBC)
            iv = cipher.iv
            padded_data = data + (16 - len(data) % 16) * chr(16 - len(data) % 16)
            encrypted_data = cipher.encrypt(padded_data.encode('utf-8'))
            return b64encode(encrypted_data).decode('utf-8'), b64encode(iv).decode('utf-8')

        def send_encrypted_request(url, data, key):
            # Шифруем данные
            encrypted_data, iv = encrypt_data(data, key)

            # Формируем тело запроса
            print(encrypted_data, iv)
            payload = {
                "encryptedData": encrypted_data,
                "iv": iv
            }

            # Отправляем POST-запрос на указанный URL
            response = requests.post(url, json=payload)

            return response.text

        # Пример использования
        url = "https://us-central1-describepicture.cloudfunctions.net/ask_gemini_pro_vision_model_new_public"
        data = json.dumps({
            "imageUrl": f"https://storage.googleapis.com/describe-picture-image/{self.file_name_gemini}",
            "prompt": f"{prompt} with markdown",
            "mimeType": "image/jpeg",
            "userId": "sess_2f8R11T6oKwTJl52N973YRwpUks",
            "date": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        })
        key = bytes.fromhex("8fb207b01e2e45d36cb26a1ae0a3b850ab1b86181110e7ddd5c27e54465c8dfd")

        result = send_encrypted_request(url, data, key)
        print(result)
        return None, None


def detect_bad_image(image_path, testing=False):
    try:
        describer = AiDescribePictureAPI(testing=testing)
        describer.upload(image_path)
        nswf, _ = describer.get_answer(".")  # Запрос неважен
        return nswf
    except:
        return None


def describe_image(image_path, prompt: str, testing=False):
    try:
        describer = AiDescribePictureAPI(testing=testing)
        describer.upload(image_path)
        nswf, answer = describer.get_answer(prompt)
        return nswf, answer
    except Exception as e:
        print(e)
        return None, "-"


def describe_image_multy_prompt(image_path, prompts: list, testing=False):
    describer = AiDescribePictureAPI(testing=testing)
    describer.upload(image_path)

    nswf_all = False
    answers = []
    for prompt in prompts:
        nswf, answer = describer.get_answer(prompt)
        answers.append(answer)
        if nswf:
            nswf_all = True

    return nswf_all, answers

describe_image(r"C:\Users\as280\Downloads\temp.png", "что это?")