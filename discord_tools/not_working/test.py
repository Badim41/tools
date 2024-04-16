import json
import requests
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode
import datetime


def oe(G, W):
    key = bytes.fromhex("8fb207b01e2e45d36cb26a1ae0a3b850ab1b86181110e7ddd5c27e54465c8dfd")
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, iv)
    encrypted_data, tag = cipher.encrypt_and_digest(G.encode())
    return {
        "encryptedData": b64encode(encrypted_data).decode(),
        "iv": iv.hex()  # Кодирование iv в строку
    }

# Данные для отправки
from datetime import datetime

# Получение текущего времени в формате UTC
current_time_utc = datetime.utcnow()

# Вывод текущего времени в формате UTC
print("Текущее время в формате UTC:", current_time_utc)

data = {
    "imageUrl": "https://storage.googleapis.com/describe-picture-image/uploads/1712897143269-file",  # Пример URL изображения
    "prompt": "Текст запроса" + " with markdown",
    "mimeType": "image/jpeg",  # Пример MIME-типа изображения
    "userId": "aac_2dZpSF3yuNYV5nFRcAypywlGQmN",  # Пример идентификатора пользователя
    "date": str(current_time_utc)
}

print(data)
# Зашифрованные данные и iv
encrypted_data_iv = oe(json.dumps(data), "8fb207b01e2e45d36cb26a1ae0a3b850ab1b86181110e7ddd5c27e54465c8dfd")
print(encrypted_data_iv)

# URL и заголовки запроса
url = 'https://us-central1-describepicture.cloudfunctions.net/ask_gemini_pro_vision_model_new_public'
headers = {
    'content-type': 'application/json',
    'accept': '*/*',
    'accept-language': 'ru,en;q=0.9',
    'origin': 'https://describepicture.org',
    'referer': 'https://describepicture.org/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36'
}

# Отправка запроса
response = requests.post(url, headers=headers, json=encrypted_data_iv)
print(response.status_code)
print(response.text)

