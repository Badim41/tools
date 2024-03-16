import os
import requests
import time

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
        url = "https://us-central1-describepicture.cloudfunctions.net/ask_gemini_pro_vision_model"

        payload = {
            "imageUrl": f"https://storage.googleapis.com/describe-picture-image/{self.file_name_gemini}",
            "prompt": f"{prompt} with markdown",
            "mimeType": "image/png"
        }

        headers = {
            "authority": "us-central1-describepicture.cloudfunctions.net",
            "accept": "*/*",
            "content-type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if response.status_code == 500:
            return True, "NSFW DETECTED"

        if self.testing:
            logger.logging("ANSWER:", response, response.text)
        result = response.json()['answer']
        if not result:
            logger.logging("RESULT IS EMPTY:", result)
            time.sleep(0.5)
            return self.get_answer(prompt)
        else:
            return False, result


def detect_bad_image(image_path, testing=False):
    describer = AiDescribePictureAPI(testing=testing)
    describer.upload(image_path)
    nswf, _ = describer.get_answer(".")  # Запрос неважен
    return nswf


def describe_image(image_path, prompt, testing=False):
    describer = AiDescribePictureAPI(testing=testing)
    describer.upload(image_path)
    nswf, answer = describer.get_answer(prompt)
    return nswf, answer