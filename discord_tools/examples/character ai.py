import asyncio
from discord_tools.character_ai_chat import Character_AI

char_token = "CHAR_TOKEN"

char_id = "CHAR_ID"

async def main():
    character = Character_AI(char_id, char_token)
    while True:
        result = await character.get_answer(input("Вопрос:"))
        print("Ответ:", result)

if __name__ == '__main__':
    asyncio.run(main())
