import base64
import json
import os
import random
import re
import requests
import shutil
import time
from requests.utils import dict_from_cookiejar

from discord_tools.sql_db import get_database, set_database_not_async as set_database
from discord_tools.logs import Logs, Color

logger = Logs(warnings=True)


class Astica_Describe_Params:
    describe = "describe"
    objects = "objects"
    categories = "categories"
    moderate = "moderate"
    tags = "tags"
    brands = "brands"
    color = "color"
    faces = "faces"
    celebrities = "celebrities"
    landmarks = "landmarks"
    gpt = "gpt"  # caption_GPTS
    gpt_detailed = "gpt_detailed"  # Slower


class GenerateQuality:
    high = 'high'
    standard = 'standard'
    fast = 'fast'
    faster = 'faster'


class Astica_Response_Example:
    describe = {
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 2.3449999999999998
        },
        "status": "success",
        "caption": {
            "text": "a close-up of a computer screen",
            "confidence": 0.7
        },
        "metadata": {
            "width": 250,
            "height": 250
        },
        "celebrities": [],
        "landmarks": []
    }

    objects = {
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        },
        "status": "success",
        "objects": [],
        "metadata": {
            "width": 250,
            "height": 250
        },
        "celebrities": [],
        "landmarks": []
    }

    categories = {
        "status": "success",
        "categories": [
            {
                "name": "others_",
                "score": 0.0078125
            },
            {
                "name": "outdoor_",
                "score": 0.01171875
            },
            {
                "name": "text_sign",
                "score": 0.84375
            }
        ],
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }

    moderate = {
        "status": "success",
        "moderate": {
            "isAdultContent": False,
            "isRacyContent": False,
            "isGoryContent": False,
            "adultScore": 0.0022407304495573044,
            "racyScore": 0.003612220985814929,
            "goreScore": 0.000581094529479742
        },
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }
    tags = {
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        },
        "status": "success",
        "tags": [
            {
                "name": "screenshot",
                "confidence": 0.94
            },
            {
                "name": "graphic design",
                "confidence": 0.9
            },
            {
                "name": "graphics",
                "confidence": 0.89
            },
            {
                "name": "colorfulness",
                "confidence": 0.88
            },
            {
                "name": "rectangle",
                "confidence": 0.87
            },
            {
                "name": "text",
                "confidence": 0.84
            },
            {
                "name": "design",
                "confidence": 0.52
            }
        ],
        "metadata": {
            "width": 250,
            "height": 250
        },
        "celebrities": [],
        "landmarks": []
    }
    brands = {
        "status": "success",
        "brands": [],
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }

    color = {
        "status": "success",
        "colors": {
            "dominantColorForeground": "White",
            "dominantColorBackground": "Blue",
            "dominantColors": [
                "White",
                "Blue"
            ],
            "accentColor": "0132CA",
            "isBwImg": False,
            "isBWImg": False
        },
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }

    faces = {
        "status": "success",
        "faces": [],
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }

    celebrities = {
        "status": "success",
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }

    landmarks = {
        "status": "success",
        "celebrities": [],
        "landmarks": [],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 1.65
        }
    }
    gpt = {
        "readResult": {
            "stringIndexType": "TextElements",
            "content": "8K",
            "pages": {}
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 31.211699999999997
        },
        "status": "success",
        "caption": {
            "text": "a close-up of a computer screen",
            "confidence": 0.7
        },
        "caption_list": [
            {
                "text": "a close-up of a computer screen",
                "confidence": 0.7,
                "rectangle": {
                    "x": 0,
                    "y": 0,
                    "w": 250,
                    "h": 250
                }
            },
            {
                "text": "a white arrow with black text",
                "confidence": 0.68,
                "rectangle": {
                    "x": 46,
                    "y": 0,
                    "w": 177,
                    "h": 243
                }
            },
            {
                "text": "a number and k on a white background",
                "confidence": 0.7,
                "rectangle": {
                    "x": 51,
                    "y": 0,
                    "w": 149,
                    "h": 68
                }
            },
            {
                "text": "a white arrow pointing to a colorful background",
                "confidence": 0.68,
                "rectangle": {
                    "x": 55,
                    "y": 64,
                    "w": 160,
                    "h": 131
                }
            },
            {
                "text": "a green and white square with a black corner",
                "confidence": 0.66,
                "rectangle": {
                    "x": 120,
                    "y": 168,
                    "w": 78,
                    "h": 78
                }
            }
        ],
        "objects": [],
        "tags": [
            {
                "name": "screenshot",
                "confidence": 0.94
            },
            {
                "name": "graphic design",
                "confidence": 0.9
            },
            {
                "name": "graphics",
                "confidence": 0.89
            },
            {
                "name": "colorfulness",
                "confidence": 0.88
            },
            {
                "name": "rectangle",
                "confidence": 0.87
            },
            {
                "name": "text",
                "confidence": 0.84
            },
            {
                "name": "design",
                "confidence": 0.52
            }
        ],
        "people_list": [
            {
                "confidence": 0,
                "rectangle": {
                    "x": 1,
                    "y": 0,
                    "w": 209,
                    "h": 70
                }
            },
            {
                "confidence": 0,
                "rectangle": {
                    "x": 0,
                    "y": 1,
                    "w": 55,
                    "h": 240
                }
            },
            {
                "confidence": 0,
                "rectangle": {
                    "x": 0,
                    "y": 0,
                    "w": 227,
                    "h": 249
                }
            },
            {
                "confidence": 0,
                "rectangle": {
                    "x": 0,
                    "y": 0,
                    "w": 54,
                    "h": 69
                }
            }
        ],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "categories": [
            {
                "name": "others_",
                "score": 0.0078125
            },
            {
                "name": "outdoor_",
                "score": 0.01171875,
                "detail": {
                    "landmarks": []
                }
            },
            {
                "name": "text_sign",
                "score": 0.84375
            }
        ],
        "moderate": {
            "isAdultContent": False,
            "isRacyContent": False,
            "isGoryContent": False,
            "adultScore": 0.0022407304495573044,
            "racyScore": 0.003612220985814929,
            "goreScore": 0.000581094529479742
        },
        "faces": [],
        "brands": [],
        "colors": {
            "dominantColorForeground": "White",
            "dominantColorBackground": "Blue",
            "dominantColors": [
                "White",
                "Blue"
            ],
            "accentColor": "0132CA",
            "isBwImg": False,
            "isBWImg": False
        },
        "celebrities": [],
        "landmarks": [],
        "imageType": {
            "clipArtType": 0,
            "lineDrawingType": 0
        },
        "ocr": {
            "text": "8K",
            "writing_style": [],
            "pages": [
                {
                    "page_number": {
                        "height": 250,
                        "width": 250,
                        "angle": 0.3283,
                        "pageNumber": 1,
                        "words": [
                            {
                                "content": "8K",
                                "boundingBox": [
                                    82,
                                    6,
                                    150,
                                    6,
                                    149,
                                    64,
                                    82,
                                    64
                                ],
                                "confidence": 0.993,
                                "span": {
                                    "offset": 0,
                                    "length": 2
                                }
                            }
                        ],
                        "spans": [
                            {
                                "offset": 0,
                                "length": 2
                            }
                        ],
                        "lines": [
                            {
                                "content": "8K",
                                "boundingBox": [
                                    82,
                                    6,
                                    166,
                                    8,
                                    164,
                                    63,
                                    83,
                                    64
                                ],
                                "spans": [
                                    {
                                        "offset": 0,
                                        "length": 2
                                    }
                                ]
                            }
                        ]
                    },
                    "page_height": 250,
                    "page_width": 250,
                    "page_angle": 0.3283,
                    "page_text": [
                        {
                            "text": "8K",
                            "bbox": {
                                "x": 82,
                                "y": 6,
                                "w": 68,
                                "h": 0
                            },
                            "wordShape": "rectangle"
                        }
                    ]
                }
            ]
        },
        "caption_GPTS": "A close-up image of a computer screen is shown, with a dominant foreground color of white and a dominant background color of blue. The screen displays a white arrow with black text, along with a number and the letter \"K\" on a white background. A white arrow is also seen pointing to a colorful background. Additionally, there is a green and white square with a black corner visible on the screen. The image appears to be a screenshot or graphic design, showcasing elements of colorfulness and rectangles. The overall design is clean and modern, with a focus on text and graphics. The image is not explicit or gory in any way, making it suitable for a wide audience.",
        "GPT_level": 0
    }
    gpt_detailed = {
        "readResult": {
            "stringIndexType": "TextElements",
            "content": "8K",
            "pages": {}
        },
        "astica": {
            "request": "vision",
            "requestType": "analyze",
            "modelVersion": "2.1",
            "api_qty": 37.2917
        },
        "status": "success",
        "caption": {
            "text": "a close-up of a computer screen",
            "confidence": 0.7
        },
        "caption_list": [
            {
                "text": "a close-up of a computer screen",
                "confidence": 0.7,
                "rectangle": {
                    "x": 0,
                    "y": 0,
                    "w": 250,
                    "h": 250
                }
            },
            {
                "text": "a white arrow with black text",
                "confidence": 0.68,
                "rectangle": {
                    "x": 46,
                    "y": 0,
                    "w": 177,
                    "h": 243
                }
            },
            {
                "text": "a number and k on a white background",
                "confidence": 0.7,
                "rectangle": {
                    "x": 51,
                    "y": 0,
                    "w": 149,
                    "h": 68
                }
            },
            {
                "text": "a white arrow pointing to a colorful background",
                "confidence": 0.68,
                "rectangle": {
                    "x": 55,
                    "y": 64,
                    "w": 160,
                    "h": 131
                }
            },
            {
                "text": "a green and white square with a black corner",
                "confidence": 0.66,
                "rectangle": {
                    "x": 120,
                    "y": 168,
                    "w": 78,
                    "h": 78
                }
            }
        ],
        "objects": [],
        "tags": [
            {
                "name": "screenshot",
                "confidence": 0.94
            },
            {
                "name": "graphic design",
                "confidence": 0.9
            },
            {
                "name": "graphics",
                "confidence": 0.89
            },
            {
                "name": "colorfulness",
                "confidence": 0.88
            },
            {
                "name": "rectangle",
                "confidence": 0.87
            },
            {
                "name": "text",
                "confidence": 0.84
            },
            {
                "name": "design",
                "confidence": 0.52
            }
        ],
        "people_list": [
            {
                "confidence": 0,
                "rectangle": {
                    "x": 1,
                    "y": 0,
                    "w": 209,
                    "h": 70
                }
            },
            {
                "confidence": 0,
                "rectangle": {
                    "x": 0,
                    "y": 1,
                    "w": 55,
                    "h": 240
                }
            },
            {
                "confidence": 0,
                "rectangle": {
                    "x": 0,
                    "y": 0,
                    "w": 227,
                    "h": 249
                }
            },
            {
                "confidence": 0,
                "rectangle": {
                    "x": 0,
                    "y": 0,
                    "w": 54,
                    "h": 69
                }
            }
        ],
        "metadata": {
            "height": 250,
            "width": 250,
            "format": "Png"
        },
        "categories": [
            {
                "name": "others_",
                "score": 0.0078125
            },
            {
                "name": "outdoor_",
                "score": 0.01171875,
                "detail": {
                    "landmarks": []
                }
            },
            {
                "name": "text_sign",
                "score": 0.84375
            }
        ],
        "moderate": {
            "isAdultContent": False,
            "isRacyContent": False,
            "isGoryContent": False,
            "adultScore": 0.0022407304495573044,
            "racyScore": 0.003612220985814929,
            "goreScore": 0.000581094529479742
        },
        "faces": [],
        "brands": [],
        "colors": {
            "dominantColorForeground": "White",
            "dominantColorBackground": "Blue",
            "dominantColors": [
                "White",
                "Blue"
            ],
            "accentColor": "0132CA",
            "isBwImg": False,
            "isBWImg": False
        },
        "celebrities": [],
        "landmarks": [],
        "imageType": {
            "clipArtType": 0,
            "lineDrawingType": 0
        },
        "ocr": {
            "text": "8K",
            "writing_style": [],
            "pages": [
                {
                    "page_number": {
                        "height": 250,
                        "width": 250,
                        "angle": 0.3283,
                        "pageNumber": 1,
                        "words": [
                            {
                                "content": "8K",
                                "boundingBox": [
                                    82,
                                    6,
                                    150,
                                    6,
                                    149,
                                    64,
                                    82,
                                    64
                                ],
                                "confidence": 0.993,
                                "span": {
                                    "offset": 0,
                                    "length": 2
                                }
                            }
                        ],
                        "spans": [
                            {
                                "offset": 0,
                                "length": 2
                            }
                        ],
                        "lines": [
                            {
                                "content": "8K",
                                "boundingBox": [
                                    82,
                                    6,
                                    166,
                                    8,
                                    164,
                                    63,
                                    83,
                                    64
                                ],
                                "spans": [
                                    {
                                        "offset": 0,
                                        "length": 2
                                    }
                                ]
                            }
                        ]
                    },
                    "page_height": 250,
                    "page_width": 250,
                    "page_angle": 0.3283,
                    "page_text": [
                        {
                            "text": "8K",
                            "bbox": {
                                "x": 82,
                                "y": 6,
                                "w": 68,
                                "h": 0
                            },
                            "wordShape": "rectangle"
                        }
                    ]
                }
            ]
        },
        "caption_GPTS": "The image is a close-up of a computer screen featuring a design that leans heavily on graphics. It has a dominant color scheme of white and blue, with an accent of a deeper shade of blue. There is also a hint of colorfulness in the background, possibly suggesting other colors being present. The screen displays a white arrow with black text, a number, and 'k' on a white background. There seems to be no identifiable faces, landmarks, or celebrities. The content on the screen appears to be safe and non-explicit.",
        "GPT_level": 1
    }


