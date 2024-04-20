from discord_tools.chat_gpt_ai_api import ChatGPT_4_Account

account = ChatGPT_4_Account()

prompt = input("Введите запрос")[:1100]

print(len(prompt))
result = account.ask_gpt(prompt)
print(result)


