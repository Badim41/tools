import json
from datetime import datetime, timedelta


class KeyManager:
    def __init__(self, service, json_file="expired_keys.json"):
        self.json_file = json_file

        self.service = service

    def load_keys(self):
        try:
            with open(self.json_file, 'r') as file:
                keys = json.load(file)
        except FileNotFoundError:
            keys = {self.service: []}

        # сервиса нет в ключах
        if self.service not in keys.values():
            keys[self.service] = []

        return keys

    def save_keys(self, keys):
        with open(self.json_file, 'w') as file:
            json.dump(keys, file, indent=4)

    def add_expired_key(self, key):
        keys = self.load_keys()

        keys[self.service].append({"key": key, "expired": datetime.now().strftime("%Y-%m-%d")})
        self.save_keys(keys)

    def get_not_expired_keys(self, row_keys, recovering_time):
        if recovering_time is None:
            recovering_time = 99999

        if row_keys is None:
            return None

        expired_days_ago = datetime.now() - timedelta(days=recovering_time)
        keys = self.load_keys()

        updated_keys = []

        for key in row_keys:
            found = False
            for config_key in keys[self.service]:
                if key in config_key.values():
                    found = True
                    expired_date = datetime.strptime(config_key["expired"], "%Y-%m-%d")
                    if expired_date < expired_days_ago:
                        updated_keys.append(key)
            if not found:
                updated_keys.append(key)
        return updated_keys

if __name__ == '__main__':
    key_manager = KeyManager("Test")
    # key_manager.add_expired_key("test_key")
    # key_manager.add_expired_key("test_key2")
    keys = ["test_key3", "test_key2"]
    current_keys = key_manager.get_not_expired_keys(keys, recovering_time=None)

    print("Валидные ключи:", current_keys)
