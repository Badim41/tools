import base64
import os
import requests
import time
import traceback
from PIL import Image
from msilib.schema import Media

from discord_tools.chat_gpt_ai_api import ChatGPT_4_Account
from discord_tools.logs import Logs, Color
from discord_tools.astica_API import Astica_Describe_Params, Astica_API
from discord_tools.detect_mat import ban_words
from discord_tools.reka_API import Reka_API, MediaType, NSFW_DETECTED_MESSAGE
from discord_tools.timer import Time_Count

logger = Logs(warnings=True)


def get_image_base64_encoding(file_path) -> str:
    with open(file_path, 'rb') as file:
        image_data = file.read()
    return base64.b64encode(image_data).decode('utf-8')


def vercel_API(image_path, proxies=None, timeout=60, attempts=2, *args, **kwargs):
    """
    return: caption, text
    speed: fast
    ???
    comment: очень хорошо распознаёт текст, не поддерживает запрос. Не подходит для модерации, часто превышается лимит
    proxy: нужен
    """
    response_text = "not defined"
    for i in range(attempts):
        try:
            if i == 2:
                proxies = {"http": "socks5://localhost:9050", "https": "socks5://localhost:9050"}
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
        except Exception as e:
            logger.logging("Error in vercel_API", e, response_text)
            time.sleep(3)


def iodraw_API(image_path, prompt='What photo is this?', proxies=None, timeout=120, attempts=2, *args, **kwargs):
    """
    speed: slow
    Moderate = 13s-22s
    Describe = 9-16s
    comment: хорошо воспринимает запрос, хорошо находит даже рукописный текст
    """

    for i in range(attempts):
        if i == 2:
            proxies = {"http": "socks5://localhost:9050", "https": "socks5://localhost:9050"}
        response_text = "not defined"
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
            time.sleep(3)


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
        if i == 3:
            proxies = {"http": "socks5://localhost:9050", "https": "socks5://localhost:9050"}
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
            time.sleep(3)


