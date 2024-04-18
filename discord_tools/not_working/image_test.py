import requests

url = "https://www.bing.com/images/create"

data = {
    "q": "short, 3D render, high detail, Octane render, 8K, HD",
    "rt": "3", "FORM": "GENCRE"}

headers = {}

proxy = "socks5://localhost:5051"

proxies = {
    'http': proxy,
    'https': proxy
}

response = requests.request("POST", url, data="", headers=headers, params=data, proxies=proxies)

print(response.text)
