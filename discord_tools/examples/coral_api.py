import asyncio
from discord_tools.chat_gpt import ChatGPT
from discord_tools.coral_API import Coral_API


coral_api = Coral_API(email="EMAIL", password="PASSWORD")

chat_gpt = ChatGPT(coral_api=coral_api)

result = asyncio.run(chat_gpt.run_all_gpt("Что ты умеешь?"))
print(result)
# ... Моя версия - GPT-999-Turbo, разработанная компанией CloseAI.
