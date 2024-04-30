# Discord Tools

Инструменты для работы с Discord, функции чат-ботов, генерация изображений, модерация текста, поиск в интернете, базы данных, перевод, таймеры.

1. [Установка](#section-1)
2. [ChatGPT](#section-2)
    1. [Создание класса](#section-2.1)
    2. [С ключами OPEN_AI](#section-2.2)
    3. [С аутентификационным ключом ChatGPT (бесплатно)](#section-2.3)
    4. [С аутентификационным ключом character.ai (бесплатно)](#section-2.4)
    5. [Ответ](#section-2.5)
    6. [Несколько ответов](#section-2.6)
    7. [Сохранение истории](#section-2.7)
    8. [С системным запросом](#section-2.8)
    9. [Поиск в интернете с GPT](#section-2.9)
    10. [Поиск c ключом Google (РЕКОМЕНДОВАНО)](#section-2.10)
    11. [Ограничить использование ключа OPEN_AI](#section-2.11)
    12. [Модерация](#section-2.12)
3. [Character.ai](#section-3)
    1. [Модерация мата](#section-3.1)
4. [Инструменты для модерации](#section-4)
5. [Бесплатная генерация изображений](#section-5)
    1. [С указанием ключей](#section-5.1)
6. [Цветные логи](#section-6)
7. [Таймеры](#section-7)
8. [Перевод](#section-9)
9. [База данных](#section-10)
10. [Скачать аудиофайл по ссылке с ютуба](#section-11)
11. [Отделить вокал/иструментал](#section-12)
    1. [Одна модель](#section-12.1)
    2. [Несколько моделей](#section-12.2)
12. [Увеличение разрешения изображени](#section-13)
13. [Убрать фон с изображения](#section-14)

## Установка <a name="section-1"></a>

Установите пакет с помощью pip:

```bash
pip install git+https://github.com/Badim41/tools.git
```

# ChatGPT <a name="section-2"></a>
## Создание класса <a name="section-2.1"></a>
```python
from discord_tools.chat_gpt import ChatGPT

chat_gpt = ChatGPT()
```
### С ключами OPEN_AI  <a name="section-2.2"></a>
```python
from discord_tools.chat_gpt import ChatGPT

chat_gpt = ChatGPT(OPEN_AI_KEY: [str, list])
```
### С аутентификационным ключом ChatGPT (бесплатно)  <a name="section-2.3"></a>
```python
from discord_tools.chat_gpt import ChatGPT

# https://chat.openai.com/api/auth/session - {accessToken}
chat_gpt = ChatGPT(auth_keys=AUTH_KEY: [str, list])
```
### С аутентификационным ключом character.ai (бесплатно)  <a name="section-2.4"></a>
![img.png](img.png)
```python
from discord_tools.chat_gpt import ChatGPT

# https://beta.character.ai - На F12 смотрите char_token в Local Storage
chat_gpt = ChatGPT(char_tokens=CHAR_TOKEN: [str, list])
```

### С аутентификационным ключом deepseek (бесплатно)  <a name="section-2.4.1"></a>
```python
from discord_tools.chat_gpt import ChatGPT

# https://chat.deepseek.com - На F12 смотрите Authorization в любом запросе к сайту
chat_gpt = ChatGPT(deep_seek_auth_keys=DEEP_SEEK_AUTH_KEYS: [str, list])
```

### С ключом deepseek (бесплатно)  <a name="section-2.4.2"></a>
```python
# https://platform.deepseek.com/api_keys
chat_gpt = ChatGPT(deep_seek_keys=DEEP_SEEK_API_KEYS: [str, list])
```

### С логином и паролем или ключом https://coral.cohere.com
```python
from discord_tools.chat_gpt import ChatGPT
from discord_tools.coral_API import Coral_API

coral_api = Coral_API(email="EMAIL", password="PASSWORD")
coral_api = Coral_API(api_key="API_KEY")

chat_gpt = ChatGPT(coral_api=coral_api)

result = await chat_gpt.run_all_gpt("Что ты умеешь?")
print(result)
```

### Все сразу
```python
from discord_tools.chat_gpt import ChatGPT
chat_gpt = ChatGPT(openAI_keys=OPEN_AI_KEYS,
                auth_keys=AUTH_KEYS,
                char_tokens=CHAR_TOKEN,
                deep_seek_keys=DEEP_SEEK_API_KEYS,
                deep_seek_auth_keys=DEEP_SEEK_AUTH_KEYS,
                coral_api=coral_api)
```
## Ответ <a name="section-2.5"></a>
```python
result = await chat_gpt.run_all_gpt("запрос")
print(result)
```
### Несколько ответов <a name="section-2.6"></a>
```python
from discord_tools.chat_gpt import ChatGPT_Mode
result = await chat_gpt.run_all_gpt("запрос", mode=ChatGPT_Mode.all)
print(result)
```
### Сохранение истории <a name="section-2.7"></a>
```python
from discord_tools.chat_gpt import clear_history
result = await chat_gpt.run_all_gpt("запрос", user_id=123) # 123 - номер для сохранения
print(result)
await clear_history(123) # отчистка
```
### С системным запросом  <a name="section-2.8"></a>
```python
result = await chat_gpt.run_all_gpt("запрос", gpt_role="Ты полезный ассистент")
print(result)
```
## Поиск в интернете с GPT  <a name="section-2.9"></a>
```python
from discord_tools.internet import Internet

internet = Internet(chat_gpt)
result = await internet_searcher.search("Погода в Москве сейчас")
```
### Поиск c ключом Google (РЕКОМЕНДОВАНО)  <a name="section-2.10"></a>
```python
API_SEARCH_KEY, CSE_ID - https://docs.typingmind.com/plugins/use-web-search-and-image-search
internet = Internet(chat_gpt, api_search_key=API_SEARCH_KEY, cse_id=CSE_ID)
result = await internet.search("Погода в Москве сейчас")
```
## Суммирование информации с GPT  <a name="section-2.10-2"></a>
```python
result = await chat_gpt.summarise("запрос", full_text="Содержание текст")
print(result)
```
## Ограничить использование ключа OPEN_AI  <a name="section-2.11"></a>
```python
result = await chat_gpt.run_all_gpt("запрос", limited=True)
print(result)

internet = Internet(chat_gpt, limited=True)
result = await internet.search("запрос")
print(result)

result = await chat_gpt.summarise("запрос", full_text="Содержание текст", limited=True) 
print(result)
```
## Модерация  <a name="section-2.12"></a>
```python
flagged_status, violated_categories = await chat_gpt.moderation_request(text)
if flagged_status:
    print("Нарушенные категории:", violated_categories)
```
# Character.ai  <a name="section-3"></a>
```python
from discord_tools.character_ai_chat import Character_AI
character = Character_AI(char_id, char_token)
result = await character.get_answer("запрос")
print(result)
```
## Модерация мата <a name="section-3.1"></a>
```python
from discord_tools.character_ai_chat import Character_AI, ModerateParams
character = Character_AI(char_id, char_token)
result = await character.get_answer("запрос", moderate_answer=ModerateParams.replace_mat)
print(result)
ModerateParams.skip - не модерировать
ModerateParams.until_good - генерировать до ответа, который пройдёт модерацию
ModerateParams.replace_mat - заменить все нежелательные слова на "^_^"
```
# Инструменты для модерации  <a name="section-4"></a>
```python
from discord_tools.detect_mat import moderate_mat_in_sentence
sentence = "пошёл &*:+@ !"
found_mats, sentence = await moderate_mat_in_sentence(sentence)
if found_mats:
    print("Найдены нежелательные слова, изменённое предложение:", sentence)
```
# Бесплатная генерация изображений <a name="section-5"></a>
```python
from discord_tools.image_generate import GenerateImages
generator = GenerateImages()
images = await generator.generate("Tree 4K")
print(images) # пути к файлам
```
## С указанием ключей <a name="section-5.1"></a>
```python
from discord_tools.image_generate import GenerateImages
KANDINSKY_KEYS - https://fusionbrain.ai/keys/
CHAR_TOKENS - https://beta.character.ai - На F12 смотрите char_token в Local Storage

# куки, отправляемые на сайт. Можно посмотреть в F12
BING_COOKIES - https://www.bing.com/images/create/

generator = GenerateImages(secret_keys_kandinsky=secret_keys_kandinsky,
                                 apis_kandinsky=apis_kandinsky,
                                 char_tokens=char_tokens,
                                 bing_cookies=bing_cookies)
images = await generator.generate("Tree 4K")
print(images) # пути к файлам
```
# Цветные логи <a name="section-6"></a>
```python
from discord_tools.logs import Logs, Color
logger = Logs(warnings=True)
logger.logging("hello", "world", color=Color.GRAY)
```
# Таймеры <a name="section-7"></a>
```python
from discord_tools.timer import Time_Count
timer = Time_Count()
time.sleep(1)
spent_time = timer.count_time()
print("прошло", spent_time)
```
# Перевод <a name="section-9"></a>
```python
# Сделан, потому что многие библиотеки для перевода конфликтуют с OpenAI
from discord_tools.translate import translate_text, Languages
text = "Привет!"
translated_text = await translate_text(text, Languages.en)
print(translated_text)
```
# База данных <a name="section-10"></a>
```python
from discord_tools.sql_db import get_database, set_database
asyncio.run(set_database(section="Секция", key="Ключ", value="Значение"))
print(get_database(section="Секция", key="Ключ"))
```
```python
# Одним методом (Возможно, что не совсем удобная)*
from discord_tools.sql_db import set_get_database_async
asyncio.run(set_get_database_async(section="Секция", key="Ключ", value="Значение"))
key = asyncio.run(set_get_database_async("Секция", "Ключ"))
print(key)
```
# Скачать аудиофайл по ссылке с ютуба <a name="section-11"></a>
```python
from discord_tools.yt_downloader import get_youtube_video_id, yt_download

url = "https://youtube.com/..."
song_id = get_youtube_video_id(url)

if song_id is None:
    raise Exception("Нет song id")

song_link = song_id.split('&')[0]
audio_path = yt_download(song_link, max_duration=3600) # время в секундах
```

# Отделить вокал/иструментал (и ещё 9 моделей) <a name="section-12"></a>
## Одна модель <a name="section-12.1"></a>
```python
from discord_tools.lalalai import LalalAIModes, process_file_pipeline

file_path = "file.mp3"
result_1, result_2 = process_file_pipeline(large_file_name=file_path,
                                           mode=LalalAIModes.Vocal_and_Instrumental)
```
## Несколько моделей <a name="section-12.2"></a>
```python
from discord_tools.lalalai import full_process_file_pipeline, LalalAIModes

input_str = input("Введите имя файла или ссылку на ютуб:\n")
results = full_process_file_pipeline(input_str,
                                     modes=[LalalAIModes.Vocal_and_Instrumental,
                                            LalalAIModes.Drums,
                                            LalalAIModes.Bass,
                                            LalalAIModes.Electric_guitar,
                                            LalalAIModes.Acoustic_guitar,
                                            LalalAIModes.Piano,
                                            LalalAIModes.Synthesizer,
                                            LalalAIModes.Strings,
                                            LalalAIModes.Wind])
print("All results:", results)
```
# Увеличение разрешения изображения до 8К <a name="section-13"></a>
```python
from discord_tools.upscaler import upscale_image, Upscale_Mode

image_path = "image.png"
result_path, result_url = upscale_image(image_path, Upscale_Mode.quality_8K)
print(result_path, result_url)
```

# Убрать фон с изображения <a name="section-14"></a>
```python
from discord_tools.upscaler import remove_background

image_path = "image.png"
result_path, result_url = remove_background(image_path)
print(result_path, result_url)
```

# Описать изображение <a name="section-14"></a>
```python
from discord_tools.describe_image import describe_image

image_path = "temp.png"
nsfw, result = describe_image(image_path,prompt="Что изображено на картинке?")
print(result)
if nsfw:
    print("Картинка содержит нежелательное содержимое")
```

# Модерация изображений <a name="section-14"></a>
```python
from discord_tools.describe_image import detect_bad_image

image_path = "temp.png"
nsfw = detect_bad_image(image_path)
if nsfw:
    print("Картинка содержит нежелательное содержимое")
else:
    print("Картинка прошла модерацию")
```