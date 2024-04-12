from discord_tools.lmsys_gpt import Lmsys_API

lmsys_api = Lmsys_API()
number, model = lmsys_api.find_model(["gpt-4", "claude-3"])

lmsys_api.choose_chat(number)
print("Выбрана модель:", model)

answer = lmsys_api.get_answer("Привет! Какая ты модель?")
print(answer)