import json
import re
import requests
import time

import cohere
from cohere import ClassifyExample

from discord_tools.logs import Logs, Color
from discord_tools.sql_db import get_database, set_database_not_async as set_database
from discord_tools.timer import Time_Count

logger = Logs(warnings=True)


class Response_Example:
    image_recognize = "image_recognize"
    internet_access = "internet_access"
    image_generate = "image_generate"
    image_change = "image_change"
    else_req = "else"


class Coral_API:
    def __init__(self, api_key=None, email=None, password=None, proxies=None):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        # self.api_key = self.get_api_key()
        self.proxies = proxies
        self.email = email
        self.password = password
        # self.access_token, self.user_id = self.get_access_token_on_start()
        if not api_key and (email and password):
            self.access_token, self.user_id = self.get_access_token_on_start()
            self.api_keys = [self.get_api_key()]
        elif api_key:
            if isinstance(api_key, list):
                self.api_keys = api_key
            elif isinstance(api_key, str):
                self.api_keys = [api_key]
            else:
                raise Exception("API KEY должен быть str или list")
        else:
            raise Exception("Нет способа получения ключа")

    def login(self):
        import requests

        url = "https://production.api.os.cohere.ai/rpc/BlobheartAPI/AuthV2"

        payload = {
            "email": self.email,
            "password": self.password
        }

        headers = {
            "authority": "production.api.os.cohere.ai",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "authorization": "",
            "content-type": "application/json",
            "request-source": "playground",
            "user-agent": self.user_agent
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

        response_json = response.json()

        access_token = response_json['bearerTokens']['accessToken']
        user_id = response_json['bearerTokens']['userID']

        set_database("default", "coral_access_token", access_token)
        set_database("default", "coral_user_id", user_id)

        logger.logging("Logged in coral!", color=Color.PURPLE)

        return access_token, user_id

    def get_access_token_on_start(self):
        access_token = get_database("default", "coral_access_token")
        user_id = get_database("default", "coral_user_id")
        if access_token == "None" or user_id == "None":
            return self.login()
        else:
            return access_token, user_id

    def get_api_key(self):
        url = "https://production.api.os.cohere.ai/rpc/BlobheartAPI/GetOrCreateDefaultAPIKey"

        payload = {}
        headers = {
            "authority": "production.api.os.cohere.ai",
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
            "origin": "https://coral.cohere.com",
            "referer": "https://coral.cohere.com/",
            "request-source": "coral",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": self.user_agent
        }

        response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)

        if response.status_code == 401:
            logger.logging("Ошибка с авторизацией!", color=Color.RED)
            self.access_token, self.user_id = self.login()
            return self.get_api_key()

        return response.json()['rawKey']

    def generate(self, messages, gpt_role="Ты полезный ассистент и даёшь только полезную информацию", delay_for_gpt=1,
                 temperature=0.3,
                 model="command-r-plus", web_access=False, error=0):
        changed_messages = messages
        if not self.api_keys:
            logger.logging("coral_API: No keys")
            time.sleep(delay_for_gpt)
            return

        response_text = "[not got response]"
        response_json = "[no json]"
        try:

            transformed_messages = []
            prompt = None

            if web_access:
                connectors = [{"id": "web-search"}]
            else:
                connectors = []

            for i, msg in enumerate(changed_messages):
                if 'system' in msg['role']:
                    continue
                role = "User" if msg['role'] == "user" else "Chatbot"
                message = msg['content']
                if i == len(changed_messages) - 1:
                    prompt = message
                else:
                    transformed_messages.append({"role": role, "message": message})

            if not prompt:
                raise Exception("Неправильный формат сообщений!")

            url = "https://api.cohere.ai/v1/chat"

            payload = {
                "message": prompt,
                "temperature": temperature,
                "chat_history": transformed_messages,
                "model": model,
                "preamble": gpt_role,
                "connectors": connectors,
                "stream": False,
                "prompt_truncation": "AUTO"
            }

            headers = {
                "authority": "api.cohere.ai",
                "accept": "*/*",
                "accept-language": "ru,en;q=0.9",
                "authorization": f"Bearer {self.api_keys[0]}",
                "content-type": "application/json; charset=utf-8",
                "user-agent": self.user_agent
            }

            response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)
            if response.status_code == 429:
                if not error == 5 and self.api_keys:
                    self.api_keys = self.api_keys[1:]
                    return self.generate(messages=messages, gpt_role=gpt_role, delay_for_gpt=delay_for_gpt,
                                         temperature=temperature, model=model, web_access=web_access, error=error + 1)
                else:
                    raise Exception(f"Было опробовано {error} ключей, но ни один не подошёл. Прервано.")

            response_text = response.text
            response_json = response.json()
            return response_json['text']
        except Exception as e:
            logger.logging("Error in coral_API:", e, response_json, response_text, color=Color.RED)
            time.sleep(delay_for_gpt)

    def classify_request(self, inputs, error=0):
        url = "https://api.cohere.ai/v1/classify"
        examples = [
            ClassifyExample(text="Покажи мне погоду в Париже на следующей неделе",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Нарисуй красивый закат над океаном", label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Можешь изменить цвет неба на этой картинке на фиолетовый? <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Какие новые фильмы вышли в этом месяце?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай изображение поля с ветряными мельницами",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Переделай это фото, чтобы на нем была зима <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Не могли бы вы помочь мне с поиском информации о субсидиях для малого бизнеса?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Как тебя зовут?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сгенерируй изображение щенка играющего с клубком ниток",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Можешь ли ты сделать этот пейзаж более ярким? <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Какие новые книги были опубликованы недавно вашим любимым автором?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Расскажи мне анекдот", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Создай изображение красивого современного интерьера",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какой прогноз погоды на завтра в Нью-Йорке?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Сделай эту картину более яркой и насыщенной <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Как называется столица Бразилии?", label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Нарисуй портрет молодой женщины с длинными вьющимися волосами",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Переделай это фото, чтобы на нем был вечер <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто был 16-м президентом США?", label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Можешь объяснить, как работает блокчейн?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сгенерируй изображение футуристического города будущего",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Кто выиграл последние президентские выборы в России?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Сделай эту картину более темной и таинственной <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Чем отличаются ядовитые и неядовитые змеи?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Можешь создать абстрактный рисунок в стиле кубизма?",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Что такое искусственный интеллект?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какой курс евро к доллару сегодня?", label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Нарисуй красивый водопад в тропическом лесу",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Измени цвет волос на этом портрете на рыжий <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто написал роман 'Война и мир'?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что такое черная дыра?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сгенерируй концепт-арт фэнтезийного замка",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какие симптомы свидетельствуют о гриппе?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Сделай этот пейзаж более туманным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто изобрел телефон?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Играешь ли ты в видеоигры?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Создай изображение космического корабля, путешествующего сквозь галактики",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какие известные достопримечательности есть в Париже?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Сделай эту картину более яркой и солнечной <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто был первым человеком, ступившим на Луну?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что означает аббревиатура 'ИИ'?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Нарисуй изображение милого маленького робота",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какая самая высокая гора в мире?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сделай этот пейзаж более живым и реалистичным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто написал 'Маленького принца'?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что такое метавселенная?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сгенерируй изображение красочного подводного мира с коралловыми рифами",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="В каком году была основана компания Apple?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Измени фон на этом изображении на черный <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто изобрел лампочку?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что такое искусственный интеллект?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Можешь создать изображение средневекового рыцаря на боевом коне?",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какие главные достопримечательности есть в Риме?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Сделай эту картину более мрачной и пугающей <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="В каком году была открыта периодическая система химических элементов?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Объясни, что такое блокчейн простыми словами",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Создай изображение роскошной современной ванной комнаты",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какие известные музеи есть в Вашингтоне?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Измени цвет неба на этой картине на оранжевый <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто является автором книги 'Преступление и наказание'?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что такое криптовалюта?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Нарисуй фэнтезийный пейзаж с драконом", label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какая самая длинная река в мире?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сделай этот портрет более реалистичным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто был первым президентом США?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Как работает технология распознавания лиц?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сгенерируй изображение футуристического города под куполом",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какова средняя продолжительность жизни в Японии?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Сделай эту картину более теплой и солнечной <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Кто написал роман 'На Западном фронте без перемен'?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что такое квантовые вычисления?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Создай изображение роскошного люкса в отеле",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Какое растение считается национальным цветком Японии?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Нарисуй симпатичного маленького дракона, играющего с бабочкой",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай это селфи более ярким и насыщенным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое большой взрыв?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какой была самая высокая когда-либо зарегистрированная температура на Земле?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай концептуальное изображение космического корабля, приземляющегося на Марсе",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Измени фон на этом портрете на размытый <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что означает выражение 'цифровая трансформация'?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Кто написал известный роман 'Властелин колец'?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Сгенерируй изображение уютной кофейни в Париже",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай этот пейзаж более туманным и таинственным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Объясните разницу между ИИ, машинным обучением и глубоким обучением",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какая самая маленькая страна в мире по площади?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай сюрреалистическое изображение, вдохновленное работами Сальвадора Дали",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Измени цвет волос на этом портрете на синий <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Как работает технология блокчейн?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="В каком году был изобретен Интернет?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Нарисуй викторианский сад с павлинами", label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай это изображение более ярким и контрастным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое теория относительности?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какой самый популярный национальный парк в США?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай изображение русалки, плавающей в коралловых рифах",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Измени освещение на этом изображении, сделав его более драматичным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое черная дыра?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="В каком году был основан Оксфордский университет?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Нарисуй концептуальное изображение инопланетных пейзажей",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай этот портрет более четким и детализированным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Как работают солнечные батареи?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Кто был первым человеком, покорившим Эверест?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай иллюстрацию фантастических воздушных кораблей в небе",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай небо на этом пейзаже более розовым и романтичным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое нанотехнологии?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какая самая длинная пещера в мире?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Нарисуй эльфа, путешествующего по волшебному лесу",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Добавь больше облаков на это изображение неба <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое квантовая физика?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="В какой стране находится известный водопад Виктория?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай концептуальное изображение космического корабля на орбите инопланетного мира",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Измени цвет моря на этом пейзаже на пурпурный <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое возобновляемые источники энергии?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Кто был первым человеком, полетевшим в космос?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Нарисуй красочный городской пейзаж в стиле импрессионизма",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай этот портрет более стилизованным и абстрактным <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что такое большие данные?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какова высота самого высокого здания в мире?",
                            label=Response_Example.internet_access).dict(),
            ClassifyExample(text="Создай концептуальное изображение гигантского древнего механизма",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Добавь больше облаков на это изображение неба <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Объясните, как работает технология 5G", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какая страна является родиной пиццы?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Нарисуй красивый осенний лес с падающими листьями",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Измени фон на этом портрете на сине-зеленый градиент <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Что означает термин 'Интернет вещей'?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Какова самая длинная река во Франции?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Создай изображение городского пейзажа с футуристическими зданиями",
                            label=Response_Example.image_generate).dict(),
            ClassifyExample(text="Сделай этот пейзаж более туманным и мистическим <image>",
                            label=Response_Example.image_change).dict(),
            ClassifyExample(text="Как работают квантовые компьютеры?", label=Response_Example.else_req).dict(),
            ClassifyExample(text="Кто был первым премьер-министром Великобритании?",
                            label=Response_Example.else_req).dict(),
            ClassifyExample(text="Что на этом изображении? <image>", label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что изображено на этой картинке? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Можете описать, что вы видите на этом фото? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Распознайте объекты на данном изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте содержимое этой фотографии <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что за предмет/объект/сцена на этом снимке? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте, что изображено здесь <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Дайте описание того, что вы видите на картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте и распознайте содержание изображения <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что это может быть? Опишите эту фотографию <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расскажите, что вы видите на этом изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите предметы и объекты, присутствующие на картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Распознайте и назовите все объекты на этом снимке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что изображено на данной фотографии? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте содержимое изображения и перечислите заметные элементы <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте основные объекты и действия на этой картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите визуальную сцену, представленную на данном изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что это за предмет/объект/существо на фотографии? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Дайте подробное описание содержимого картинки <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расскажите, что вы видите происходящим на этом снимке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте изображение и перечислите все распознанные объекты <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте людей, животных, предметы на данной фотографии <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите визуальный контекст, представленный на картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что это за место/локация, изображенная на снимке? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Дайте детальное описание изображения, включая мельчайшие детали <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расскажите, что вы видите происходящим на переднем и заднем планах <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте картинку и назовите основные объекты, цвета и формы <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что это за предмет и для чего он может использоваться? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите действие/событие, запечатленное на фотографии <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте породу животного на этом изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расскажите, что происходит на картинке и что могло произойти до/после <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите настроение и эмоции, которые передает данное изображение <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Назовите объекты, которые вы распознаете на этой фотографии <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Дайте интерпретацию содержания картинки и ее возможного значения <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что вы видите на переднем плане данного изображения? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте цветовую гамму и опишите доминирующие цвета <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Какие предметы вы можете опознать на заднем плане? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расскажите, какая деятельность происходит на фотографии <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите настроение и обстановку, запечатленные на снимке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте людей/персонажей, если таковые присутствуют <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что могло произойти перед событиями, показанными на картинке? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируйте символику и знаки, если они есть на изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите текстуры и материалы основных объектов <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Назовите стиль и жанр данного изображения, если применимо <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Какие чувства и эмоции вызывает у вас эта картинка? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте марку/модель автомобиля на фотографии <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите условия освещения на данном изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Распознайте исторический период или эпоху, представленную на картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Какие художественные техники и приемы вы видите в этом изображении? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Перечислите все распознаваемые на снимке здания и архитектурные элементы <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите фон и окружающую среду, в которой происходит действие <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Какие особенности на изображении позволяют предположить его дату создания? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Определите страну/регион, типичные для показанных на картинке элементов <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Что вы можете сказать о возможном назначении объектов на данном снимке? <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Опишите геометрические формы и узоры в композиции изображения <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Идентифицируйте марку/модель часов на этом изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расскажите, какие действия выполняются людьми/персонажами на картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Дай ответ на следующий вопрос: <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Ответь на вопросы, указанные на этом изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Прочитай и ответь на текст, приведенный на картинке <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Распознай вопрос на данном изображении и дай на него ответ <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Изучи содержимое изображения и ответь на представленные там вопросы <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Расшифруй текст на этой фотографии и ответь на него <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Прочитай написанное на этой картинке и дай соответствующий ответ <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Обработай информацию, изображенную на картинке, и ответь на нее <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Прокомментируй вопросы, заданные на представленном изображении <image>",
                            label=Response_Example.image_recognize).dict(),
            ClassifyExample(text="Проанализируй текст на данной фотографии и предоставь ответ <image>",
                            label=Response_Example.image_recognize).dict()]

        if isinstance(inputs, str):
            inputs = [inputs]

        payload = {
            "inputs": inputs,
            "examples": examples
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_keys[0]}"
        }

        response = requests.post(url, json=payload, headers=headers, proxies=self.proxies)

        if response.status_code == 429:
            if not error == 5 and self.api_keys:
                self.api_keys = self.api_keys[1:]
                return self.classify_request(inputs=inputs, error=error + 1)
            else:
                raise Exception(f"Было опробовано {error} ключей, но ни один не подошёл. Прервано.")

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def safe_summorize(self, text, big_text):
        def split_text_into_sentences(text):
            sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s')
            sentences = sentence_endings.split(text)
            sentences = [s.strip() for s in sentences]
            return sentences

        def split_into_chunks(text, chunk_size=8000):
            sentences = split_text_into_sentences(text)
            chunks_sentences = []
            current_chunk = ''
            current_chunk_length = 0

            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= chunk_size:  # Add 1 for space
                    if current_chunk:
                        current_chunk += ' ' + sentence
                    else:
                        current_chunk = sentence
                    current_chunk_length += len(sentence) + 1
                else:
                    chunks_sentences.append(current_chunk)
                    current_chunk = sentence
                    current_chunk_length = len(sentence)

            if current_chunk:  # Append remaining sentences if any
                chunks_sentences.append(current_chunk)

            return chunks_sentences

        chunks = split_into_chunks(big_text)

        url = "https://api.cohere.ai/v1/rerank"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_keys[0]}"
        }

        for chunk in chunks:
            url = "https://api.cohere.ai/v1/chat"

            payload = {
                "message": text,
                "model": "command-r-plus",
                "connectors": [],
                "stream": False,
                "documents": [{"title": "Stream TXT record", "text": chunk}],
                "prompt_truncation": "AUTO"
            }

            headers = {
                "authority": "api.cohere.ai",
                "accept": "*/*",
                "accept-language": "ru,en;q=0.9",
                "authorization": f"Bearer {self.api_keys[0]}",
                "content-type": "application/json; charset=utf-8",
                "user-agent": self.user_agent
            }

            response = requests.request("POST", url, json=payload, headers=headers, proxies=self.proxies)
            print(response.status_code)
            response_text = response.text
            response_json = response.json()
            print(response_json['text'])


prompt_streamer = """# Введение
Этот текст - текстовая расшифровка стрима стримера Faradey (Фарадей)


# Задача
Сделай датасет, который будет содержать вопросы и ответы данного стримера с чатом.
Сделай максимально большое количество вопросов и ответов из файла.
Выводи в формате JSON:
[
{
"Q":"вопрос",
"A":"ответ"
}
...
]


# Примеры
Q: Как относишься к косплеерам?
A: Нормально."""

if __name__ == "__main__":
    proxy = "socks5://localhost:5051"  # Здесь указываем порт 5051, как в вашей команде SSH

    proxies = {
        'http': proxy,
        'https': proxy
    }

    timer = Time_Count()

    api = Coral_API(proxies=proxies, api_key="1uiEYiGMMqUcueHDUGw4XWI8kEEtsC5HMTIo5nya")

    file_path = r'C:\Users\as280\Downloads\4Voice.txt'
    with open(file_path, "r", encoding="utf-8") as reader:
        content = reader.read()

    api.safe_summorize(prompt_streamer, content)
    input()
    test_json = api.classify_request("Измени изображение <image>")
    print(test_json["classifications"][0]["prediction"], timer.count_time(ignore_error=True))
    print(test_json)
