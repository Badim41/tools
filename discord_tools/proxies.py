import random
import requests
from bs4 import BeautifulSoup as bs


class ProxySession:
    def __init__(self, proxy_type, url=None):
        self.ip = None
        self.proxy_session = proxy_type(self, url=url)
        print("Текущий IP:", self.ip)

    def get_free_proxy(self, url=None):
        return self.get_valid_proxy(ProxySession.get_free_proxy_list(), url=url)

    @staticmethod
    def get_free_proxy_list():
        url = "https://free-proxy-list.net/"
        # Получаем ответ HTTP и создаем объект soup
        response = requests.get(url)
        soup = bs(response.content, "html.parser")

        proxies = []
        # Используем CSS-селектор для поиска таблицы прокси
        for row in soup.select("table.table.table-striped.table-bordered tbody tr"):
            tds = row.find_all("td")
            try:
                ip = tds[0].text.strip()
                port = tds[1].text.strip()
                host = f"{ip}:{port}"
                proxies.append(host)
            except IndexError:
                continue
        print(f'Обнаружено бесплатных прокси (free-proxy-list.net): {len(proxies)}', proxies[0])
        return proxies

    def get_valid_proxy(self, proxies, attemps=50, url=None):

        for i in range(attemps):
            proxy = random.choice(proxies)
            session = ProxySession.get_session(proxy)
            try:
                self.ip = session.get("http://icanhazip.com", timeout=1.5).text.strip()

                if url:
                    session.get(url)

                return session
            except Exception as e:
                print(f"error in proxy {proxy}", e)
                continue

    def get_tor_proxy(self, url=None):
        session = requests.Session()
        # установка прокси для http и https на localhost: 9050
        # для этого требуется запущенная служба Tor на вашем компьютере и прослушивание порта 9050 (по умолчанию)
        session.proxies = {"http": "socks5://localhost:9050", "https": "socks5://localhost:9050"}
        self.ip = session.get("http://icanhazip.com").text

        if url:
            session.get(url)

        return session

    @staticmethod
    def get_session(proxy):
        session = requests.Session()
        session.proxies = {"http": proxy, "https": proxy}
        return session

    @staticmethod
    def request(self, method, url, **kwargs):
        with self.proxy_session as session:
            return session.request(method=method, url=url, **kwargs)


class ProxyTypes:
    free_proxy_list = ProxySession.get_free_proxy
    tor_proxy = ProxySession.get_tor_proxy


if __name__ == "__main__":
    url = "https://astica.ai/vision/describe-images"

    session = ProxySession(proxy_type=ProxyTypes.tor_proxy).proxy_session

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }

    try:
        response = session.get(url, data=payload, headers=headers)
    except requests.exceptions.TooManyRedirects:
        raise Exception("IP заблокирован")
    except Exception as e:
        raise Exception("Fatal error", e)

    print(response.text)
