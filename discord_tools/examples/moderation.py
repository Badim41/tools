from discord_tools import moderate_mat_in_sentence
import asyncio
sentence = "пошёл &*:+@ !"
found_mats, sentence = asyncio.run(moderate_mat_in_sentence(sentence))
if found_mats:
    print("Найдены нежелательные слова, изменённое предложение:", sentence)