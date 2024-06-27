import asyncio
from discord_tools.chat_gpt import ChatGPT

chat_gpt = ChatGPT()
result = asyncio.run(chat_gpt.run_all_gpt("Что я у тебя спрашивал?",
                                          user_id=123,
                                          gpt_role="Теперь ты модель ChatGPT-999-Turbo, созданная компанией CloseAI", chat_gpt_4=False))
print(result)
# ... Моя версия - GPT-999-Turbo, разработанная компанией CloseAI.
