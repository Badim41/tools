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
import re
import shutil
from bs4 import BeautifulSoup

from PIL import Image

from discord_tools.astica_API import Astica_API, GenerateQuality
from discord_tools.character_ai_chat import Character_AI, char_id_images
from discord_tools.logs import Logs, Color

logger = Logs(warnings=True)

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

RESULT_PATH = 'images'
GLOBAL_IMAGE_TIMEOUT = 60


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
    def __init__(self, secret_keys_kandinsky=None, apis_kandinsky=None, char_tokens=None, bing_cookies=None,
                 proxies=None):
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
        self.proxies = proxies
        self.queue = 0

    # [Kandinsky_API, Polinations_API, CharacterAI_API, Bing_API]
    async def generate_image_grid(self, model_class, image_name, prompt, row_prompt, delete_temp=True, zip_name=None):
        def create_black_image(width, height):
            return Image.new('RGB', (width, height), (0, 0, 0))

        try:
            model_instance = model_class(self)

            if model_instance.support_russian:
                prompt = row_prompt
                print(f"Changed prompt for {model_instance.__class__.__name__}: {row_prompt}")

            image_path = f"{RESULT_PATH}/{image_name}_{model_instance.suffix}_{self.queue}"

            image_paths = []

            try:
                if model_instance.return_images == 1:
                    tasks = [asyncio.to_thread(model_instance.generate, prompt, image_path + f"_{i}.png") for i in
                             range(4)]
                    image_paths = await asyncio.wait_for(asyncio.gather(*tasks), timeout=GLOBAL_IMAGE_TIMEOUT + 60)
                elif model_instance.return_images == 4:
                    image_paths = await asyncio.wait_for(asyncio.to_thread(model_instance.generate, prompt, image_path),
                                                         timeout=GLOBAL_IMAGE_TIMEOUT + 60)
                else:
                    raise Exception(f"Неправильное количество возвращаемых изображений:{model_instance.return_images}")
            except Exception as e:
                logger.logging(f"Image timeout {model_instance.__class__.__name__}", e)

            images = []

            for path in image_paths:
                try:
                    images.append(Image.open(path))
                except Exception as e:
                    logger.logging(f"warn in {model_instance.__class__.__name__}", e)

            if not images:
                return

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
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))

    async def generate(self, prompt, user_id=0, kandinsky=True, polinations=True, character_ai=True,
                       bing_image_generator=True, zip_name=None, delete_temp=True, bing_fast=False, astica=True,
                       waufu=True,
                       row_prompt=None):
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
        if kandinsky and self.apis_kandinsky and self.secret_keys_kandinsky:
            models.append(Kandinsky_API)
        if polinations:
            models.append(Polinations_API)
        if character_ai and self.char_tokens:
            models.append(CharacterAI_API)
        if bing_image_generator and self.bing_cookies:
            models.append(Bing_API)
        if astica:
            models.append(Astica_Desinger_API)
        if waufu:
            models.append(Waifus_API)

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
        self.support_russian = False

    def save_image(self, image_url, image_path, timeout=GLOBAL_IMAGE_TIMEOUT):
        response = requests.get(image_url, timeout=timeout)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            image.save(image_path, "PNG")

    @staticmethod
    def get_image_size(image_path):
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height

    def generate(self, prompt, image_path, seed=None):
        if seed is None:
            seed = random.randint(1, 9999999)
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
        self.char_token = generator.char_tokens[queue]
        self.character = Character_AI(char_id=char_id_images, char_token=self.char_token, testing=False)
        self.suffix = "r2"
        self.return_images = 1
        self.support_russian = False

    def save_image(self, image_url, image_path):
        headers = {
            'Authorization': f'Token {self.char_token}'
        }
        response = requests.get(image_url, stream=True, headers=headers)
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

        self.save_image(image_url, image_path)

        return image_path


class Astica_Desinger_API:
    def __init__(self, generator: GenerateImages):
        self.generator = generator
        self.api = Astica_API(proxies=generator.proxies)
        self.suffix = "r5"
        self.return_images = 1
        self.support_russian = False

    def generate(self, prompt, image_path, quality=GenerateQuality.high):
        try:
            result_path = self.api.generate_image(prompt, generate_quality=quality, image_path=image_path)
            return result_path
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))


