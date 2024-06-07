import io
import os
import requests
import time
from PIL import Image

from discord_tools.logs import Logs, Color
from urllib.parse import urlparse, parse_qs
from urllib.parse import quote

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
    def __init__(self, mode, upscale_factor=None, testing=False, proxies=None, cookies=None):
        self.key = None
        self.upload_url = None
        self.mode = mode
        self.mode_params = FotorModes.get_mode(mode, upscale_factor=upscale_factor)
        self.upscale_factor = upscale_factor
        self.testing = testing
        self.proxies = proxies
        self.cookies = cookies

    def change_mode(self):
        url = "https://www.fotor.com/api/image/sr/task/v2"

        payload = {
            "key": self.key,
            **self.mode_params
        }
        headers = {
            "x-app-id": "app-fotor-web"
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

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

            response = requests.get(url, headers=headers, params=params, proxies=self.proxies)

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

    def upload_on_url_upscale(self, image_path):
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

    def get_upload_url_upscale(self):
        url = "https://www.fotor.com/api/image/sr/upload/url/v2"

        querystring = {"mimeType": "jpg"}

        payload = ""
        headers = {
            "x-app-id": "app-fotor-web"
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring, proxies=self.proxies)

        if self.testing:
            logger.logging("get upload url:", response.text)

        self.upload_url = response.json()['data']['uploadUrl']
        self.key = response.json()['data']['key']

    def get_result_background(self, task_id):
        while True:
            url = f"https://www.fotor.com/api/app/cutout/result/{task_id}"

            payload = ""
            response = requests.request("GET", url, data=payload)
            result_status = response.json()['data']['status']
            print(result_status, response.text)
            if not result_status:
                time.sleep(5)
                continue
            else:
                break
        return response.json()['data']['imgUrl']

    def send_background_request(self, image_key):
        url = "https://www.fotor.com/api/app/cutout/request"

        querystring = {"action": "auto", "imageKey": image_key,
                       "returnForm": "png"}

        payload = {}
        headers = {
            "authority": "www.fotor.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.fotor.com",
            "referer": "https://www.fotor.com/ru/features/background-remover/upload",
            "x-app-id": "app-fotor-web"
        }

        response = requests.request("POST", url, headers=headers, json=payload, params=querystring, proxies=self.proxies)

        print(response.text)
        return response.json()['data']['taskId']

    def upload_on_url_background(self, image_path, expires, oss_access_key_id, signature, upload_key):
        url = f'https://fotor-com-cutout.oss-accelerate.aliyuncs.com/{upload_key}'
        querystring = {"Expires": expires, "OSSAccessKeyId": oss_access_key_id,
                       "Signature": signature}

        # print("upload url", url)

        headers = {
            "Content-Type": "image/png",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru,en;q=0.9",
            "Connection": "keep-alive",
            "Origin": "https://www.fotor.com",
            "Referer": "https://www.fotor.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="122", "Not(A: Brand";v="24", "YaBrowser";v="24.4", "Yowser";v="2.5"',
            "sec-ch-ua-mobile": "?0"
        }
        with open(image_path, 'rb') as file_content:
            response = requests.request("PUT", url, data=file_content, headers=headers, params=querystring)

        print(response.text, response.status_code, querystring)

    def get_upload_url_remove_background(self):
        url = "https://www.fotor.com/api/app/cutout/v2/upload-img"

        querystring = {"mimeType": "image/png", "num": "1"}

        payload = ""
        response = requests.request("GET", url, data=payload, params=querystring, proxies=self.proxies)

        data = response.json()['data'][0]

        parsed_url = urlparse(data['uploadUrl'])

        # Извлечение значений переменных из запроса
        query_params = parse_qs(parsed_url.query)

        # Получение значений переменных
        expires = query_params.get('Expires', [''])[0]
        oss_access_key_id = query_params.get('OSSAccessKeyId', [''])[0]
        signature = query_params.get('Signature', [''])[0]

        base_url = "{url.scheme}://{url.netloc}{url.path}".format(url=parsed_url)

        # print("Базовая часть URL без параметров:", base_url)

        print(response.text)

        self.upload_url = base_url

        upload_key = data['uploadKey']

        print("expires, oss_access_key_id, signature, upload_key", expires, oss_access_key_id, signature, upload_key)

        return expires, oss_access_key_id, signature, upload_key


def save_image_png(image_url, image_path, chunk_size=1024):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
            print("Изображение успешно сохранено по пути:", image_path)
            return image_path
        else:
            print("Ошибка при загрузке изображения. Код состояния:", response.status_code)
    except BaseException as e:
        print("Ошибка при загрузке изображения:", e)


class Upscale_Mode:
    quality_8K = "8K"
    quality_4K = "4K"
    quality_HD = "HD"


MAX_PIXELS = 8000


def upscale_image(image_path, upscale_factor=None, random_factor="", testing=False, only_url=False, proxies=None):
    print(image_path)
    def get_image_dimensions(file_path):
        with Image.open(file_path) as img:
            width, height = img.size
        x = int(width)
        y = int(height)
        return x, y

    resize_image_if_small_or_big(image_path)

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

    fotor = FotorAPI(mode=FotorModes.upscaler, upscale_factor=upscale_factor_val, testing=testing, proxies=proxies)
    fotor.get_upload_url_upscale()
    fotor.upload_on_url_upscale(image_path)
    fotor.change_mode()
    result_url = f"https://u-static.fotor.com/images/text-to-image/result/{fotor.get_result_upscale()}.jpg"

    if only_url:
        result_path = ""
    else:
        result_path = save_image_png(result_url, random_factor + "upscaled.png")

    return result_path, result_url


def remove_background(image_path, random_factor="", testing=False, only_url=False, proxies=None):
    resize_image_if_small_or_big(image_path)
    fotor = FotorAPI(mode=FotorModes.upscaler, testing=testing, proxies=proxies)
    expires, oss_access_key_id, signature, upload_key = fotor.get_upload_url_remove_background()
    # exit()
    fotor.upload_on_url_background(image_path, expires, oss_access_key_id, signature, upload_key)
    time.sleep(3)
    # input("UPLOAD?")
    # exit()
    task_id = fotor.send_background_request(upload_key)
    # exit()
    result_url = fotor.get_result_background(task_id)

    if only_url:
        return "", result_url
    else:
        result_path = save_image_png(result_url, random_factor + "remove_background.png")

    return result_path, result_url

def resize_image_if_small_or_big(image_path, min_megapixels=0.5, max_megapixels=2, return_pixels=False):
    try:
        # Открываем изображение с помощью Pillow
        with Image.open(image_path) as img:
            # Получаем размеры изображения
            width, height = img.size
            # Вычисляем количество пикселей
            total_pixels = width * height
            # Количество пикселей в одном мегапикселе
            megapixel_pixels = 1000000

            # Проверяем, если количество пикселей меньше минимального значения
            if total_pixels < min_megapixels * megapixel_pixels:
                # Вычисляем коэффициент масштабирования для увеличения
                scale_factor = (min_megapixels * megapixel_pixels / total_pixels) ** 0.5
                # Вычисляем новые размеры изображения, сохраняя пропорции
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                if return_pixels:
                    return new_width, new_height
                
                # Масштабируем изображение
                resized_img = img.resize((new_width, new_height))
                # Сохраняем масштабированное изображение
                resized_img.save(image_path)
                print(f"Изображение успешно увеличено до {min_megapixels} мегапикселей.")
            # Проверяем, если количество пикселей больше максимального значения
            elif total_pixels > max_megapixels * megapixel_pixels:
                # Вычисляем коэффициент масштабирования для уменьшения
                scale_factor = (max_megapixels * megapixel_pixels / total_pixels) ** 0.5
                # Вычисляем новые размеры изображения, сохраняя пропорции
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)

                if return_pixels:
                    return new_width, new_height
                
                # Масштабируем изображение
                resized_img = img.resize((new_width, new_height))
                # Сохраняем масштабированное изображение
                resized_img.save(image_path)
                print(f"Изображение успешно уменьшено до {max_megapixels} мегапикселей.")
            elif return_pixels:
                return new_width, new_height
            else:                
                print("Изображение уже находится в допустимом диапазоне.")
    except Exception as e:
        print("Ошибка при масштабировании изображения:", e)


if __name__ == '__main__':
    image_path = input("File:")
    result_path, result_url = remove_background(image_path)
    print(result_path, result_url)

