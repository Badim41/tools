import asyncio
import base64
import io
import json
import os
import random
import requests
import time
import traceback
import zipfile
import urllib
import uuid
import re
import shutil
from bs4 import BeautifulSoup

from PIL import Image

from discord_tools.character_ai_chat import Character_AI, char_id_images
from discord_tools.logs import Logs, Color
from discord_tools.upscaler import upscale_image
from discord_tools.describe_image import describe_image, detect_bad_image

logger = Logs(warnings=True)

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

RESULT_PATH = 'images'


async def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            # logger.logging(f"Ширина изображения: {width}px, Высота изображения: {height}px")
            return width, height
    except Exception as e:
        logger.logging(f"Ошибка при получении размера изображения: {e}")
        return None


class GenerateImages:
    def __init__(self, secret_keys_kandinsky=None, apis_kandinsky=None, char_tokens=None, bing_cookies=None):
        if not os.path.exists(RESULT_PATH):
            os.mkdir(RESULT_PATH)

        if isinstance(secret_keys_kandinsky, list):
            self.secret_keys_kandinsky = secret_keys_kandinsky
        elif isinstance(secret_keys_kandinsky, str):
            self.secret_keys_kandinsky = [secret_keys_kandinsky]
        else:
            self.secret_keys_kandinsky = secret_keys_kandinsky

        if isinstance(apis_kandinsky, list):
            self.apis_kandinsky = apis_kandinsky
        elif isinstance(apis_kandinsky, str):
            self.apis_kandinsky = [apis_kandinsky]
        else:
            self.apis_kandinsky = apis_kandinsky

        if isinstance(char_tokens, list):
            self.char_tokens = char_tokens
        elif isinstance(char_tokens, str):
            self.char_tokens = [char_tokens]
        else:
            self.char_tokens = char_tokens

        if isinstance(bing_cookies, list):
            self.bing_cookies = bing_cookies
        elif isinstance(bing_cookies, str):
            self.bing_cookies = [bing_cookies]
        else:
            self.bing_cookies = bing_cookies

        self.blocked_requests = []
        self.queue = 0

    # [Kandinsky_API, Polinations_API, CharacterAI_API, Bing_API]
    async def generate_image_grid(self, model_class, image_name, prompt, row_prompt, delete_temp=True, zip_name=None):
        def create_black_image(width, height):
            return Image.new('RGB', (width, height), (0, 0, 0))

        model_instance = model_class(self)

        if model_instance.suffix not in ["r2", "r3"]:
            prompt = row_prompt
            print(f"Changed prompt for {model_instance.__class__.__name__}: {row_prompt}")

        image_path = f"{RESULT_PATH}/{image_name}_{model_instance.suffix}_{self.queue}"

        try:
            if model_instance.return_images == 1:
                tasks = [asyncio.to_thread(model_instance.generate, prompt, image_path + f"_{i}.png") for i in range(4)]
                image_paths = await asyncio.wait_for(asyncio.gather(*tasks), timeout=60)
            elif model_instance.return_images == 4:
                image_paths = await asyncio.wait_for(asyncio.to_thread(model_instance.generate, prompt, image_path), timeout=60)
            else:
                raise Exception(f"Неправильное количество возвращаемых изображений:{model_instance.return_images}")
        except TimeoutError:
            logger.logging(f"Image timeout {model_instance.__class__.__name__}")

        if not image_paths:
            return

        images = [Image.open(path) for path in image_paths]

        image_width, image_height = Image.open(image_paths[0]).size
        black_image = create_black_image(image_width, image_height)

        for i in range(4):
            images.append(black_image)

        grid_width = 2 * image_width
        grid_height = 2 * image_height
        grid_image = Image.new('RGB', (grid_width, grid_height))

        for i in range(2):
            for j in range(2):
                index = i * 2 + j
                grid_image.paste(images[index], (j * image_width, i * image_height))

        final_path = image_paths[0].replace(".png", "FINAL.png")
        grid_image.save(final_path)

        if zip_name:
            for result in image_paths:
                with zipfile.ZipFile(zip_name, "a") as zipf:
                    zipf.write(result)

        if delete_temp:
            for image_path in image_paths:
                os.remove(image_path)

        return final_path

    async def generate(self, prompt, user_id=0, kandinsky=True, polinations=True, character_ai=True,
                       bing_image_generator=True,
                       zip_name=None, delete_temp=True, bing_fast=False, row_prompt=None):
        self.queue += 1

        if not row_prompt:
            row_prompt = prompt

        if zip_name:
            text_name = f"prompt_{user_id}.txt"
            with zipfile.ZipFile(zip_name, "w") as zipf:
                with open(text_name, "w") as text_file:
                    text_file.write(prompt)
                zipf.write(text_name)
                os.remove(text_name)

        models = []
        if kandinsky:
            models.append(Kandinsky_API)
        if polinations:
            models.append(Polinations_API)
        if character_ai:
            models.append(CharacterAI_API)
        if bing_image_generator:
            models.append(Bing_API)

        functions = [self.generate_image_grid(model_class=model, image_name=user_id, prompt=prompt, zip_name=zip_name,
                                              delete_temp=delete_temp, row_prompt=row_prompt) for model in models]

        results = [result for result in await asyncio.gather(*functions) if result and os.path.exists(result)]

        if zip_name:
            with zipfile.ZipFile(zip_name, "a") as zipf:
                for result in results:
                    zipf.write(result)

        return results


