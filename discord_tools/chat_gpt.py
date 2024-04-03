import asyncio
import g4f
import json
import logging
import os
import requests
import traceback
import uuid

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage

from discord_tools.logs import Logs, Color
from discord_tools.character_ai_chat import Character_AI, ModerateParams
from discord_tools.translate import translate_text

_providers = [
    # AUTH
    # g4f.Provider.Raycast,
    # g4f.Provider.Phind,
    g4f.Provider.Liaobots,  # - Doker output & Unauth
    # g4f.Provider.Bing,
    # g4f.Provider.Bard,
    # g4f.Provider.OpenaiChat,
    # g4f.Provider.Theb,

    # Binary location error
    # g4f.Provider.Poe,
    # g4f.Provider.GptChatly,
    # g4f.Provider.AItianhuSpace,

    # g4f.Provider.GPTalk, # error 'data'
    # g4f.Provider.GeminiProChat, # Server Error
    # g4f.Provider.Gpt6, # ?
    # g4f.Provider.AiChatOnline, # ?
    # g4f.Provider.GptGo, # error
    # g4f.Provider.Chatxyz, # error

    # not exists
    # g4f.Provider.ChatgptAi,
    # g4f.Provider.OnlineGpt,
    # g4f.Provider.ChatgptNext,

    # g4f.Provider.Vercel,  # cut answer
    # g4f.Provider.ChatgptDemo,  # ?

    # g4f.Provider.ChatgptLogin,  # error 403
    # g4f.Provider.ChatgptX,  # error
    # g4f.Provider.ChatgptFree,

    # Short answer
    # g4f.Provider.Aura,
    # g4f.Provider.ChatBase,
    g4f.Provider.Koala,
    g4f.Provider.ChatForAi,  # too many req
    g4f.Provider.FreeChatgpt,

    # bad providers
    # g4f.Provider.GptGod,  # error list
    # g4f.Provider.FreeGpt,# wrong language
    # g4f.Provider.GptForLove,  # error no OpenAI Key
    # g4f.Provider.Opchatgpts,  # bad
    # g4f.Provider.Chatgpt4Online,  # - bad

    # g4f.Provider.Llama2, # no model

    # not working
    # g4f.Provider.You,
    # g4f.Provider.GeekGpt,
    # g4f.Provider.AiAsk,
    # g4f.Provider.Hashnode,
    # g4f.Provider.FakeGpt,
    # g4f.Provider.Aichat,

    # undetected chrome driver
    # g4f.Provider.MyShell,
    # g4f.Provider.PerplexityAi,
    # g4f.Provider.TalkAi,

    # Other
    g4f.Provider.DeepInfra,
    g4f.Provider.Llama2,
]


async def remove_last_format_simbols(text, format="```"):
    parts = text.split(format)
    if len(parts) == 4:
        corrected_text = format.join(parts[:3]) + parts[3]
        return corrected_text
    return text


async def load_history_from_json(user_id):
    if not user_id:
        return []

    try:
        with open(f'gpt_history/{user_id}_history.json', 'r') as file:
            chat_history = json.load(file)
    except FileNotFoundError:
        chat_history = []

    # print("load_history:", chat_history)
    return chat_history


def serialize_chat_message(obj):
    if isinstance(obj, ChatCompletionMessage):
        return {
            'role': obj.role,
            'content': obj.content,
        }
    # Add more checks for other custom objects if needed
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


async def save_history(history, user_id):
    if not user_id:
        return

    # print("Save history:", history, user_id)
    with open(f'gpt_history/{user_id}_history.json', 'w') as file:
        json.dump(history, file, indent=4, default=serialize_chat_message)


async def get_sys_prompt(user_id, gpt_role):
    if gpt_role == "GPT" or not gpt_role or not user_id:
        sys_prompt = [{"role": "system", "content": "Ты полезный ассистент и даёшь только полезную информацию"}]
    else:
        sys_prompt = [{"role": "system", "content": gpt_role}]
    return sys_prompt

def transform_messages(messages):
    transformed_messages = []
    for message in messages:
        transformed_message = {
            "id": str(uuid.uuid4()),
            "author": {"role": message['role']},
            "content": {"content_type": "text", "parts": [message['content']]},
            "metadata": {}
        }
        transformed_messages.append(transformed_message)
    return transformed_messages

async def clear_history(user_id):
    try:
        os.remove(f'gpt_history/{user_id}_history.json')
    except FileNotFoundError:
        pass


