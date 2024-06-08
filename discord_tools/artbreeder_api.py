import base64
import io
import os.path
import random
import requests

from PIL import Image

import json

from discord_tools.upscaler import resize_image_if_small_or_big


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_mask_base64(image_path):
    # Открываем исходное изображение
    original_image = Image.open(image_path)
    original_width, original_height = original_image.size
    mask_width = 1024
    mask_height = 1024
    # Создаем изображение маски
    mask = Image.new('RGB', (mask_width, mask_height), color='black')

    # Вычисляем координаты для центрирования
    left = (mask_width - original_width) // 2
    top = (mask_height - original_height) // 2
    right = left + original_width
    bottom = top + original_height

    # Вставляем белую область в центре маски
    mask.paste((255, 255, 255), (left, top, right, bottom))

    # Кодируем маску в формат base64
    buffered = io.BytesIO()
    mask.save(buffered, format="PNG")
    encoded_mask = base64.b64encode(buffered.getvalue()).decode("utf-8")

    with open("mask.png", "wb") as file:
        file.write(buffered.getvalue())

    return encoded_mask


class ArtbreederModels:
    dreamshaper = "sd-1.5-dreamshaper-8"
    realistic = "sd-1.5-realistic"
    sdxl = "sdxl-1.0-lcm-base"


