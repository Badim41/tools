import io
import os
import requests
from PIL import Image
from discord_tools.detect_mat import moderate_mat_in_sentence
from discord_tools.logs import Logs, Color

logger = Logs(warnings=True)

char_id_faradey = "_lpN3-bUhOIGPej2VmRYaVAWSsW7T9z3vWWVlt6SFW4"  # Faradey
char_id_badim41 = "KNA19UuC0-8-G15wQ9XtrvUJcZphTZQ2XkwY2u-B3Og"  # Badim41
char_id_keklol = "_iX7Jr7aKL67upcVIzWTHf1g3LtN4I2NosrGEXhpDJE"  # Kek lol
char_id_images = "bQBlcCVVjfTAzv8OWK30dw7Tj-TNtKC_Rh0Z46Dx6fY"  # images

import uuid
import characterai, asyncio


class ModerateParams:
    until_good = "until_good"
    replace_mat = "replace_mat"
    skip = "skip"


class Character_AI:
    def __init__(self, char_id, char_token, testing=False):
        self.char_id = char_id
        self.char_token = char_token
        self.user_id = None
        self.room_id = None
        self.testing = testing

    async def create_chat(self):
        client = characterai.PyAsyncCAI(self.char_token)

        async with client.connect() as chat2:
            chat_id = str(uuid.uuid4())
            await chat2.new_chat(self.char_id, chat_id, self.user_id)
            logger.logging("room id:", chat_id, color=Color.GRAY)
            return chat_id

    async def get_user_id(self):
        client = characterai.PyAsyncCAI(self.char_token)

        async with client.connect() as chat2:
            try:
                await chat2.new_chat(self.char_id, "делаем", "ошибку")
            except Exception as e:
                # я не придумал как получить user_id по-другому :(
                e = str(e)
                user_id = e[e.rfind(" ") + 1:-1]
                return user_id

    async def wait_for_image(self, image_url):
        if self.testing:
            print("image_url", image_url)
        try:
            for i in range(120):
                if self.testing and i % 20 == 0:
                    logger.logging(f"wait character.ai {image_url}: {i/2} s")
                await asyncio.sleep(0.5)
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_path = f"temp.png"
                    image = Image.open(io.BytesIO(response.content))
                    image.save(image_path, "PNG")
                    os.remove(image_path)
                    break
            # print(f"Не удалось загрузить изображение\"{image_url}\"")
        except Exception as e:
            print("No such url", e)
            pass

    async def decode_response(self, data: dict, username_in_answer):
        if self.testing:
            print("JSON DATA:", data)
        turn = data["turn"]
        author = turn["author"]
        candidates = turn["candidates"][-1]
        turn_key = turn["turn_key"]

        name = author["name"]
        text = candidates["raw_content"]
        turn_id = turn_key["turn_id"]
        candidate_id = candidates["candidate_id"]
        chat_id = turn_key["chat_id"]
        primary_candidate_id = ["primary_candidate_id"]
        image = ""
        try:
            image = data["turn"]["candidates"][0]["tti_image_rel_path"]
            await self.wait_for_image(image)
        except Exception:
            pass
        if username_in_answer:
            return f'{name}: {text}', turn_id, candidate_id, chat_id, primary_candidate_id, image
        else:
            return text, turn_id, candidate_id, chat_id, primary_candidate_id, image

    async def get_answer(self, message: str, username_in_answer=False, moderate_answer=ModerateParams.until_good,
                         return_image=False):
        try:
            if not self.room_id or not self.user_id:
                self.user_id = await self.get_user_id()
                self.room_id = await self.create_chat()
                if self.testing:
                    logger.logging("loaded character.ai", self.room_id, self.user_id, self.char_id, self.char_token,
                                   color=Color.GRAY)

            client = characterai.PyAsyncCAI(self.char_token)
            async with client.connect() as chat2:

                data = await chat2.send_message(self.char_id, self.room_id, message,
                                                {'author_id': f'{self.user_id}'})

                text, turn_id, candidate_id, chat_id, primary_candidate_id, image = \
                    await self.decode_response(data,
                                               username_in_answer)

                # пока есть маты
                while True:
                    mat_found, replaced_text = await moderate_mat_in_sentence(text)
                    if moderate_answer == ModerateParams.skip:
                        break
                    elif moderate_answer == ModerateParams.replace_mat:
                        if mat_found:
                            text = replaced_text
                        break
                    elif moderate_answer == ModerateParams.until_good:
                        if not mat_found:
                            break
                        await chat2.rate(1, chat_id, turn_id, candidate_id)
                        logger.logging("Оставлен плохой отзыв!", color=Color.GRAY)
                        data = await chat2.next_message(self.char_id, chat_id, turn_id)
                        text, turn_id, candidate_id, chat_id, primary_candidate_id, image = await self.decode_response(data,
                                                                                                                       username_in_answer)
                    else:
                        raise Exception("Не выбран тип модерации")

                await chat2.rate(5, chat_id, turn_id, candidate_id)

                if self.testing:
                    logger.logging("Answer from character.ai:", text, image, color=Color.GRAY)
        except Exception as e:
            logger.logging("character AI error:", str(e), color=Color.RED)
            text, image = "", ""

        if not return_image:
            return text

        return text, image