def get_image_base64_encoding(file_path) -> str:
    with open(file_path, 'rb') as file:
        image_data = file.read()
    image_extension = os.path.splitext(file_path)[1]
    base64_encoded = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/{image_extension[1:]};base64,{base64_encoded}"


def get_audio_base64_encoding(audio_path: str) -> str:
    with open(audio_path, 'rb') as file:
        audio_data = file.read()
    audio_extension = os.path.splitext(audio_path)[1]
    base64_encoded = base64.b64encode(audio_data).decode('utf-8')
    # Make sure to append base64 header
    return f"data:audio/{audio_extension[1:]};base64,{base64_encoded}"


class Astica_Free_API_key:
    def __init__(self, proxies=None):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
        self.proxies = proxies
        self.accesstok, self.ret, self.cookie = self.get_access_tokens()
        self.tkn = self.get_token()
        set_database("default", "astica_api", self.tkn)

    def get_access_tokens(self):
        url = "https://astica.ai/vision/describe-images"

        payload = ""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ru,en;q=0.9",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.user_agent
        }

        try:
            response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)
        except requests.exceptions.TooManyRedirects:
            raise Exception("Твой IP заблокирован. Используйте proxy")

        # logger.logging(response.text)
        key_1 = "accesstok"
        key_2 = "ret"
        return Astica_Free_API_key.find_key(response.text, rf"{key_1}\s*:\s*'([^']*)'"), \
            int(Astica_Free_API_key.find_key(response.text, rf"{key_2}\s*=\s*(\d+)")), \
            "; ".join([f"{k}={v}" for k, v in dict_from_cookiejar(response.cookies).items()])

    def get_token(self, error=0):
        url = "https://astica.ai/ajax/pa.ajax.php"

        payload = f"dt=1&dtv=2&accesstok={self.accesstok}"
        headers = {
            "cookie": self.cookie,
        }

        try:
            response = requests.request("GET", url, data=payload, headers=headers, proxies=self.proxies)
        except requests.exceptions.TooManyRedirects:
            raise Exception("Твой IP заблокирован. Используйте proxy")

        key = "ur_api_key"
        api_key = Astica_Free_API_key.find_key(response.text, rf"{key}\s*=\s*'([^']*)'")

        if not api_key:
            # if error == 3:
            #     with open("temp_response_key.txt", "w", encoding='utf-8') as writer:
            #         writer.write(response.text + "\n")
            #         writer.write(self.cookie + "\n")
            #         writer.write(self.accesstok + "\n")
            raise Exception("Не удалось получить ключ, повторите попытку через несколько минут")
        # logger.logging("Нет ключа доступа. Задержка 120 секунд. Попытка:", error)
        # time.sleep(120)
        # self.accesstok, self.ret, self.cookie = self.get_access_tokens()
        # return self.get_token(error=error + 1)

        logger.logging("refresh API key", api_key)
        return api_key

    @staticmethod
    def find_key(text, pattern):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None


