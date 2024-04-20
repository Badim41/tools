import base64
import os
import requests
import time
import traceback
from PIL import Image

from discord_tools.chat_gpt_ai_api import ChatGPT_4_Account
from discord_tools.logs import Logs, Color
from discord_tools.astica_API import Astica_Describe_Params, Astica_API
from discord_tools.detect_mat import ban_words
from discord_tools.timer import Time_Count

logger = Logs(warnings=True)


def get_image_base64_encoding(file_path) -> str:
    with open(file_path, 'rb') as file:
        image_data = file.read()
    return base64.b64encode(image_data).decode('utf-8')


def vercel_API(image_path, proxies=None, timeout=60, *args, **kwargs):
    """
    return: caption, text
    speed: fast
    ???
    comment: очень хорошо распознаёт текст, не поддерживает запрос. Не подходит для модерации, часто превышается лимит
    proxy: нужен
    """
    url = "https://2txt.vercel.app/api/completion"

    payload = {"prompt": f"data:image/png;base64,{get_image_base64_encoding(image_path)}"}
    headers = {
        "authority": "2txt.vercel.app",
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }

    response = requests.request("POST", url, json=payload, headers=headers, proxies=proxies, timeout=timeout)

    if response.text == 'Rate limit exceeded':
        raise Exception('Превышен лимит')
    elif not response.text:
        raise Exception("Нет ответа. Статус:", response.status_code)
    # print(response.text)
    response_text = response.text
    text = ""
    for item in response_text.split("\n"):
        text += item.lstrip("0:\"").rstrip("\"")

    if "▲" in response_text:
        caption, text = text.split("▲")
        text = f"Caption: {caption}\nText: {text}"

    # Хотя бы так?
    for ban_word in ban_words:
        for word in text.split(" "):
            if (word.lower() + " ").startswith(ban_word):
                return True, text

    return None, text


def iodraw_API(image_path, prompt='What photo is this?', proxies=None, timeout=120, attempts=3, *args, **kwargs):
    """
    speed: slow
    Moderate = 13s-22s
    Describe = 9-16s
    comment: хорошо воспринимает запрос, хорошо находит даже рукописный текст
    """
    for i in range(attempts):
        response_text = "not inited response"
        try:
            url = "https://www.iodraw.com/ai/getChatText.json"

            payload = {
                "type": "image",
                "contents": [{"parts": [{"text": prompt}, {"inline_data": {
                    "mime_type": "image/png",
                    "data": get_image_base64_encoding(image_path)
                }}]}]
            }
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "ru,en;q=0.9",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

            response = requests.request("POST", url, json=payload, headers=headers, proxies=proxies, timeout=timeout)
            #
            response_text = response.text
            response_json = response.json()
            answer = response_json.get('content', None)
            if answer is None:
                return True, 'NSFW detected'
            else:
                return False, answer
        except Exception as e:
            logger.logging("Error in iodraw_API", e, response_text)
            time.sleep(30)

def chat_gpt_4_vision(image_path, prompt='What photo is this?', proxies=None, attempts=3, *args, **kwargs):
    """
    speed: fast
    Moderate = 11-13s (37s с получением ключа)
    Describe = 11-13s (37s с получением ключа)
    comment: Отличный. Не даёт описать плохую картинку
    """
    response_text = "not defined"
    timer = Time_Count()
    for i in range(attempts):
        try:
            account = ChatGPT_4_Account(proxies=proxies)
            result = account.ask_gpt(prompt=prompt, image_path=image_path)
            ban_results = ["I'm sorry", "Sorry, I can't", "I can't help", "I can't assist", "I can't provide"]
            print(timer.count_time(ignore_error=True))
            for ban_result in ban_results:
                if ban_result in result:
                    return True, result

            return False, result
        except Exception as e:
            if "Not found account" in str(e):
                return
            logger.logging("Error in chatGPT-4", e, response_text)
            time.sleep(30)

def astica_API(image_path, prompt="", isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None, *args,
               **kwargs):
    """
    speed: faster
    Describe / moderate = 5-7s (20s с получением ключа)
    comment: english only, не воспринимает запрос, плохо распознаёт текст
    """

    def get_object_info(data, result="", indent=0):
        for item in data:
            object_name = item['object']
            result += '  ' * indent + f'Object: {object_name}' + "\n"
            if 'parent' in item:
                result = get_object_info([item['parent']], result=result, indent=indent + 1)
        return result

    api = Astica_API(proxies=proxies)
    result = api.get_image_description(
        image_path,
        prompt=prompt,
        vision_params=Astica_Describe_Params.gpt_detailed)

    logger.logging("Response from server:", result, color=Color.GRAY)

    if result.get('caption_GPTS'):
        caption = result['caption_GPTS']
    else:
        text = ""
        if 'caption' in result and 'text' in result['caption']:
            text = "### caption:\n" + result['caption']['text'] + "\n\n"

        caption = text + "### objects:\n" + get_object_info(data=result['objects'])

    return (result['moderate']['isAdultContent'] and isAdultContent) or \
           (result['moderate']['isRacyContent'] and isRacyContent) or \
           (result['moderate']['isGoryContent'] and isGoryContent), caption


class Describers_API:
    Verstel = vercel_API
    Astica = astica_API
    Iodraw = iodraw_API
    ChatGPT4 = chat_gpt_4_vision


def detect_bad_image(image_path, isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None,
                     describers=None):
    if not os.path.isfile(image_path):
        raise Exception("Файл с изображением не найден.")

    lower_image_resolution(image_path)

    if describers is None:
        describers = [Describers_API.Iodraw, Describers_API.Astica, Describers_API.ChatGPT4, Describers_API.Verstel]

    for describer_method in describers:
        try:
            timer = Time_Count()
            nsfw, _ = describer_method(image_path, prompt='', isAdultContent=isAdultContent,
                                             isRacyContent=isRacyContent, isGoryContent=isGoryContent, proxies=proxies)
            # print("Detect bad image:", nsfw, _, str(describer_method), timer.count_time(ignore_error=True))
            return nsfw
        except Exception as e:
            logger.logging("wanr in detect bad image:", e, color=Color.GRAY)
    return None


def describe_image(image_path, prompt="", isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None,
                   describers=None):
    """
    return:
    NSFW:
        True = not safe
        False = safe
        None = не удалось получить
    description:
        type: str
        '-' = не удалось получить
    """
    if not os.path.isfile(image_path):
        raise Exception("Файл с изображением не найден.")

    logger.logging("describe image:", image_path, prompt, color=Color.GRAY)

    lower_image_resolution(image_path)

    if describers is None:
        describers = [Describers_API.ChatGPT4, Describers_API.Iodraw, Describers_API.Verstel, Describers_API.Astica]

    for describer_method in describers:
        try:
            # timer = Time_Count()
            nsfw, answer = describer_method(image_path, prompt=prompt, isAdultContent=isAdultContent,
                                       isRacyContent=isRacyContent, isGoryContent=isGoryContent, proxies=proxies)
            # print("Describe image:", nsfw, answer, str(describer_method), timer.count_time(ignore_error=True))
            return nsfw, answer
        except Exception as e:
            logger.logging("wand in detect bad image:", e, color=Color.GRAY)
    return None, "-"

def lower_image_resolution(image_path, max_pixels=1000000):
    img = Image.open(image_path)
    width, height = img.size
    current_pixels = width * height
    if current_pixels > max_pixels:
        new_width = int((max_pixels / current_pixels) ** 0.5 * width)
        new_height = int((max_pixels / current_pixels) ** 0.5 * height)
        img = img.resize((new_width, new_height))
        img.save(image_path)
