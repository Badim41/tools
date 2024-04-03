from discord_tools.chat_gpt import ChatGPT
chat_gpt = ChatGPT(testing=True)
result = await chat_gpt.run_all_gpt("Какая ты модель GPT?", user_id=123, gpt_role="Теперь ты модель ChatGPT-999-Turbo, созданная компаниней CloseAI")
print(result)
# ... Моя версия - GPT-999-Turbo, разработанная компанией CloseAI.
