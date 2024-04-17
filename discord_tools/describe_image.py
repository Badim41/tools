import base64
import os
import requests
import traceback

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


def iodraw_API(image_path, prompt='What photo is this?', proxies=None, timeout=60, *args, **kwargs):
    """
    speed: slow
    Moderate = 13s-22s
    Describe = 9-16s
    comment: хорошо воспринимает запрос, хорошо находит даже рукописный текст
    """
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
        # print(response.text)

        response_json = response.json()
        answer = response_json.get('content', None)
        if answer is None:
            return True, 'NSFW detected'
        else:
            return False, answer
    except Exception as e:
        print("Error in iodraw_API", e)
        return None, '-'


def astica_API(image_path, prompt="", isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None, *args,
               **kwargs):
    """
    speed: fast
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

    astica_api = Astica_API(proxies=proxies)
    result = astica_api.get_image_description(
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


def detect_bad_image(image_path, isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None,
                     describers=None):

    if describers is None:
        describers = [Describers_API.Iodraw, Describers_API.Astica, Describers_API.Verstel]

    for describer_method in describers:
        try:
            timer = Time_Count()
            nsfw, _ = describer_method(image_path, prompt='', isAdultContent=isAdultContent,
                                             isRacyContent=isRacyContent, isGoryContent=isGoryContent, proxies=proxies)
            # print("Detect bad image:", nsfw, _, str(describer_method), timer.count_time(ignore_error=True))
            return nsfw
        except Exception as e:
            print("wanr in detect bad image:", e)
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

    if describers is None:
        describers = [Describers_API.Iodraw, Describers_API.Verstel, Describers_API.Astica]

    for describer_method in describers:
        try:
            # timer = Time_Count()
            nsfw, answer = describer_method(image_path, prompt='', isAdultContent=isAdultContent,
                                       isRacyContent=isRacyContent, isGoryContent=isGoryContent, proxies=proxies)
            # print("Describe image:", nsfw, answer, str(describer_method), timer.count_time(ignore_error=True))
            return nsfw, answer
        except Exception as e:
            print("wand in detect bad image:", e)
    return None, "-"