class Polinations_API:
    def __init__(self, generator: GenerateImages):
        self.generator = generator
        self.queue = generator.queue
        self.suffix = "r3"
        self.return_images = 1

    def save_image(self, image_url, image_path):
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.save(image_path, "PNG")

    @staticmethod
    def get_image_size(image_path):
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height

    def generate(self, prompt, image_path, seed=random.randint(1, 9999999)):
        try:
            image_site = f"https://image.pollinations.ai/prompt/{prompt}?&seed={seed}&nologo=true"
            self.save_image(image_url=image_site, image_path=image_path)

            x, y = Polinations_API.get_image_size(image_path)

            if x == 1024 and y == 1024:
                image = Image.open(image_path)
                cropeed_image = image.crop((0, 0, 1024, 950))
                resized_image = cropeed_image.resize((1024, 1024))
                resized_image.save(image_path)
            else:
                logger.logging("NOT 1024*1024")
                image = Image.open(image_path)
                cropeed_image = image.crop((0, 0, 1024, 950))
                resized_image = cropeed_image.resize((1024, 1024))
                resized_image.save(image_path)

            logger.logging(f"{self.__class__.__name__} done: {image_path}")

            return image_path
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))


class CharacterAI_API:
    def __init__(self, generator: GenerateImages):
        self.generator = generator
        queue = generator.queue % len(generator.char_tokens)
        char_token = generator.char_tokens[queue]
        self.character = Character_AI(char_id=char_id_images, char_token=char_token, testing=True)
        self.suffix = "r2"
        self.return_images = 1

    def save_image(self, image_url, image_path):
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.save(image_path, "PNG")
        else:
            raise Exception("char.ai: нельзя сохранить изображение")

    def generate(self, prompt, image_path):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            image_path = loop.run_until_complete(self.generate_image(prompt, image_path))

            loop.close()

            logger.logging(f"{self.__class__.__name__} done: {image_path}")

            return image_path
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))

    async def generate_image(self, prompt, image_path):

        _, image_url = await self.character.get_answer(message=prompt, return_image=True)

        await self.save_image(image_url, image_path)

        return image_path


