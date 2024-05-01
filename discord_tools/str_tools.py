import json
import re


def convert_answer_to_json(answer, keys, start_symbol="{", end_symbol="}"):
    if isinstance(keys, str):
        keys = [keys]

    answer = answer.replace(" ", "")

    if start_symbol in answer and end_symbol in answer:
        answer = answer[answer.find(start_symbol):]
        answer = answer[:answer.rfind(end_symbol) + 1]
    else:
        print("Не json")
        return False, "Не json"

    try:
        response = json.loads(answer)
        for key in keys:
            if response.get(key, "NULL_VALUE") == "NULL_VALUE":
                print("Нет ключа")
                return False, "Нет ключа"
        return True, response
    except json.JSONDecodeError as e:
        print("Error", e)
        return False, str(e)


def remove_emojis(text):
    # Паттерн для поиска смайликов
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # смайлики эмодзи
                               u"\U0001F300-\U0001F5FF"  # символы и пиктограммы
                               u"\U0001F680-\U0001F6FF"  # символы транспорта и карты
                               u"\U0001F1E0-\U0001F1FF"  # флаги (iOS)
                               "]+", flags=re.UNICODE)
    # Удаляем смайлики из текста
    return emoji_pattern.sub(r'', text)
