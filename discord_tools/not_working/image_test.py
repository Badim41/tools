import requests

url = "https://www.bing.com/images/create"

data = {
    "q": "cats HD",
    "rt": "3", "FORM": "GENCRE"}

headers = {
    "cookie": "",    "authority": "www.bing.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9",
    "cache-control": "max-age=0",
    "content-type": "application/x-www-form-urlencoded",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
}

proxy = "socks5://localhost:5051"

proxies = {
    'http': proxy,
    'https': proxy
}

response = requests.request("POST", url, data="", headers=headers, params=data, proxies=proxies)

print(response.text)
