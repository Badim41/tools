import asyncio
import base64
import io
import json
import os
import random
import requests
import time
import zipfile
import urllib
import uuid
import re
import shutil

from PIL import Image

from discord_tools.character_ai_chat import Character_AI, char_id_images
from discord_tools.upscaler import upscale_image
from discord_tools.describe_image import describe_image, detect_bad_image

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

async def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            # print(f"Ширина изображения: {width}px, Высота изображения: {height}px")
            return width, height
    except Exception as e:
        print(f"Ошибка при получении размера изображения: {e}")
        return None

async def make_grind(image_paths, delete_temp=True):
    def create_black_image(width, height):
        return Image.new('RGB', (width, height), (0, 0, 0))

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

    if delete_temp:
        for image_path in image_paths:
            os.remove(image_path)

    return final_path


class Kandinsky_API:

    def __init__(self, url, api_key, secret_key):
        try:
            self.URL = url
            self.AUTH_HEADERS = {
                'X-Key': f'Key {api_key}',
                'X-Secret': f'Secret {secret_key}',
            }
        except Exception as e:
            print("error in async_image:(id:4)", e)

    def get_model(self):
        try:
            response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
            data = response.json()
            return data[0]['id']
        except Exception as e:
            print("error in async_image:(id:3)", e)

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        try:
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
        except Exception as e:
            print("error in async_image:(id:2)", e)

    async def check_generation(self, request_id, attempts=20, delay=1):
        def get_response():
            return requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)

        try:
            while attempts > 0:
                response = await asyncio.to_thread(get_response)
                data = response.json()
                if data['status'] == 'DONE':
                    return data['images']

                attempts -= 1
                time.sleep(delay)
        except Exception as e:
            print("error in async_image:(id:1)", e)


