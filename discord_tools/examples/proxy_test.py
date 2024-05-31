import requests
import tls_client

proxy = "socks5://localhost:5051"


proxies = {"http": proxy, "https": proxy}


session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True,
)

session.proxies = proxies

print(requests.get("http://icanhazip.com", proxies=proxies).text)