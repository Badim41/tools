from datetime import datetime


class Color:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    GRAY = '\033[37m'

class Logs:
    def __init__(self, warnings=False, errors=True):
        self.warnings = warnings
        self.errors = errors

    def logging(self, *args, color=None):
        text = ' '.join(map(str, args))
        if not isinstance(color, str) and color is not None:
            raise ValueError("Not a valid color")

        with open("__logs__", "a", encoding="utf-8") as writer:
            writer.write(f"({datetime.now().strftime('%d.%m.%H.%M')}){text}\n")

        if "error" in text.lower() or "traceback" in text.lower() or "ошибка" in text.lower():
            if self.errors:
                colored_text = f"{Color.RED}{text}{Color.RESET}" if color is None else f"{color}{text}{Color.RESET}"
                print(colored_text)
        else:
            if self.warnings:
                colored_text = f"{Color.YELLOW}{text}{Color.RESET}" if color is None else f"{color}{text}{Color.RESET}"
                print(colored_text)