class GenerateImages:
    def __init__(self, secret_keys_kandinsky=None, apis_kandinsky=None, char_tokens=None, bing_cookies=None):
        if not os.path.exists('images'):
            os.mkdir('images')

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

        self.kandinskies = []
        if secret_keys_kandinsky:
            for i in range(len(secret_keys_kandinsky)):
                self.kandinskies.append(Kandinsky_API(url='https://api-key.fusionbrain.ai/',
                                                      secret_key=secret_keys_kandinsky[i],
                                                      api_key=apis_kandinsky[i]))

        self.characters_ai = []
        if char_tokens:
            for char_token in char_tokens:
                self.characters_ai.append(Character_AI(char_id=char_id_images, char_token=char_token, testing=True))
        
        self.blocked_requests = []
        self.queue = 0

    async def generate(self, prompt, user_id=0, kandinsky=True, polinations=True, character_ai=True, bing_image_generator=True,
                       zip_name=None, delete_temp=True, bing_fast=False):
        self.queue += 1
        if zip_name:
            text_name = f"prompt_{user_id}.txt"
            with zipfile.ZipFile(zip_name, "w") as zipf:
                with open(text_name, "w") as text_file:
                    text_file.write(prompt)
                zipf.write(text_name)
                os.remove(text_name)

        functions = []
        if kandinsky:
            functions.append(self.kandinsky_generate(prompt, user_id))
        if polinations:
            functions.append(self.image_polinations(prompt, user_id, zip_name, delete_temp))
        if character_ai:
            functions.append(self.character_ai(prompt, user_id))
        if bing_image_generator:
            # bing_image_generate(self, prompt, user_id, zip_name, delete_temp, fast=False):
            functions.append(self.bing_image_generate(prompt, user_id, zip_name, delete_temp, bing_fast))

        results = [result for result in await asyncio.gather(*functions) if result and os.path.exists(result)]

        if zip_name:
            with zipfile.ZipFile(zip_name, "a") as zipf:
                for result in results:
                    zipf.write(result)

        return results

    async def kandinsky_generate(self, prompt, user_id):
        try:
            if not self.kandinskies:
                return None
            api = self.kandinskies[self.queue % len(self.kandinskies)]
            model_id = api.get_model()
            uuid = api.generate(prompt, model_id)
            image_data_base64 = await api.check_generation(request_id=uuid, attempts=10, delay=1)
            selected_image_base64 = image_data_base64[0]
            image_data_binary = base64.b64decode(selected_image_base64)
            image_path = f"images/{user_id}_{self.queue}_r1.png"
            with open(image_path, 'wb') as file:
                file.write(image_data_binary)
            print("Kandinsky done!", image_path)
            return image_path
        except Exception as e:
            print("Error in kandinsky:",e)

    async def image_polinations(self, prompt, user_id, zip_name, delete_temp):
        def save_image_png(image_url, i):
            try:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    image_path = f"images/{user_id}_{self.queue}_{i}_r3.png"
                    image.save(image_path, "PNG")

                    return image_path
            except Exception as e:
                print("Ошибка при конвертации изображения:", e)
                pass

        try:
            all_results = []
            for i in range(4):
                image_site = f"https://image.pollinations.ai/prompt/{prompt}?&seed={random.randint(1, 9999999)}&nologo=true"
                result = await asyncio.to_thread(save_image_png, image_site, i)
                if await get_image_size(result):
                    x, y = await get_image_size(result)
                    if x == 1024 and y == 1024:
                        image = Image.open(result)
                        cropeed_image = image.crop((0, 0, 1024, 950))
                        resized_image = cropeed_image.resize((1024, 1024))
                        resized_image.save(result)
                    else:
                        print("NOT 1024*1024")
                        image = Image.open(result)
                        cropeed_image = image.crop((0, 0, 1024, 950))
                        resized_image = cropeed_image.resize((1024, 1024))
                        resized_image.save(result)
                else:
                    print("NOT 1024*1024, NOT FOUND X AND Y")
                    image = Image.open(result)
                    resized_image = image.resize((1024, 1024))
                    resized_image.save(result)

                all_results.append(result)
                print(f"image_polinations done{i + 1}/4!", result)

            if zip_name:
                for result in all_results:
                    with zipfile.ZipFile(zip_name, "a") as zipf:
                        zipf.write(result)

            grind_image = await make_grind(all_results, delete_temp=delete_temp)
            return grind_image
        except Exception as e:
            print("error in image_polinations:", e)

    async def character_ai(self, prompt, user_id):
        if not self.characters_ai:
            return None
        async def save_image():
            response = requests.get(image_url)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                image.save(image_path, "PNG")
            else:
                raise Exception("char.ai: нельзя сохранить изображение")

        image_path = f"images/{user_id}_{self.queue}_2r.png"
        try:
            character_ai = self.characters_ai[self.queue % len(self.characters_ai)]
            _, image_url = await character_ai.get_answer(message=prompt, username_in_answer=False, return_image=True)
            await save_image()
            print("character AI done!", image_path)
            return image_path
        except Exception as e:
            print("error in character.ai:", e)

    async def bing_image_generate(self, prompt, user_id, zip_name, delete_temp, fast):
        def generate_images(prompt_row):
            while True:
                if prompt_row.lower() in self.blocked_requests:
                    raise Exception("Запрос уже был запрешён")
                encoded_word = prompt_row.encode('utf-8')
                prompt = urllib.parse.quote(encoded_word)
            
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
                    'cookie': self.bing_cookies[0],
                    'sec-ch-ua-platform-version': '"6.5.0"',
                    'user-agent': user_agent
                }
            
                params = {
                    'q': prompt_row,
                    'rt': '3',
                    'FORM': 'GENCRE',
                }
            
                data = {
                    'q': prompt_row,
                    'qs': 'ds',
                }
            
                response = requests.post('https://www.bing.com/images/create', params=params, headers=headers, data=data)
            
                # print(response.text)
            
                if "Предупреждение о содержимом" in response.text:
                    self.blocked_requests.append(prompt_row.lower())
                    raise Exception("Не пройдена модерация запроса")
                elif "Предоставьте более описательный запрос" in response.text:
                    print("Не достаточно описан")
                    time.sleep(1)
                    prompt_row += ", HD, " + prompt_row
                else:
                    break
            
            pattern = r'"([^"]*bing\.com[^"]*)"'
            matches = re.findall(pattern, response.text)
            
            request_id = None
            
            if matches:
                # Если найдены совпадения, выводим их
                for match in matches:
                    if "https://www.bing.com/images/create?q=" in match:
                        id_match = re.search(r'id=([^&]+)', match)
                        if id_match:
                            request_id = id_match.group(1)
                            print(request_id)
                            break
                    # print(match)
            else:
                print("Совпадения не найдены")

            if request_id is None:
                raise Exception("Нет ID, вероятно запрос заблокирован")

            url = 'https://www.bing.com/images/create'
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'upgrade-insecure-requests': '1',
                'cookie': self.bing_cookies[0],
                'user-agent': user_agent
            }
            
            params = {
                'q': prompt_row,
                'rt': rt,
                'FORM': 'GENCRE',
                'id': request_id,
                'nfy': '1'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            # print(response.text)
            
            pattern = r'IG:"([^"]+)"'
            match = re.search(pattern, response.text)
            
            if match:
                image_group_id = match.group(1)
                print(image_group_id)
            else:
                raise Exception("Совпадения не найдено")

            matches = []
            i = 0
            
            while len(matches) < 4:
                if i > 100:
                    if len(matches) > 0:
                        break
                    raise Exception("Timeout bing error")
                time.sleep(1)
                url = f"https://www.bing.com/images/create/async/results/{request_id}?q={prompt}+&IG={image_group_id}&IID=images.as"
            
                headers = {
                    'cookie': self.bing_cookies[0],
                    'sec-ch-ua-platform-version': '"6.5.0"',
                    'user-agent': user_agent
                }
            
                response = requests.get(url, headers=headers)
                
                pattern = r'thId=([^&]+)&quot;'
                matches = re.findall(pattern, response.text)
                image_urls = set()
                for match in matches:
                    image_id = match.replace('\\', '')
                    image_urls.add(f"https://th.bing.com/th/id/{image_id}?pid=ImgGn")
                print(image_urls)
                i+=1

            all_results = []
            for i, image_url in enumerate(image_urls):
                result = save_image_png(image_url, i)
                all_results.append(result)
            return all_results
            
        
        def save_image_png(image_url, i):
            response = requests.get(image_url, stream=True)
            image_path = f"images/{user_id}_{self.queue}_{i}_r4.png"
            if response.status_code == 200:
                with open(image_path, 'wb') as file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file)
                return image_path
    
            else:
                print(f"Ошибка при загрузке изображения. Код статуса: {response.status_code}")

        if not self.bing_cookies:
            return None

        rt = 3 if fast else 4
        
        try:
            all_results = await asyncio.to_thread(generate_images, prompt_row=prompt)

            if zip_name:
                for result in all_results:
                    with zipfile.ZipFile(zip_name, "a") as zipf:
                        zipf.write(result)

            print("Bing images done!")
            grind_image = await make_grind(all_results, delete_temp=delete_temp)
            return grind_image
        except Exception as e:
            print("error in bing_image_generate:", e)

async def reduce_image_resolution(image_path, target_size_mb=49):
    img = Image.open(image_path)
    while os.path.getsize(image_path) > target_size_mb * 1024 * 1024:
        new_width = int(img.width * 0.90)
        new_height = int(img.height * 0.90)
        img = img.resize((new_width, new_height))
        img.save(image_path)
