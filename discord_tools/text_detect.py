import base64
import os
import requests


def get_image_base64_encoding(file_path) -> str:
    with open(file_path, 'rb') as file:
        image_data = file.read()
    image_extension = os.path.splitext(file_path)[1]
    base64_encoded = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/{image_extension[1:]};base64,{base64_encoded}"

proxy = "socks5://localhost:5051"  # Здесь указываем порт 5051, как в вашей команде SSH

proxies = {
    'http': proxy,
    'https': proxy
}

def text_detect(image_path, proxies=None, timeout=60):
    """
    return: caption, text
    """
    url = "https://2txt.vercel.app/api/completion"

    payload = {"prompt": get_image_base64_encoding(image_path)}
    headers = {
        "authority": "2txt.vercel.app",
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }

    response = requests.request("POST", url, json=payload, headers=headers, proxies=proxies, timeout=timeout)

    if response.text == 'Rate limit exceeded':
        raise Exception('Превышен лимит')
    # print(response.text)
    response_text = response.text
    text = ""
    for item in response_text.split("\n"):
        text += item.lstrip("0:\"").rstrip("\"")

    if "▲" in response_text:
        return text.split("▲")
    else:
        return text, ''