async def trim_history(history, max_length=4000):
    current_length = sum(len(message["content"]) for message in history)
    while history and current_length > max_length:
        removed_message = history.pop(0)
        current_length -= len(removed_message["content"])
    return history


class ChatGPT_Mode:
    fast = "Fast"
    all = "All"


class ChatGPT:
    def __init__(self, openAI_keys=None, openAI_moderation=None,
                 auth_keys=None, save_history=True,
                 warnings=True,
                 errors=True, testing=False, char_tokens=None, char_ids=None):
        if isinstance(openAI_moderation, list):
            self.openAI_keys = openAI_keys
        elif isinstance(openAI_moderation, str):
            self.openAI_keys = [openAI_keys]
        else:
            self.openAI_keys = None

        self.gpt_queue = 0

        self.moderation_queue = 0
        self.is_running_moderation = False
        self.previous_requests_moderation = {}

        if isinstance(openAI_moderation, list):
            self.openAI_moderation = openAI_moderation
        elif isinstance(openAI_moderation, str):
            self.openAI_moderation = [openAI_moderation]
        elif self.openAI_keys:
            self.openAI_moderation = self.openAI_keys
        else:
            self.openAI_moderation = None

        if isinstance(auth_keys, list):
            self.openAI_auth_keys = auth_keys
        elif isinstance(auth_keys, str):
            self.openAI_auth_keys = [auth_keys]
        else:
            self.openAI_auth_keys = None

        self.character_queue = 0

        if char_tokens:
            if not char_ids:
                char_ids = []
                for i in range(len(char_tokens)):
                    char_ids.append("BXjpSWm9GY21z5b3V-x3ZnudZD1G1xV7ZaoZJ1KaDVg")
            elif len(char_ids) == len(char_tokens):
                raise Exception("char_ids:list и char_tokens:list должны быть одинаковой длины!")

            self.chars = [Character_AI(char_id=char_ids[number], char_token=char_tokens[number],
                                       testing=testing) for number in range(len(char_ids))]
        else:
            self.chars = []

        self.logger = Logs(warnings=warnings, errors=errors)
        self.testing = testing

    async def run_all_gpt(self, prompt, mode=ChatGPT_Mode.fast, user_id=None, gpt_role=None, limited=False,
                          translate_lang=None):
        def get_fake_gpt_functions(delay):
            functions_add = \
                [self.one_gpt_run(provider=provider, messages=messages, delay_for_gpt=delay,
                                  translate_lang=translate_lang) for provider in _providers]

            if self.chars:
                char = self.chars[self.character_queue % len(self.chars)]
                functions_add += \
                    [char.get_answer(message=prompt, moderate_answer=ModerateParams.replace_mat, return_image=False)]

            return functions_add

        if not os.path.exists('gpt_history'):
            os.mkdir('gpt_history')
        
        self.gpt_queue += 1
        if self.testing:
            self.logger.logging("run GPT", prompt, color=Color.GRAY)
        else:
            self.logger.logging("run GPT", color=Color.GRAY)

        if prompt == "" or prompt is None:
            return "Пустой запрос"

        # Ограничение
        values = [False, True]
        if limited:
            values = [False]

        # обрезка зщапроса
        if len(prompt) > 4000:
            prompt = prompt[:4000]
            self.logger.logging(f"Cut prompt: ...{prompt[3950:4000]}...", color=Color.YELLOW)

        # загрузка истории
        chat_history = await load_history_from_json(user_id)
        chat_history.append({"role": "user", "content": prompt})
        chat_history = await trim_history(chat_history, max_length=4000)

        messages = await get_sys_prompt(user_id, gpt_role) + chat_history
        if self.testing:
            self.logger.logging("messages", messages, Color.GRAY)

        if mode == ChatGPT_Mode.fast:
            # Пробуем запустить настоящие GPT первыми
            for value in values:
                answer = await self.run_official_gpt(messages, 1, value, user_id, gpt_role)
                if answer and prompt not in answer:
                    chat_history.append({"role": "assistant", "content": answer})
                    await save_history(chat_history, user_id)
                    return answer

            functions = get_fake_gpt_functions(30)

            done, pending = await asyncio.wait(functions, return_when=asyncio.FIRST_COMPLETED)

            # Принудительное завершение оставшихся функций
            for task in pending:
                task.cancel()

            # Получение результата выполненной функции
            for task in done:
                result = await task
                chat_history.append({"role": "assistant", "content": result})
                await save_history(chat_history, user_id)
                return result

        elif mode == ChatGPT_Mode.all:
            functions = [self.run_official_gpt(messages, 1, value, user_id, gpt_role) for value in values]

            functions += get_fake_gpt_functions(1)

            results = await asyncio.gather(*functions)  # результаты всех функций

            new_results = []
            for i, result in enumerate(results):
                if result and not str(result).replace("\n", "").replace(" ", "") == "":
                    new_results.append(result)

            result = '\n\n==Другой ответ==\n\n'.join(new_results)
            chat_history.append({"role": "assistant", "content": new_results[0]})
            await save_history(chat_history, user_id)
            return result

        self.logger.logging("error: no GPT mode", Color.RED)
        raise Exception("Не выбран режим GPT")

    async def one_gpt_run(self, provider, messages, delay_for_gpt, translate_lang):
        try:

            result = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                provider=provider,
                messages=messages,
                timeout=30
            )

            if result is None \
                    or result.replace("\n", "").replace(" ", "") == "" \
                    or result == "None" or "!DOCTYPE" in str(result) \
                    or "https://gptgo.ai" in str(result) \
                    or '[GoogleGenerativeAI Error]' in str(result):
                await asyncio.sleep(delay_for_gpt)
                return

            # если больше 3 "```" (форматов)
            result = await remove_last_format_simbols(result)

            # добавляем имя провайдера
            provider = str(provider)
            provider = provider[provider.find("'") + 1:]
            provider = provider[:provider.find("'")]

            if self.testing:
                self.logger.logging("PROVIDER:", provider, result, "\n", color=Color.GRAY)

            if translate_lang:
                result = await translate_text(text=result, target_lang=translate_lang)

            return result
        except Exception as e:
            if self.testing:
                self.logger.logging(f"Error in {str(provider)}", str(e), color=Color.GRAY)
            await asyncio.sleep(delay_for_gpt)
    
    async def run_no_auth_official_gpt(self, messages, delay_for_gpt, user_id):
        try:
            messages = transform_messages(messages)
            self.logger.logging(f"Run no auth GPT", color=Color.GRAY)
            
            device_id = str(uuid.uuid4())
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            
            url = 'https://chat.openai.com/backend-anon/sentinel/chat-requirements'
            
            headers = {
                'oai-device-id': device_id,
                'user-agent': user_agent
            }
            data = {}
            
            response = requests.post(url, headers=headers, json=data)
            auth_token = response.json()['token']
            
            url = 'https://chat.openai.com/backend-api/conversation'
            headers = {
                'cookie': f'oai-did={device_id}',
                'oai-device-id': device_id,
                'openai-sentinel-chat-requirements-token': auth_token,
                'user-agent': user_agent,
            }
            
            data = {
                "action": "next",
                "messages": messages,
                "parent_message_id": str(uuid.uuid4()),
                "model": "text-davinci-002-render-sha",
                "websocket_request_id": str(uuid.uuid4())
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            response_parts = response.text.split("data: ")

            if self.testing:
                self.logger.logging("ChatGPT_OFFICIAL_3 ", json.loads(response_parts[-2])['message']['content']['parts'][0], color=Color.GRAY)
            
            return json.loads(response_parts[-2])['message']['content']['parts'][0]
        except Exception as e:
            self.logger.logging("error gpt-off3", str(traceback.format_exc()), response_parts, response)

    async def run_official_gpt(self, messages, delay_for_gpt: int, key_gpt: bool, user_id, gpt_role, error=False):

        if key_gpt:
            # нет ключей
            if not self.openAI_keys:
                await asyncio.sleep(delay_for_gpt)
                return

            try:
                openai_key = self.openAI_keys[self.gpt_queue % len(self.openAI_keys)]
                client = AsyncOpenAI(api_key="sk-" + openai_key)
                completion = await client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=messages
                )
                if self.testing:
                    self.logger.logging("ChatGPT_OFFICIAL_1", completion.choices[0].message.content, color=Color.GRAY)
                return completion.choices[0].message.content
            except Exception as e:
                self.logger.logging("error (id gpt-off1)", e)

                if "Incorrect API key provided" in str(e) or "You exceeded your current quota, please check your plan and billing details." in str(e):
                    self.openAI_keys = self.openAI_keys[1:]

                if self.openAI_keys and not error:
                    return await self.run_official_gpt(messages, delay_for_gpt, key_gpt, user_id, gpt_role, error=True)
                else:
                    await asyncio.sleep(delay_for_gpt)
        else:
            # нет ключей
            if not self.openAI_auth_keys:
                return await self.run_no_auth_official_gpt(messages, delay_for_gpt, user_id)

            try:
                auth_key = self.openAI_auth_keys[self.gpt_queue % len(self.openAI_auth_keys)]

                response = await g4f.ChatCompletion.create_async(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    provider=g4f.Provider.OpenaiChat,
                    access_token=auth_key,
                    auth=auth_key,
                    timeout=30
                )
                if self.testing:
                    self.logger.logging("ChatGPT_OFFICIAL_2:", response, color=Color.GRAY)
                lines = response.split("\n")
                if len(lines) > 2:
                    if lines[1].startswith(lines[0]) or len(response) > 4100:
                        raise Exception(f"Повторяющаяся фраза. Вероятно это баг в ответе:\n {lines[0]} {lines[1]}")
                return response
            except Exception as e:
                self.logger.logging("error gpt-off2", str(traceback.format_exc()))
                if ("Could not parse your authentication" in str(e)
                        # or "Too many requests in 1 hour. Try again later." in str(e) # НЕ УДАЛЯТЬ, ЧЕРЕЗ ЧАС ВЕДЬ ВСЁ НОРМ БУДЕТ
                        or 'token is expired' in str(e)):
                    self.logger.logging("Remove AUTH key", self.openAI_auth_keys[0][:10], color=Color.CYAN)
                    self.openAI_auth_keys = self.openAI_auth_keys[1:]
                if self.openAI_auth_keys and not error:
                    return await self.run_official_gpt(messages, delay_for_gpt, key_gpt, user_id, gpt_role, error=True)
                else:
                    await asyncio.sleep(delay_for_gpt)

    async def moderation_request(self, text, error=0):
        if not self.openAI_moderation:
            self.logger.logging("No moderation keys", Color.RED)
            return False, ""

        if len(text) < 3:
            return False, ""

        if text in self.previous_requests_moderation:
            if self.testing:
                self.logger.logging(
                    f"Запрос '{text}' уже был выполнен, категория нарушений: {self.previous_requests_moderation[text][1]}",
                    color=Color.GRAY)
            return self.previous_requests_moderation[text]

        if self.is_running_moderation:
            if self.testing:
                self.logger.logging("Running!", color=Color.GRAY)
            await asyncio.sleep(0.25)

        self.is_running_moderation = True
        number = self.moderation_queue % len(self.openAI_moderation)
        api_key = self.openAI_moderation[number]
        self.moderation_queue += 1
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {'sk-' + api_key}"
        }
        data = {
            "input": text
        }
        url = "https://api.openai.com/v1/moderations"

        response = requests.post(url, headers=headers, json=data)
        self.is_running_moderation = False
        if response.status_code == 200:
            self.logger.logging(f"api_key: {api_key[:10]}", color=Color.GRAY)
            result = response.json()
            flagged = result['results'][0]['flagged']
            categories = result['results'][0]['categories']
            if flagged:
                violated_categories = [category for category, value in categories.items() if value]
                self.previous_requests_moderation[text] = (True, violated_categories)
                return True, violated_categories
            else:
                self.previous_requests_moderation[text] = (False, "")
                return False, ""
        else:
            if error == 20:
                return None, f"Request failed with status code: {response.status_code}"
            self.logger.logging(f"Error code: {response.status_code}", error, text, color=Color.GRAY)
            await asyncio.sleep(3)
            result1, result2 = await self.moderation_request(text, error=error + 1)
            return result1, result2

    async def summarise(self, prompt, full_text, limit=10, limited=False):
        # Разделение текста на куски по 3950 символов
        text_chunks = [full_text[i:i + 3950] for i in range(0, len(full_text), 3950)]

        gpt_responses = []

        i = 0
        for chunk in text_chunks:
            if i > limit:
                break
            i += 1
            response = await self.run_all_gpt(prompt + chunk, mode=ChatGPT_Mode.fast, user_id=0, limited=limited)
            if (response.startswith("I'm sorry") or
                    response.startswith("Извините") or
                    response.startswith("I cannot provide") or
                    response.startswith("Сожалею") or
                    response.startswith("К сожалению")):
                continue
            gpt_responses.append(response)

        summarized_text = '\n'.join(gpt_responses)

        return summarized_text
