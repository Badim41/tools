from discord_tools.chat_gpt import ChatGPT
chat_gpt = ChatGPT()
result = await chat_gpt.run_all_gpt("Как тебя зовут?", user_id=123)
print(result)
