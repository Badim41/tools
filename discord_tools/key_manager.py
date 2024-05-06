import json
from datetime import datetime, timedelta


class KeyManager:
    def __init__(self, service):
        self.json_file = "expired_keys.json"
        self.service = service

    def load_keys(self):
        try:
            with open(self.json_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {self.service: []}

    def save_keys(self, keys):
        with open(self.json_file, 'w') as file:
            json.dump(keys, file, indent=4)

    def add_expired_key(self, key, expiration_date):
        keys = self.load_keys()
        keys[self.service].append({"key": key, "expired": expiration_date.strftime("%Y-%m-%d")})
        self.save_keys(keys)

    def get_not_expired_keys(self, current_keys, days_to_refresh=None):
        not_expired_keys = []
        keys = self.load_keys()

        for service in keys[self.service]:
            if service["key"] in current_keys:
                not_expired_date = datetime.strptime(service["expired"], "%Y-%m-%d")
                if days_to_refresh:
                    if not_expired_date + timedelta(days=days_to_refresh) > datetime.now():
                        not_expired_keys.append(service["key"])
                else:
                    not_expired_keys.append(service["key"])
        return not_expired_keys