class ArtbreederAPI:
    def __init__(self, proxies=None, cookies=None):
        self.proxies = proxies
        self.cookies = cookies

    @staticmethod
    def save_image_url(image_url, output_path):
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.save(output_path, "PNG")
            return output_path
        return None
    def merge_images(self, reference_images, output_path, prompt="", negative_prompt="", seed=None, width=None, height=None, do_upres=True, do_upscale=False, enhance=True,
                    face_change=0.75, style_change=0.75, content_content=0.75):
        """
        reference_images:
                {
                    'data': image_to_base64("/content/image 2.png"),
                    'weight': 0.5,
                    'referenceType': 'content',
                },
                {
                    'data': image_to_base64("/content/image 1.png"),
                    'weight': 0.9,
                    'referenceType': 'content',
                },
            ]
        """
        
        if seed is None:
            seed = random.randint(1111111, 9999999)
        
        headers = {
            'accept': 'application/json',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://www.artbreeder.com',
            'priority': 'u=1, i',
            'referer': 'https://www.artbreeder.com/create/composer?from-google=true',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }
        
        json_data = {
            'job': {
                'name': 'sd-lightning',
                'data': {
                    'seed': seed,
                    'prompt': prompt,
                    'ip_adapter_scales': [
                        0.5,
                        0,
                        0,
                    ],
                    'guidance_scale': 1,
                    'width': width,
                    'height': height,
                    'reference_images': reference_images,
                    'num_inference_steps': 3,
                    'do_upres': do_upres,
                    'do_upscale': do_upscale,
                    'init_image': None,
                    'init_image_strength': 0.2,
                    'chaosScales': {
                        'face': face_change,
                        'style': style_change,
                        'content': content_content,
                    },
                    'return_binary': True,
                    'negative_prompt': negative_prompt,
                    'enhance': enhance,
                },
                'alias': 'composer-image',
            },
            'environment': None,
            'browserToken': 'ZuyyUztKaFXZXRC9vKeQ',
        }
        
        response = requests.post('https://www.artbreeder.com/api/realTimeJobs', cookies=None, headers=headers, json=json_data, proxies=self.proxies)

        with open(output_path, "wb") as file:
            file.write(response.content)

        return output_path

    def inpaint_image(self, image_path, output_path, prompt="", negative_prompt="bad anatomy, low quality",
                      guidance_scale=1.5, seed=None,
                      width=None, height=None,
                      strength=0.5, num_steps=10, model=ArtbreederModels.dreamshaper):
        resize_image_if_small_or_big(image_path, max_megapixels=1)

        if not width or not height:
            original_image = Image.open(image_path)
            width, height = original_image.size

        print(width, height)

        if seed is None:
            seed = random.randint(1111111, 9999999)
        if not os.path.exists(image_path):
            raise FileNotFoundError

        url = "https://www.artbreeder.com/api/realTimeJobs"

        # Формируем payload
        payload = {
            "browserToken": "q520YJUUHGxarkgU8P5S",
            "environment": None,
            "job": {
                "name": "sd-lcm",
                "data": {
                    "model_version": model,
                    "lcm_lora_scale": 1,
                    "guidance_scale": guidance_scale,
                    "strength": strength,
                    "init_image": image_to_base64(image_path),
                    "crop_init_image": True,
                    "height": height,
                    "width": width,
                    "negativePrompt": negative_prompt,
                    "num_steps": num_steps,
                    "prompt": prompt,
                    "prompts": [],
                    "seed": seed
                }
            }
        }

        # Преобразуем payload в JSON строку
        payload_json = json.dumps(payload)

        headers = {
            "authority": "www.artbreeder.com",
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.artbreeder.com",
            "referer": "https://www.artbreeder.com/create/prompter?fromCreate=1",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"YaBrowser\";v=\"24.4\", \"Yowser\";v=\"2.5\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36"
        }

        response = requests.post(url, data=payload_json, headers=headers, proxies=self.proxies)

        output_path = self.save_image_url(image_url=response.json()['url'], output_path=output_path)

        return output_path

    def outpaint_image(self, image_path, output_path, prompt="", guidance_scale=7.5, seed=None, width=None,
                       height=None):
        resize_image_if_small_or_big(image_path, max_megapixels=0.5)

        if not width or not height:
            original_image = Image.open(image_path)
            width, height = original_image.size
        print(width, height)

        if seed is None:
            seed = random.randint(1111111, 9999999)
        if not os.path.exists(image_path):
            raise FileNotFoundError

        url = "https://www.artbreeder.com/api/realTimeJobs"

        # image_base64 =

        payload = {
            "job": {
                "name": "kandinsky",
                "data": {
                    "prompt": prompt,
                    "kandinskyType": "inpaint",
                    "width": 1024,
                    "height": 1024,
                    "inpaint_image": image_to_base64(image_path),
                    "inpaint_mask": create_mask_base64(image_path),
                    "guidance_scale": guidance_scale,
                    "seed": seed

                }
            },
            "environment": None,
            "browserToken": "escZ1RfDYGp6BOGxwSAA"
        }

        headers = {
            "authority": "www.artbreeder.com",
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.artbreeder.com",
            "referer": "https://www.artbreeder.com/create/outpaint",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36"
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)
        print(response.text)

    def outpaint_image_v2(self, image_path, output_path, prompt=""):
        url = "https://www.artbreeder.com/api/outpainter/generate.json"

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        multipart_form_data = {
            'prompt': ('', prompt),
            'image': ('image.png', image_data, 'image/png')
        }

        headers = {
            "authority": "www.artbreeder.com",
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9",
            "origin": "https://www.artbreeder.com",
            "referer": "https://www.artbreeder.com/create/outpaint",
            "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"YaBrowser\";v=\"24.4\", \"Yowser\";v=\"2.5\"",
            "cookie": self.cookies,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36"
        }

        response = requests.post(url, files=multipart_form_data, headers=headers, proxies=self.proxies)

        print(response.text)

    def text_to_image(self, prompt, output_path, negative_prompt="bad anatomy, low quality", guidance_scale=1.5,
                      seed=None, width=1024,
                      height=1024, strength=1, num_steps=10, model=ArtbreederModels.dreamshaper):
        url = "https://www.artbreeder.com/api/realTimeJobs"

        if seed is None:
            seed = random.randint(1111111, 9999999)

        payload = {
            "job": {
                "name": "sd-lcm",
                "data": {
                    "model_version": model,
                    "lcm_lora_scale": 1,
                    "guidance_scale": guidance_scale,
                    "strength": strength,
                    "prompt": prompt,
                    "negativePrompt": negative_prompt,
                    "prompts": [],
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "num_steps": num_steps,
                    "crop_init_image": True
                }
            },
            "environment": None,
            "browserToken": "r1o60ahltK4K7yrDh162"
        }
        headers = {
            "accept": "application/json",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.artbreeder.com",
            "priority": "u=1, i",
            "referer": "https://www.artbreeder.com/create/prompter?fromCreate=1",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

        output_path = self.save_image_url(image_url=response.json()['url'], output_path=output_path)
        return output_path


if __name__ == '__main__':
    # try:
    #     # Декодирование изображения из base64 в бинарные данные
    #     image_data = base64.b64decode(input("base64"))
    #
    # # Запись бинарных данных изображения в файл
    # with open("TEST.png", "wb") as file:
    #     file.write(image_data)
    #
    #     print(f"Изображение успешно сохранено")
    # except Exception as e:
    #     print(f"Ошибка при сохранении изображения: {e}")
    # exit()

    file_path = r"C:\Users\as280\Downloads\test.png"

    api = ArtbreederAPI()

    # result = api.inpaint_image(file_path, prompt="black clouds", width=1024, height=1024, seed=1211111,
    #                            image_strength=0.85)
    # result = api.inpaint_image(file_path, prompt="anime style", strength=0.5, guidance_scale=2, num_steps=15, seed=1,
    #                            output_path="result.png")
    # api.create_account()
    result = api.outpaint_image(image_path=file_path, output_path="result.png", prompt="black clouds",seed=1)
    print(result)

