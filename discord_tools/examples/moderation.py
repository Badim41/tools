import asyncio

from discord_tools.describe_image import detect_bad_image, Describers_API
from discord_tools.detect_mat import moderate_mat_in_sentence
from discord_tools.reka_API import Reka_API

# Text

sentence = "пошёл &*:+@ !"
found_mats, sentence = asyncio.run(moderate_mat_in_sentence(sentence))
if found_mats:
    print("Найдены нежелательные слова, изменённое предложение:", sentence)

# Images

proxy = "socks5://localhost:5051"  # Здесь указываем порт 5051, как в вашей команде SSH
proxies = {
    'http': proxy,
    'https': proxy
}

reka_api = Reka_API(app_session="your app session", proxies=proxies)

nsfw_filter = detect_bad_image(image_path=input("Image file:"),
                               describers=[Describers_API.Reka],
                               reka_api=reka_api)

if nsfw_filter:
    print("Изображение небезопасно")
