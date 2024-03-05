import asyncio
import requests
import traceback
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import json
from bs4 import BeautifulSoup

from discord_tools.chat_gpt import ChatGPT

example_json = """{
  "тема": "запрос1",
  "тема": "запрос2"
}
"""


class Internet:
    def __init__(self, chat_gpt: ChatGPT, api_search_key=None, cse_id=None):
        self.api_search_key = api_search_key
        self.cse_id = cse_id
        self.chat_gpt = chat_gpt

    async def get_links_from_internet(self, text_request, api_key=False):
        def generate_search_link(word):
            encoded_word = word.encode('utf-8')
            query = urllib.parse.quote(encoded_word)
            search_link = f"https://www.google.com/search?q={query}"
            return search_link

        if api_key and self.api_search_key and self.cse_id:
            url = f"https://www.googleapis.com/customsearch/v1?q={text_request}&cx={self.cse_id}&key={self.api_search_key}&start=1&num=2"
            response = requests.get(url)
            links = []

            if response.status_code == 200:
                search_results = response.json().get('items', [])

                for result in search_results:
                    link = result.get('link')
                    if link:
                        links.append(link)
            return links[:4]
        else:
            options = webdriver.ChromeOptions()
            prefs = {
                "profile.managed_default_content_settings.images": 2
            }
            options.add_experimental_option("prefs", prefs)
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            driver.set_page_load_timeout(30)

            search_url = generate_search_link(text_request)
            print("getting", search_url)

            try:
                driver.get(search_url)
            except Exception as e:
                # print(e)
                pass

            links_row = driver.find_elements(by=By.CSS_SELECTOR, value="div.MjjYud")

            return_list = set()
            for link_row in links_row:
                try:
                    link_ready = link_row.find_element(By.CSS_SELECTOR, '[href]')
                    link_ready = link_ready.get_attribute("href")
                    print(link_ready)
                    if link_ready:
                        return_list.add(link_ready)
                except Exception as e:
                    # print(e)
                    pass
            return return_list[:2]

    async def search(self, text_request, full_answer=True, limited=False):
        def parse_links(links):
            texts = []

            for link in links:
                print(link)
                try:
                    # Получаем содержимое веб-страницы
                    response = requests.get(link)
                    response.raise_for_status()  # Проверяем, успешен ли запрос

                    # Используем BeautifulSoup для парсинга HTML-кода
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Извлекаем текст из всех заголовков на странице
                    headline_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    for headline in headline_elements:
                        headline_text = headline.get_text().strip()
                        if headline_text:
                            texts.append(headline_text)

                    # Извлекаем текст из всех параграфов на странице
                    paragraph_elements = soup.find_all('p')
                    for paragraph in paragraph_elements:
                        paragraph_text = paragraph.get_text().strip()
                        if paragraph_text:
                            texts.append(f"Paragraph: {paragraph_text}")

                except requests.RequestException as e:
                    print(f"Произошла ошибка при запросе: {e}")
                except Exception as e:
                    print(f"Произошла ошибка: {e}")

            return texts

        def search_wrapped(text_request, full_answer, limited):
            try:

                today_prompt = f"Сегодня {datetime.date.today().strftime('%a, %b %e, %Y')}."
                search_prompt = ("# Background\n\n"
                                 f"{today_prompt}\n\n"
                                 f"Готовьтесь к этому запросу: {text_request}\n\n"
                                 "# Request\n\n"
                                 "Какие 2 темы интернет-поиска помогут вам ответить на этот вопрос? Включи в запрос имя сайта, на котором точно будет эта информация"
                                 "Ответьте только в формате JSON:\n" + example_json)

                search_text = asyncio.run(self.chat_gpt.run_all_gpt(search_prompt, mode="Fast", user_id=0, limited=limited))
                search_json = json.loads(search_text.replace("```json", "").replace("```", ""))
                links = set()
                for search_request in search_json.values():
                    links_list = asyncio.run(self.get_links_from_internet(search_request, api_key=True))
                    links.update(links_list)

                parsed_links = parse_links(links)
                text_from_pages = '\n'.join(parsed_links)

                if text_from_pages:

                    background_text = asyncio.run(self.chat_gpt.summarise(f"{today_prompt}\n\n"
                                                                          "Вы предоставляете полезные и полные ответы.\n\n"
                                                                          f"Составьте список фактов из информации с сайтов, которые помогут с вопросом{text_request}:",
                                                                          text_from_pages, limited=limited))
                    while len(background_text) > 4000:
                        background_text = asyncio.run(self.chat_gpt.summarise(f"{today_prompt}\n\n"
                                                                              "Вы предоставляете полезные и полные ответы.\n\n"
                                                                              f"ВЫБЕРИ ТОЛЬКО САМУЮ ВАЖНУЮ информацию, которая поможет с вопросом {text_request}",
                                                                              background_text, limited=limited))
                    if not full_answer:
                        return '\nИсточники:\n' + '\n\n'.join(links), background_text, "\n\n".join([
                            "Ты должен проанализировать информацию, и дать ответ на запрос\n"
                            "# Информация",
                            background_text,
                            today_prompt,
                            "# Запрос",
                            f"{text_request}"])
                    else:
                        answer = asyncio.run(self.chat_gpt.run_all_gpt("\n\n".join([
                            "Ты должен проанализировать информацию, и дать ответ на запрос\n"
                            "# Информация",
                            background_text,
                            today_prompt,
                            "# Запрос",
                            f"{text_request}"]),
                            "Fast", 0, limited=limited))
                        return answer + '\n\nИсточники:\n' + '\n\n'.join(links)
            except Exception:
                traceback_str = traceback.format_exc()
                print("error in search.py:", str(traceback_str))

        return await asyncio.to_thread(search_wrapped, text_request, full_answer, limited)
