import os
import re
import requests
import time
from PIL import Image

import json

from discord_tools.logs import Logs
from discord_tools.key_manager import KeyManager

key_manager = KeyManager("stability")

logger = Logs(warnings=True)

if not os.path.exists("images"):
    os.mkdir("images")


class FoundNSFW(Exception):
    """Когда найден небезопасный контент"""
    pass


class Stable_Diffusion_API:
    def __init__(self, api_keys=None):
        if isinstance(api_keys, list):
            self.api_keys = api_keys
        elif isinstance(api_keys, str):
            self.api_keys = [api_keys]

        if not self.api_keys:
            self.api_keys = [self.get_free_api_key()]

        self.api_keys = key_manager.get_not_expired_keys(self.api_keys, recovering_time=None)

    @staticmethod
    def get_free_api_key():
        url = "https://www.midjourneyfree.ai/static/js/main.5be83a7f.js"

        payload = ""
        headers = {
            "Referer": "https://www.midjourneyfree.ai/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36"
        }

        response = requests.request("GET", url, data=payload, headers=headers)

        text = response.text

        # Регулярное выражение для извлечения значения sk-KEY
        pattern = r'Authorization:"Bearer ([\w-]+)"'

        # Извлечение значения sk-KEY
        match = re.search(pattern, text)
        if match:
            sk_key = match.group(1)
            if sk_key.startswith("sk-"):
                return sk_key
        raise Exception("sk-KEY не найден.")

    def search_and_replace(self, image_path, prompt, search_prompt, random_factor="", negative_prompt="", seed=0,
                           output_format="png"):
        if not self.api_keys:
            print("No api keys stability")
            return False
        try:
            host = f"https://api.stability.ai/v2beta/stable-image/edit/search-and-replace"

            params = {
                "seed": seed,
                "mode": "search",
                "output_format": output_format,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "search_prompt": search_prompt,
            }

            headers = {
                "Accept": "image/*",
                "Authorization": f"Bearer {self.api_keys[0]}"
            }

            # Encode parameters
            files = {}
            files["image"] = open(image_path, 'rb')

            # Send request
            logger.logging(f"Sending REST request to {host}...")
            response = requests.post(
                host,
                headers=headers,
                files=files,
                data=params
            )
            if not response.ok:
                if response.status_code == 402:
                    logger.logging("Недостаточно средств на балансе, удаляем ключ:", self.api_keys[0])
                    key_manager.add_expired_key(self.api_keys[0])
                    self.api_keys = self.api_keys[1:]
                    return self.search_and_replace(image_path=image_path, prompt=prompt, search_prompt=search_prompt,
                                                   random_factor=random_factor, negative_prompt=negative_prompt,
                                                   seed=seed, output_format=output_format)
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            # Decode response
            output_image = response.content
            finish_reason = response.headers.get("finish-reason")

            # Check for NSFW classification
            if finish_reason == 'CONTENT_FILTERED':
                raise FoundNSFW

            # Save and display result
            filename, _ = os.path.splitext(os.path.basename(image_path))
            edited = f"images/{random_factor}{filename}.{output_format}"
            with open(edited, "wb") as f:
                f.write(output_image)
            return edited
        except FoundNSFW:
            return FoundNSFW
        except Exception as e:
            logger.logging("ERROR IN SEARCH AND REPLACE:", e)

    @staticmethod
    def resize_image(image_path):
        # Открываем изображение
        img = Image.open(image_path)

        # Получаем размеры изображения
        width, height = img.size

        # Проверяем, соответствуют ли размеры требованиям API
        if width == 1024 and height == 576:
            # Изображение уже подходит, не нужно изменять размер
            return
        elif width == 576 and height == 1024:
            # Изображение уже подходит, не нужно изменять размер
            return
        elif width == 768 and height == 768:
            # Изображение уже подходит, не нужно изменять размер
            return
        else:
            # Изображение не соответствует требованиям API, изменяем его размер

            # Проверяем, отличаются ли ширина и высота менее чем на 10%
            if abs(width - height) < 0.1 * min(width, height):
                print("Изменение размера изображения: 768*768")
                # Размеры изображения изменяются на 768x768
                img = img.resize((768, 768))
            else:
                aspect_ratio = width / height

                if aspect_ratio > 1:
                    print("Изменение размера изображения: 1024*576")
                    img = img.resize((1024, 576))
                else:
                    print("Изменение размера изображения: 576*1024")
                    img = img.resize((576, 1024))

            img.save(image_path)

    def get_generate_video_id(self, image_path):
        self.resize_image(image_path)
        response = requests.post(
            f"https://api.stability.ai/v2beta/image-to-video",
            headers={
                "authorization": f"Bearer {self.api_keys[0]}"
            },
            files={
                "image": open(image_path, "rb")
            },
            data={
                "seed": 0,
                "cfg_scale": 1.8,
                "motion_bucket_id": 127
            },
        )
        if response.status_code == 402:
            print("Недостаточно средств на балансе, удаляем ключ:", self.api_keys[0])
            key_manager.add_expired_key(self.api_keys[0])
            self.api_keys = self.api_keys[1:]
            return self.get_generate_video_id(image_path=image_path)
        if "Your request was flagged" in response.text:
            return FoundNSFW

        video_id = response.json().get('id')
        print("VIDEO ID", video_id, response.json())
        return video_id

    def img_to_video(self, image_path, random_factor="", attemps=100):
        if not self.api_keys:
            print("No api keys stability")
            return False

        try:
            generation_id = self.get_generate_video_id(image_path)
            for i in range(attemps):

                response = requests.request(
                    "GET",
                    f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
                    headers={
                        'accept': "video/*",  # Use 'application/json' to receive base64 encoded JSON
                        'authorization': f"Bearer {self.api_keys[0]}"
                    },
                )

                if response.status_code == 202:
                    time.sleep(10)
                else:
                    break

            output_path = f"images/{random_factor}video.mp4"
            if response.status_code == 200:
                logger.logging("Generation complete!")
                with open(output_path, 'wb') as file:
                    file.write(response.content)
                return output_path
            else:
                raise Exception(str(response.json()))
        except Exception as e:
            logger.logging("ERROR IN VIDEO GENERATE:", e)

    def text_to_image(self, prompt, negative_prompt="", aspect_ratio="1:1", seed=0, output_format="png", model="sd3",
                      random_factor: [int, str] = "1", output_path=None):
        # prompt = "Victory Day"  # @param {type:"string"}
        # negative_prompt = ""  # @param {type:"string"}
        # aspect_ratio = "1:1"  # @param ["21:9", "16:9", "3:2", "5:4", "1:1", "4:5", "2:3", "9:16", "9:21"]
        # seed = 0  # @param {type:"integer"}
        # output_format = "png"  # @param ["jpeg", "png"]
        # model = "sd3"  # @param ["sd3", "sd3-turbo"]
        if not self.api_keys:
            print("No api keys stability")
            return False

        host = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt if model == "sd3" else "",
            "aspect_ratio": aspect_ratio,
            "seed": seed,
            "output_format": output_format,
            "model": model,
            "mode": "text-to-image"
        }

        headers = {
            "Accept": "image/*",
            "Authorization": f"Bearer {self.api_keys[0]}"
        }

        # Encode parameters
        files = {"none":""}

        # Send request
        logger.logging(f"Sending REST request to {host}...")
        response = requests.post(
            host,
            headers=headers,
            files=files,
            data=params
        )

        if not response.ok:
            if response.status_code == 402:
                logger.logging("Недостаточно средств на балансе, удаляем ключ:", self.api_keys[0])
                key_manager.add_expired_key(self.api_keys[0])
                self.api_keys = self.api_keys[1:]
                return self.text_to_image(prompt=prompt, negative_prompt=negative_prompt, aspect_ratio=aspect_ratio,
                                          seed=seed, output_format=output_format, model=model)
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        # Decode response
        output_image = response.content
        finish_reason = response.headers.get("finish-reason")

        # Check for NSFW classification
        if finish_reason == 'CONTENT_FILTERED':
            raise Exception("Generation failed NSFW classifier")

        # Save and display result
        if not output_path:
            print("No output_path")
            output_path = f"{random_factor}.{output_format}"

        with open(output_path, "wb") as f:
            f.write(output_image)
        print("saved stability as", output_path)

        return output_path

if __name__ == '__main__':
    import asyncio
    from discord_tools.image_generate import GenerateImages
    sd = Stable_Diffusion_API(api_keys="sk-lRd9jouC5Xpkqqpk3cgLySCjs4Rzr4c4JwbxeDI57UWeCtNW")
    generator = GenerateImages(stable_diffusion=sd)
    images = asyncio.run(generator.generate("Tree 4K", polinations=False, waufu=False, hugging_face=False))
    print(images)

