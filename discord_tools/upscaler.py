import io
import os
import requests
import time
from PIL import Image

from discord_tools.logs import Logs, Color

logger = Logs(warnings=True)


class FotorModes:
    upscaler = "upscaler"

    # extender = "extender"

    @staticmethod
    def get_mode(mode_key, upscale_factor=4):
        mode_key = mode_key.replace(" ", "_")
        modes_dict = {
            "upscaler": {"mode": "enhancement", "upscaleFactor": upscale_factor}
        }

        return modes_dict[mode_key.lower()]


class FotorAPI:
    def __init__(self, mode, upscale_factor: int, testing=False):
        self.key = None
        self.upload_url = None
        self.mode = mode
        self.mode_params = FotorModes.get_mode(mode, upscale_factor=upscale_factor)
        self.upscale_factor = upscale_factor
        self.testing = testing

    def change_mode(self):
        url = "https://www.fotor.com/api/image/sr/task/v2"

        payload = {
            "key": self.key,
            **self.mode_params
        }
        headers = {
            "x-app-id": "app-fotor-web"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if self.testing:
            logger.logging("CHANGE MODE:", response.text)

    def get_result_upscale(self):
        while True:
            url = "https://www.fotor.com/api/image/sr/result/v2"
            headers = {
                "accept": "application/json, text/plain, */*",
                "x-app-id": "app-fotor-web"
            }

            params = {
                "key": self.key
            }

            response = requests.get(url, headers=headers, params=params)

            # Проверка статуса ответа
            if response.status_code == 200:
                # Обработка успешного ответа

                if self.testing:
                    logger.logging("get result:", response.text)
                result_status = response.json()['data']['status']
                if not result_status:
                    time.sleep(1 * self.upscale_factor // 2)
                    continue
                return response.json()['data']['id']
            else:
                logger.logging("Ошибка:", response.status_code)
                return

    def upload_on_url(self, image_path):
        if self.testing:
            logger.logging("UPLOAD")

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "image/jpeg"
        }

        with open(image_path, 'rb') as file:
            file_content = file.read()

        response = requests.put(self.upload_url, headers=headers, data=file_content)

        if response.status_code == 200:
            if self.testing:
                logger.logging("End upload:", response.text)
        else:
            logger.logging("Ошибка:", response.status_code)

    def get_upload_url(self):
        url = "https://www.fotor.com/api/image/sr/upload/url/v2"

        querystring = {"mimeType": "jpg"}

        payload = ""
        headers = {
            "x-app-id": "app-fotor-web"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        if self.testing:
            logger.logging("get upload url:", response.text)

        self.upload_url = response.json()['data']['uploadUrl']
        self.key = response.json()['data']['key']


def save_image_png(image_url, image_path):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.save(image_path, "PNG")
            return image_path
    except Exception as e:
        logger.logging("Ошибка при конвертации изображения:", e)
        pass


class Upscale_Mode:
    quality_8K = "8K"
    quality_4K = "4K"
    quality_HD = "HD"


MAX_PIXELS = 8000


def upscale_image(image_path, upscale_factor=None, random_factor="", testing=False, only_url=False):
    def get_image_dimensions(file_path):
        with Image.open(file_path) as img:
            width, height = img.size
        x = int(width)
        y = int(height)
        return x, y

    if not random_factor:
        random_factor = os.path.basename(image_path)[:-4] + "_"

    if upscale_factor == Upscale_Mode.quality_8K:
        upscale_factor_val = float(
            (MAX_PIXELS * MAX_PIXELS / (
                        get_image_dimensions(image_path)[0] * get_image_dimensions(image_path)[1])) ** 0.5)
    elif upscale_factor == Upscale_Mode.quality_4K:
        upscale_factor_val = float(
            (4000 * 4000 / (get_image_dimensions(image_path)[0] * get_image_dimensions(image_path)[1])) ** 0.5)
    elif upscale_factor == Upscale_Mode.quality_HD:
        upscale_factor_val = float(
            (2048 * 2048 / (get_image_dimensions(image_path)[0] * get_image_dimensions(image_path)[1])) ** 0.5)
    elif upscale_factor is None:
        upscale_factor_val = float(
            (MAX_PIXELS * MAX_PIXELS / (
                        get_image_dimensions(image_path)[0] * get_image_dimensions(image_path)[1])) ** 0.5)
    else:
        logger.logging("Invalid upscale factor provided.")
        return None, None

    max_pixels_in_side = max(get_image_dimensions(image_path)[1] * upscale_factor_val,
                             get_image_dimensions(image_path)[0] * upscale_factor_val)
    if max_pixels_in_side > 10000:
        reduce_factor = max_pixels_in_side / 11000
        upscale_factor_val = float(upscale_factor_val / reduce_factor)

    upscale_factor_val = round(upscale_factor_val, 1)
    logger.logging(f"Upscale factor:", upscale_factor_val,
                   int(get_image_dimensions(image_path)[0] * upscale_factor_val),
                   int(get_image_dimensions(image_path)[1] * upscale_factor_val))

    fotor = FotorAPI(mode=FotorModes.upscaler, upscale_factor=upscale_factor_val, testing=testing)
    fotor.get_upload_url()
    fotor.upload_on_url(image_path)
    fotor.change_mode()
    result_url = f"https://u-static.fotor.com/images/text-to-image/result/{fotor.get_result_upscale()}.jpg"

    if only_url:
        result_path = ""
    else:
        result_path = save_image_png(result_url, random_factor + "upscaled.png")

    return result_path, result_url