class Bing_API:
    def __init__(self, generator: GenerateImages):
        self.generator = generator
        self.app_version = '"6.5.0"'
        queue = generator.queue % len(generator.bing_cookies)
        self.bing_cookie = generator.bing_cookies[queue]
        self.suffix = "r4"
        self.return_images = 4
        self.user_agent = user_agent

    def get_request_id(self, prompt_row, rt):
        i = 0
        while True:
            if i == 50:
                raise Exception("Спустя 50 попыток не отправлен запрос")

            if prompt_row.lower() in self.generator.blocked_requests:
                raise Exception("Запрос уже был запрешён")

            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
                'cookie': self.bing_cookie,
                'sec-ch-ua-platform-version': self.app_version,
                'user-agent': self.user_agent
            }

            params = {
                'q': prompt_row,
                'rt': rt,
                'FORM': 'GENCRE',
            }

            data = {
                'q': prompt_row,
                'qs': 'ds',
            }

            response = requests.post('https://www.bing.com/images/create', params=params, headers=headers,
                                     data=data)

            soup = BeautifulSoup(response.text, 'html.parser')

            element = None

            try:
                element = soup.find(id="giloadhelpc").find_all('div')[0]
            except:
                pass

            # Не найден?
            if not element:
                logger.logging("ERROR IN BING: NOT FOUND ELEMENT")
                element = response.text

            if "Предупреждение о содержимом" in element:
                self.generator.blocked_requests.append(prompt_row.lower())
                raise Exception("Не пройдена модерация запроса")
            elif "Предоставьте более описательный запрос" in element:
                logger.logging("Недостаточно описан")
                time.sleep(1)
                prompt_row += ", HD, " + prompt_row
            else:
                logger.logging("Generate text:", element.text)
                break

            i += 1

        pattern = r'"([^"]*bing\.com[^"]*)"'
        matches = re.findall(pattern, response.text)

        if matches:
            for match in matches:
                if "https://www.bing.com/images/create?q=" in match:
                    id_match = re.search(r'id=([^&]+)', match)
                    if id_match:
                        return id_match.group(1)
        else:
            raise Exception("Совпадения не найдены")

        raise Exception("Нет ID, вероятно запрос заблокирован")

    def get_image_group_id(self, prompt_row, rt, request_id):
        url = 'https://www.bing.com/images/create'
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'upgrade-insecure-requests': '1',
            'cookie': self.bing_cookie,
            'user-agent': self.user_agent
        }

        params = {
            'q': prompt_row,
            'rt': rt,
            'FORM': 'GENCRE',
            'id': request_id,
            'nfy': '1'
        }

        response = requests.get(url, headers=headers, params=params)

        pattern = r'IG:"([^"]+)"'
        match = re.search(pattern, response.text)

        if match:
            return match.group(1)
        else:
            raise Exception("Совпадения не найдено")

    def check_generation(self, prompt_row, request_id, image_group_id, timeout=45):

        encoded_word = prompt_row.encode('utf-8')
        prompt = urllib.parse.quote(encoded_word)

        matches = []
        i = 0
        image_urls = set()

        while len(matches) < 4:
            if i > timeout:
                if len(matches) > 0:
                    break
                raise Exception("Timeout bing error")

            time.sleep(1)
            url = f"https://www.bing.com/images/create/async/results/{request_id}?q={prompt}+&IG={image_group_id}&IID=images.as"

            headers = {
                'cookie': self.bing_cookie,
                'sec-ch-ua-platform-version': self.app_version,
                'user-agent': self.user_agent
            }

            response = requests.get(url, headers=headers)

            pattern = r'thId=([^&]+)&quot;'
            matches = re.findall(pattern, response.text)
            for match in matches:
                image_id = match.replace('\\', '')
                image_urls.add(f"https://th.bing.com/th/id/{image_id}?pid=ImgGn")
            i += 1

        return image_urls

    def save_image(self, image_url, image_path):
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_path, 'wb') as file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, file)
            return image_path

        else:
            logger.logging(f"Ошибка при загрузке изображения. Код статуса: {response.status_code}")

    def generate(self, prompt, image_path, fast=False):
        try:
            rt = 4 if fast else 3
            request_id = self.get_request_id(prompt_row=prompt, rt=rt)
            image_group_id = self.get_image_group_id(prompt_row=prompt, rt=rt, request_id=request_id)
            image_urls = self.check_generation(prompt_row=prompt, request_id=request_id, image_group_id=image_group_id)

            results = []

            for i, image_url in enumerate(image_urls):
                result = self.save_image(image_url=image_url, image_path=image_path + f"_{i}.png")
                results.append(result)

            logger.logging(f"{self.__class__.__name__} done: {results}")

            return results
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))


class Kandinsky_API:
    def __init__(self, generator: GenerateImages):
        self.URL = 'https://api-key.fusionbrain.ai/'

        queue = generator.queue % len(generator.apis_kandinsky)

        self.AUTH_HEADERS = {
            'X-Key': f'Key {generator.apis_kandinsky[queue]}',
            'X-Secret': f'Secret {generator.secret_keys_kandinsky[queue]}',
        }

        self.suffix = "r1"
        self.return_images = 1

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate_request(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "style": "UHD",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=20, delay=1):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)

    def save_image(self, image_data_base64, image_path):
        selected_image_base64 = image_data_base64[0]
        image_data_binary = base64.b64decode(selected_image_base64)
        with open(image_path, 'wb') as file:
            file.write(image_data_binary)

    def generate(self, prompt, image_path):
        try:
            model_id = self.get_model()
            uuid = self.generate_request(prompt, model_id)
            image_data_base64 = self.check_generation(request_id=uuid, attempts=60, delay=1)
            self.save_image(image_data_base64, image_path)

            logger.logging(f"{self.__class__.__name__} done: {image_path}")

            return image_path
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))


async def reduce_image_resolution(image_path, target_size_mb=49):
    img = Image.open(image_path)
    while os.path.getsize(image_path) > target_size_mb * 1024 * 1024:
        new_width = int(img.width * 0.90)
        new_height = int(img.height * 0.90)
        img = img.resize((new_width, new_height))
        img.save(image_path)
