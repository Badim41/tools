import asyncio
import base64
import io
import json
import os
import random
import requests
import time
import zipfile
from PIL import Image

from discord_tools.character_ai_chat import Character_AI, char_id_images
from discord_tools.upscaler import upscale_image

async def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            # print(f"Ширина изображения: {width}px, Высота изображения: {height}px")
            return width, height
    except Exception as e:
        print(f"Ошибка при получении размера изображения: {e}")
        return None


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
    def __init__(self, secret_keys_kandinsky=None, apis_kandinsky=None, char_tokens=None):
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

        self.kandinskies = []

        for i in range(len(secret_keys_kandinsky)):
            self.kandinskies.append(Kandinsky_API(url='https://api-key.fusionbrain.ai/',
                                                  secret_key=secret_keys_kandinsky[i],
                                                  api_key=apis_kandinsky[i]))

        self.characters_ai = []
        for char_token in char_tokens:
            self.characters_ai.append(Character_AI(char_id=char_id_images, char_token=char_token, testing=True))

        self.queue = 0

    async def generate(self, prompt, user_id=0, kandinsky=True, polinations=True, character_ai=True,
                       zip_name=None):
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
            functions.append(self.image_polinations(prompt, user_id, zip_name))
        if character_ai:
            functions.append(self.character_ai(prompt, user_id))

        results = [result for result in await asyncio.gather(*functions) if result and os.path.exists(result)]

        if zip_name:
            with zipfile.ZipFile(zip_name, "a") as zipf:
                for result in results:
                    zipf.write(result)

        return results

    async def kandinsky_generate(self, prompt, user_id):
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

    async def image_polinations(self, prompt, user_id, zip_name):
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

        async def make_grind(image_paths):
            images = [Image.open(path) for path in image_paths]
            image_width, image_height = images[0].size
            grid_width = 2 * image_width
            grid_height = 2 * image_height
            grid_image = Image.new('RGB', (grid_width, grid_height))

            for i in range(2):
                for j in range(2):
                    index = i * 2 + j
                    grid_image.paste(images[index], (j * image_width, i * image_height))

            final_path = image_paths[3].replace(".png", "FINAL.png")
            grid_image.save(final_path)

            for i in range(4):
                os.remove(image_paths[i])

            return final_path

        try:
            all_results = []
            for i in range(4):
                image_site = f"https://image.pollinations.ai/prompt/{prompt}?&seed={random.randint(1, 9999999)}&nologo=true"
                result = await asyncio.to_thread(save_image_png, image_site, i)
                if await get_image_size(result):
                    x, y = await get_image_size(result)
                    if x == 768 and y == 768:
                        image = Image.open(result)
                        cropped_image = image.crop((0, 0, 768, 725))
                        resized_image = cropped_image.resize((768, 768))
                        resized_image.save(result)
                    else:
                        image = Image.open(result)
                        cropped_image = image.crop((0, 0, 512, 468))
                        resized_image = cropped_image.resize((768, 768))
                        resized_image.save(result)
                else:
                    image = Image.open(result)
                    cropped_image = image.crop((0, 0, 512, 468))
                    resized_image = cropped_image.resize((768, 768))
                    resized_image.save(result)

                all_results.append(result)
                print(f"image_polinations done{i + 1}/4!", result)

            if zip_name:
                for result in all_results:
                    with zipfile.ZipFile(zip_name, "a") as zipf:
                        zipf.write(result)

            grind_image = await make_grind(all_results)
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