def astica_API(image_path, prompt="", isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None,
               attempts=2, *args,
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

    for i in range(attempts):
        if i == 2:
            proxies = {"http": "socks5://localhost:9050", "https": "socks5://localhost:9050"}
        try:
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
        except Exception as e:
            logger.logging("Error in astica_API", e)
            time.sleep(3)


def reka_recognize_image(image_path, reka_api, prompt="",
                         attempts=2, *args, **kwargs):
    """
    speed: slow
    Describe / moderate = 5-7s (20s с получением ключа)
    comment: english only, не воспринимает запрос, плохо распознаёт текст
    """
    if not reka_api:
        return None, None
    if not prompt:
        prompt = "Подробно опиши, что изображено на картинке"

    for i in range(attempts):
        try:
            result = reka_api.generate(file_path=image_path, media_type=MediaType.image,
                                       messages=[{"role": "user", "content": prompt}])

            logger.logging("Response from server:", result, color=Color.GRAY)

            if result == NSFW_DETECTED_MESSAGE:
                return True, result

            return False, result
        except Exception as e:
            logger.logging("Error in reka_API", e)
            time.sleep(3)


class Describers_API:
    Verstel = vercel_API
    Astica = astica_API
    Iodraw = iodraw_API
    ChatGPT4 = chat_gpt_4_vision
    Reka = reka_recognize_image


def detect_bad_image(image_path, isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None,
                     describers=None, reka_api=None):
    if not os.path.isfile(image_path):
        raise Exception("Файл с изображением не найден.")
        raise Exception("Файл с изображением не найден.")

    lower_image_resolution(image_path)

    if describers is None:
        describers = [Describers_API.Iodraw, Describers_API.Astica, Describers_API.Reka, Describers_API.ChatGPT4,
                      Describers_API.Verstel]

    for describer_method in describers:
        try:
            timer = Time_Count()
            nsfw, _ = describer_method(image_path, prompt='', isAdultContent=isAdultContent,
                                       isRacyContent=isRacyContent, isGoryContent=isGoryContent, proxies=proxies,
                                       reka_api=reka_api)
            print("Detect bad image:", nsfw, _, str(describer_method), timer.count_time(ignore_error=True))
            return nsfw
        except Exception as e:
            logger.logging("wanr in detect bad image:", e, color=Color.GRAY)
    return None


def describe_image(image_path, prompt="", isAdultContent=True, isRacyContent=True, isGoryContent=True, proxies=None,
                   describers=None, reka_api=None):
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
        describers = [Describers_API.ChatGPT4, Describers_API.Iodraw, Describers_API.Reka, Describers_API.Verstel,
                      Describers_API.Astica]

    for describer_method in describers:
        try:
            timer = Time_Count()
            nsfw, answer = describer_method(image_path, prompt=prompt, isAdultContent=isAdultContent,
                                            isRacyContent=isRacyContent, isGoryContent=isGoryContent, proxies=proxies,
                                            reka_api=reka_api)
            print("Describe image:", nsfw, answer, str(describer_method), timer.count_time(ignore_error=True))
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

app_session_reka = "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwidWF0IjoxNzE0NzczMTQzLCJpYXQiOjE3MTQwNzI0MzAsImV4cCI6MTcxNTAzMjM0M30..GKLezIt2EQ3PM4YK.f6TrbzetVtj2OmPe_eVhgpjitVwlkBOf9EoErbZamTwi456cUsZbQq6tm775c4zFnPq4qeMxWilROCPE17wGZ6ImwFKIM4NTP_H2bL2BVq4yBY74YL77ZzTdA02nIvItBSpNZgYf_KcjbtmBXsrYHSr_oACfgSb5iEQSFG65JX4BbdaPmpUlhE1X6KUh3qiDspjYvINA8Jklgls4cM-hJoOdBaCwyJcAxy2LDPAGOSjMAoGy3KS4pfZGFwvnDi7DUs9dncyUzjTVVxBjTr93o49khKz-lKwzJ9_iUow5ILh3h6ZaA8TbqDtWO_eH2jrtQuDk8x2yPcrKutpnQa7xvcMOepjkf7qBlquL0v6rKRdYfjWKVV2m2YzRwPsV-xHMDCDAN_16_NiE1p2whwTrNnGhKly4mDyaZQelBgRIRfOe-zEJALlUJrHGYyfRPx8DMRBRK-YsCGVrGkLtmUiUzh8n6mUiOdNGNIVWgu1OLpHWZFmjaTF6oND21eR5WKMx5xYVDZ6IQr_evCcT0tj9qHzF2_-6TDLGiyP_IcKaLL2f7VGpuY6-qTfqb-eqaRJKPcmtyTyr0NRTyD4CED5naCwoqPae7-V2AS3QYNSr4U6cuHdp8Da-ofUCHKIOO2KN4JOIh5o11WeHWZFti6C7UrT7QMr9bSw1gUHPiJCULX_79CFBSWxXo-B5LPHhCPpPVSbl6t1TS0lMtI9aL__lLWm11PgCB2LrJ23kCf9AgMWymsM8Y8eoE3jGscR5K2BusadrevSPoQcgVJG89hRYwepVBjcCussRPthnw1TKIv4U-oIwDWkEy6FSDgZCUg07fOgExM2fkhNAbUEa2LmNF0e8rA6Wf0bFa3y_r7bj3CFNkJ8Tpo4p9rHV23nniRLY2jXyuxJLB73iJv85tlLsT-2RgzxnwIxp6k2MSCISXqT7lb0b8JNHQmqF8_ILAgiEQsPwKa5XVd-xbA69yVXhI5zc8mSk7mp5mOIWR6s66l570MrWjDkxkWJbi1whzasCj9eQmSGvNd0o1JcGhos2TGm7R67MmGNDAllMctqZ1pFbDshJQpeP8tmpdwTrl_F8-ntrjNZW54zZ61Cei0IfZvQ8ZlluX0DKDAG7jBuWO28uR28Nf53209WSSttnt77_ynhjBxtRyhzEgzmHgNV8_jsAydzCM-F3sXi-jQ3m0u0ObLglJAf6sDL18w6vOemhb-43Bg98t8sYzx7xqEsDDKPmnt3GhEkvVanbYpghbR8TVTc80IMkH0OiDsjpa_bPdmjMwm0dznzhBPS_vpexMrEE1pcQhU84bT4DqWWmdeN461JfVg0ceejQAcl3-J5tC1gy9-80ARTz4DLEWgR3WbwTvwJ2LM-1I9iK7ZrwcWw-3nbB4wAFZ75gluHCsZ6fH3vHKWWsjKA4a_iYUcjITbljlXcAxcoc849Vt-ESIZb8rSBfSetVPm1RHEEKjyHVIDW8ex5g5pjd7woHgbrDR7nde8qXAgbwwdvc__gLxlFw7ZeplXGIaKROwcMVEFOYNcFRWmEgFnZkHhzevUnBWYoKxELWT2fJKByeEdtOnbqJtq1NSbsrBjZ1HW4r1j1e-KW_O5rq802-ntJsqSfB0bN4AcpIjE6RZKcecF_Jr3C7e5c51UuRjRY3Be-gkuXFtA3P_GZ-R4FKLDJYSnxErDqgxmhukYYcAXDsaXVqSMVz-Rm8uGLdBNMv4SZE60CP1Atn7I-CBS47EtgwZ6TwZD_fleibzqE8xcxBGbGLcwQlMXrLYAqtMsLSzmUwn1ZZmKGDNqiYhHxqG4-1m5gII4h2VpVqc6_tHYwKPh29UXv1OZ7pE-Wia3bz3z3cN4VKUFmNfi-bTCiFBtbzGWSExh5xUXv4dvrekXMTul9wVyj1vsIWFbGTtsf166ZwulTGl81W2L6PKg5fusxjU_4uLBhOtJHX_Svv0UAAEEYAgzS2o7xL9rNMy4LcZxFlcqyD_lBSu0avK5fxXukPnLaoCgDo6uLnF9T2jaQFbLroJs_fqSIg0-4iuM-wXCf-Hkdv8DYvzlG65EXnAESPbSFKs-JRvSEGHgp4EUeRlsoOsB67WxDJcCy1_z-bzl3tO9t2EtUYz1hVUebeHacHjfovKiQmdo_x9jTz53RIw027_C2ZG3q4H7Y273R0Ayoxn2zmLzkpa_-YIDO-l1_m_TpxKleWdh642k1A3ndLtGm7fU5FzSNY44hRrVFCEFARnChwkCe5XnQfMS0H45OLeqcqoE80vDiGMJHdQufJ9KLVF_2TCdgaw1p9ff4KYNUv6s81bxAewiALxhMqydf8HgCoGs0saGibfdgZufc9ahjvtHIEmAaCPsGlgsoigXEP7zOCbPW9YEuWLlOArzdJ49bEfQQqmqDCIbAoNefKKwqbpmgSGQYd1A-iivKWAjyX-jT1-XZebz-36IcLayaoLAzqCMJ7kmaCCaHx8TXBYn17Z8mOW0F77vu0BdMrC7JU1yAJY3M7DpuB1D5VHSs5v-PM5IhqPxJpZN14B488pqOWxqyIdppHcI44dll5aZLpHBZJsONPeKacyxKnmnvzQBTcXXuQx_NRxzIIn0OsQ0RWrAC7ivG0RKv8-jd6Zf8aXslwqolpbJCgkLOiaPfePmU43__nOv6IgFd-62gjUDvNlK0ZvWA3zG3JsQW2wn5bcAAQg1s15XqxTizl-k7WGIuAl-XZuJixXNH8qeqcd3FNvW-26pxg0huVnxtinqsbis3ChYNyTgaX5ERE0_G7gOzfk4gh5nLuKj1P8F-X4c9QiljpLdhhQVxlOI3hoYfVOAcUrKjrc8RZG6xkCpcYKDHbC9rugUgsdOdmZeHX8CO2dDERKTJD9XovAvVFMTx9KoYA9TKb2-3w0celzDMq87T8jR8nlYG5fCCveHR6tFmZan96eRSDef7Z66e_-Zpy5r3YczrMmnYp3QdZr9hd4RiBruzdytQlMRIJ2ynAME2ih0ceKJu8_2Wn7ZYxDyEy2sz8UDq2dw4l6MPgFsCnkgiaRpancmz5M2SWgm0YEq6cCGQU3caxp8glowosgEVBjdSy5RQ1ku9a0O_Lvl6N6TCJxb0iiSvdRSx53rpZl2B6GNO54NmcFQLIGSJgEbUlQ_OBrCh_-EHoouwS6NmupDJi4snFar0D8bV-S7byA_pz9KqQhAJNCs_yOran5WXILb-v4JbTqC3lDOxV4yXBKycG.7S4CbtpeAiSR3w7mYKxuMQ"

api = Reka_API(app_session=app_session_reka)
print(describe_image(image_path=r"C:\Users\as280\Downloads\NSWF_DETECTION_FILTER.png", describers=[Describers_API.Reka], reka_api=api))