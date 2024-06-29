from discord_tools.chat_gpt_ai_api import ChatGPT_4_Account
proxy = "socks5://localhost:5051"  # Здесь указываем порт 5051, как в вашей команде SSH

proxies = {
    'http': proxy,
    'https': proxy
}

account = ChatGPT_4_Account(proxies=proxies)

# kielbasarendell.yvvh
prompt = input("Введите запрос:")
result = account.ask_gpt(prompt, image_path=r"C:\Users\as280\Downloads\image_1.png")
print(result)

