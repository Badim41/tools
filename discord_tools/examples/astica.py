import json

from discord_tools.astica_API import Astica_API

# создание класса
astica_api = Astica_API()

# Описание изображения
from discord_tools.astica_API import Astica_Describe_Params

image_path = "cookie.png"
result = astica_api.get_image_description(
    image_path,
    prompt="Что это за картинка?",
    vision_params=Astica_Describe_Params.gpt_detailed)
print(result['caption_GPTS'])

# Генерация текста (GPT)
prompt = "Привет! Как дела?"
result = astica_api.generate_text(prompt, instruction="Ты полезный ассистент и всегда даёшь ответы на русском")
print(result['output'])

# Генерация изображений
from discord_tools.astica_API import GenerateQuality

prompt = "Wonderful tree"
result = astica_api.generate_image(prompt, generate_quality=GenerateQuality.faster)
print(json.dumps(result, indent=4))

# Из текста в речь (TTS)
output_file = "test.wav"
text = "Hellow, how are you today?"
audio_path = astica_api.text_to_speech(text, output_file=output_file)

# Распознавание речи
audio_file = "test.wav"
result = astica_api.transcribe_audio(audio_file)
print(json.dumps(result, indent=4))
