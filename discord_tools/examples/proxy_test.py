import requests

proxy = "socks5://localhost:5051"

proxies = {"http": proxy, "https": proxy}

print(requests.get("http://icanhazip.com", proxies=proxies).text)