class Astica_API:
    def __init__(self, api_key=None, proxies=None):
        self.proxies = proxies
        if api_key is None:
            api_key = get_database("default", "astica_api")
            if str(api_key) == "None":
                api_key = Astica_Free_API_key(self.proxies).tkn

        self.api_key = api_key

    def get_image_description(self, image_path: str, prompt="", length=90,
                              vision_params=Astica_Describe_Params.gpt, timeout=25) -> dict:
        try:

            input_image = get_image_base64_encoding(image_path)

            payload = {
                'tkn': self.api_key,
                'modelVersion': '2.1_full',
                'visionParams': vision_params,
                'input': input_image,
                'gpt_prompt': prompt,
                'prompt_length': length
            }

            response = requests.post('https://vision.astica.ai/describe', data=json.dumps(payload),
                                     timeout=timeout,
                                     headers={'Content-Type': 'application/json', })

            return self.handle_response(response, self.get_image_description, image_path, prompt, length, vision_params,
                                        timeout)
        except Exception as e:
            logger.logging("Ошибка при получении описания изображения (astica API):", e)

    def generate_text(self, input_text, instruction='', think_pass=1, temperature=0.7,
                      top_p=0.35, token_limit=16000, timeout=25):
        """
                Генерирует текст на основе входных данных.

                Параметры:
                - input_text (str): Входной текст, на основе которого будет сгенерирован текст.
                - instruction (str): Дополнительный контекст или инструкция для модели. По умолчанию пустая строка.
                - think_pass (int): Количество проходов модели. По умолчанию 1.
                - temperature (float): Креативность ответа модели. По умолчанию 0.7.
                - top_p (float): Разнообразие и предсказуемость ответа модели. По умолчанию 0.35.
                - token_limit (int): Максимальная длина ответа модели в токенах. По умолчанию 55.
                - stop_sequence (str): Строка, означающая конец генерации текста. По умолчанию пустая строка.
                - stream_output (int): Определяет, следует ли отображать ответы в реальном времени. 0 или 1. По умолчанию 0.
                - low_priority (int): Определяет, следует ли использовать низкий приоритет для снижения стоимости запроса. 0 или 1. По умолчанию 0.
        """
        try:
            payload = {
                'tkn': self.api_key,
                'modelVersion': 'GPT-S2',
                'instruction': instruction,
                'input': input_text,
                'think_pass': think_pass,
                'temperature': temperature,
                'top_p': top_p,
                'token_limit': token_limit,
                'stop_sequence': '',
                'stream_output': 0,
                'low_priority': 0
            }

            response = requests.post('https://nlp.astica.ai/generate', data=json.dumps(payload), timeout=timeout,
                                     headers={'Content-Type': 'application/json'})

            return self.handle_response(response, self.generate_text, input_text, instruction, think_pass, temperature,
                                        top_p, token_limit, timeout)

        except Exception as e:
            logger.logging("Ошибка при генерации текста (astica API):", e)

    def text_to_speech(self, input_text, voice_id=0, lang='en-US', output_file='output.wav', timeout=20):
        try:
            result = self.handle_audio_request(input_text=input_text, voice_id=voice_id, lang=lang,
                                               output_file=output_file, timeout=timeout)
            wav_data = bytes(result['wavBuffer']['data'])  # it's ok
            with open(output_file, 'wb') as f:
                f.write(wav_data)
            return True
        except Exception as e:
            logger.logging("Ошибка при озвучивании текста (astica API):", e)

    def handle_audio_request(self, input_text, voice_id=0, lang='en-US', output_file='output.wav', timeout=20):
        payload = {
            'tkn': self.api_key,
            'modelVersion': '1.0_full',
            'input': input_text,
            'voice': voice_id,
            'lang': lang,
        }

        response = requests.post('https://voice.astica.ai/speak', data=json.dumps(payload), timeout=timeout,
                                 headers={'Content-Type': 'application/json'})

        return self.handle_response(response, self.handle_audio_request,
                                    input_text=input_text, voice_id=voice_id,
                                    lang=lang, output_file=output_file, timeout=timeout)

    def generate_image(self, prompt, image_path, prompt_negative='', generate_quality=GenerateQuality.faster, generate_lossless=0,
                       seed=None, moderate=1, timeout=60):
        def save_image(image_url):
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as file:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, file)
                return image_path
            else:
                raise Exception(f"Ошибка при загрузке изображения. Код статуса: {response.status_code}")

        try:
            result = self.handle_image_request(prompt=prompt, prompt_negative=prompt_negative,
                                               generate_quality=generate_quality,
                                               generate_lossless=generate_lossless,
                                               seed=seed, moderate=moderate, timeout=timeout)
            logger.logging("image json generated:", result, color=Color.GRAY)

            save_image(result['output'])

            return image_path if os.path.exists(image_path) else None
        except Exception as e:
            logger.logging("Ошибка при генерации изображения (astica API):", e)
            return False

    def handle_image_request(self, prompt, prompt_negative='', generate_quality=GenerateQuality.faster,
                             generate_lossless=0,
                             seed=None, moderate=1, timeout=60):

        if seed is None:
            seed = random.randint(1, 99999999)

        payload = {
            'tkn': self.api_key,
            'modelVersion': '2.0_full',
            'prompt': prompt,
            'prompt_negative': prompt_negative,
            'generate_quality': generate_quality,
            'generate_lossless': generate_lossless,
            'seed': seed,
            'moderate': moderate,
            'low_priority': 0,
        }

        response = requests.post('https://design.astica.ai/generate_image', data=json.dumps(payload),
                                 timeout=timeout,
                                 headers={'Content-Type': 'application/json'})

        return self.handle_response(response, self.handle_image_request,
                                    prompt=prompt, prompt_negative=prompt_negative,
                                    generate_quality=generate_quality, generate_lossless=generate_lossless,
                                    seed=seed, moderate=moderate)

    def transcribe_audio(self, audio_path, timeout=25):
        audio_input = get_audio_base64_encoding(audio_path)

        payload = {
            'tkn': self.api_key,
            'modelVersion': '1.0_full',
            'input': audio_input,
            'doStream': 0,
            'low_priority': 0
        }

        response = requests.post('https://listen.astica.ai/transcribe', data=json.dumps(payload), timeout=timeout,
                                 headers={'Content-Type': 'application/json'})

        return self.handle_response(response, self.transcribe_audio, audio_path, timeout)

    def handle_response(self, response, function, *args, **kwargs):
        if response.status_code == 200:
            if response.json().get('error'):
                error = response.json()['error']
                logger.logging("warn:", error)
                if (error == "invalid api token"
                        or error == 'missing API key'
                        or 'Visit billing at astica.ai/account' in error):
                    self.api_key = Astica_Free_API_key(self.proxies).tkn
                    return function(*args, **kwargs)
                elif error == 'astica.org API: Please do not exceed 45 requests per minute.':
                    time.sleep(5)
                    return function(*args, **kwargs)
                else:
                    raise Exception("Error in response:", error)

            return response.json()
        else:
            return {'status': 'error', 'error': 'Failed to connect to the API.'}