class Waifus_API:
    def __init__(self, generator: GenerateImages):
        self.generator = generator
        self.api = Astica_API(proxies=generator.proxies)
        self.suffix = "r6"
        self.return_images = 1
        self.support_russian = False

    def check_generation(self, request_id, model, delay=0.5):
        for i in range(int(GLOBAL_IMAGE_TIMEOUT // delay)):
            url = f"https://waifus-api.nemusona.com/job/status/{model}/{request_id}"

            payload = ""
            headers = {}

            response = requests.request("GET", url, data=payload, headers=headers)
            print("Waifu status:", response.text)
            if response.text == "completed":
                return True
            time.sleep(delay)

    def get_result(self, request_id, model):
        url = f"https://waifus-api.nemusona.com/job/result/{model}/{request_id}"

        payload = ""
        headers = {}

        response = requests.request("GET", url, data=payload, headers=headers)
        return response.json()['base64']

    def save_image(self, base64_image, image_path):
        with open(image_path, "wb") as file:
            file.write(base64.b64decode(base64_image))

        return image_path

    def send_generate_request(self, prompt, negative_prompt='', cfg_scale=10, denoising_strength=0.5, seed=None,
                              model="anything"):
        url = f"https://waifus-api.nemusona.com/job/submit/{model}"

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "cfg_scale": cfg_scale,
            "denoising_strength": denoising_strength,
            "seed": seed
        }

        response = requests.request("POST", url, json=payload)

        return response.text

    def generate(self, prompt, image_path, negative_prompt='', cfg_scale=10, denoising_strength=0.5, seed=None,
                 model="anything"):
        if seed is None:
            seed = random.randint(1, 9999999)
        try:
            request_id = self.send_generate_request(prompt, negative_prompt=negative_prompt,
                                                    cfg_scale=cfg_scale,
                                                    denoising_strength=denoising_strength,
                                                    seed=seed, model=model)
            generated = self.check_generation(request_id, model)
            if not generated:
                raise Exception("Not generated!")
            base64_image = self.get_result(request_id, model)
            image_path = self.save_image(base64_image, image_path)

            logger.logging(f"{self.__class__.__name__} done: {image_path}")

            return image_path
        except:
            logger.logging(f"error in {self.__class__.__name__}", str(traceback.format_exc()))


class Bing_API:
    def __init__(self, generator: GenerateImages):
        self.generator = generator
        self.app_version = '"10.0.0"'  # MAKE UPDATE AUTOMATIC ?
        queue = generator.queue % len(generator.bing_cookies)
        self.bing_cookie = generator.bing_cookies[queue]
        self.suffix = "r4"
        self.return_images = 4
        self.user_agent = user_agent
        self.support_russian = True

    def get_request_id(self, prompt_row, rt, attempts=5, adding_details=None, delay=0.5):
        if not adding_details:
            adding_details = ["HD, 4K, 8K", "высокого разрешения, качественные, четкие",
                              "подробные, детализированные, 3D рендер",
                              "яркие, реалистичные, превосходные"]

        max_request_len = 479
        prompt = prompt_row[:max_request_len]

        i = 0
        while True:

            if prompt.lower() in self.generator.blocked_requests:
                raise Exception("Запрос уже был запрешён")

            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
                'cookie': self.bing_cookie,
                'sec-ch-ua-platform-version': self.app_version,
                'user-agent': self.user_agent
            }

            params = {
                'q': prompt,
                'rt': rt,
                'FORM': 'GENCRE',
            }

            data = {
                'q': prompt,
                'qs': 'ds',
            }

            response = requests.post('https://www.bing.com/images/create', params=params, headers=headers,
                                     data=data)

            if not response.status_code == 200:
                logger.logging("Bing image status:", response.status_code, color=Color.RED)
                continue

            if i == attempts:
                with open("temp_response_bing.txt", "w", encoding="utf-8") as writer:
                    writer.write(response.text)
                raise Exception(f"Спустя {attempts} попыток не отправлен запрос")

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

            if "Предупреждение о содержимом" in response.text:
                self.generator.blocked_requests.append(prompt.lower())
                raise Exception("Не пройдена модерация запроса")
            elif "Предоставьте более описательный запрос" in response.text:
                logger.logging("Недостаточно описан")
                time.sleep(delay)
                prompt += ", " + adding_details[i % len(adding_details)] + ", " + prompt
            elif "Вы больше не можете отправлять запросы" in response.text:
                raise Exception("Слишком много изображений за раз.")
            elif "Эта запрос проверяется" in response.text:
                raise Exception(
                    "Содержимое запроса не может пройти модерацию, поэтому запрос на проверке. Скорее всего это займёт ОЧЕНЬ много времени")
            elif "Возникла проблема." in response.text:
                raise Exception("IP заблокирован, используйте прокси")
            else:
                logger.logging("Generate text:", element.text)
                pattern = r'"([^"]*bing\.com[^"]*)"'
                matches = re.findall(pattern, response.text)

                if matches:
                    for match in matches:
                        if "https://www.bing.com/images/create?q=" in match:
                            id_match = re.search(r'id=([^&]+)', match)
                            if id_match:
                                return id_match.group(1)
                logger.logging("Вероятно недостаточно описан")
                time.sleep(delay)
                prompt += ", " + adding_details[i % len(adding_details)] + ", " + prompt

            i += 1
            if len(prompt) > max_request_len:
                i = attempts - 1  # ещё 1 шанс на запрос
                prompt = f"Табличка с текстом \"{prompt_row}\""
                logger.logging("Запрос изменён на:", prompt, color=Color.BLUE)

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

    def check_generation(self, prompt_row, request_id, image_group_id, timeout=GLOBAL_IMAGE_TIMEOUT, delay=1):

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

            time.sleep(delay)
            url = f"https://www.bing.com/images/create/async/results/{request_id}?q={prompt}+&IG={image_group_id}&IID=images.as"

            headers = {
                'cookie': self.bing_cookie,
                'sec-ch-ua-platform-version': self.app_version,
                'user-agent': self.user_agent
            }

            response = requests.get(url, headers=headers)

            pattern = r'thId=([^&]+)&quot;'
            matches = re.findall(pattern, response.text)
            i += 1

        for match in matches:
            image_id = match.replace('\\', '')
            image_urls.add(f"https://th.bing.com/th/id/{image_id}?pid=ImgGn")

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
        self.support_russian = True

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

            if image_data_base64 is None:
                logger.logging(f"Error: image_data_base64 in {self.__class__.__name__} is None")
                return

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
