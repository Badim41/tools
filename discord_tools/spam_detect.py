def detect_caps_lock(text):
    return all(char.isupper() or char.isspace() for char in text) and len(text) > 5

def detect_spam(text):
    words = text.split(" ")
    if len(words) < 6:
        return False
    uniq_words = set()
    for word in words:
        uniq_words.add(word)
    spam = len(words) // len(uniq_words) > 2
    print(len(words), len(uniq_words), len(words) // len(uniq_words), spam)
    return spam