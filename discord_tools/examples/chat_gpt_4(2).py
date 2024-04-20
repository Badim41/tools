from discord_tools.chat_gpt_ai_api import ChatGPT_4_Account

account = ChatGPT_4_Account()

result = account.ask_gpt("Какая ты модель GPT?")
print(result)
