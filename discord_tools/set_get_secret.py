import os


def set_secret(key, value):
    os.environ[key] = value
def get_secret(key):
    return os.environ.get(key)