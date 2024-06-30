import requests


def get_exchange_rate(value='USD'):
    try:
        url = 'https://www.cbr-xml-daily.ru/daily_json.js'
        response = requests.get(url)
        data = response.json()

        if value in data['Valute']:
            cny_to_rub = data['Valute'][value]['Value']
            return cny_to_rub
    except Exception as e:
        print("get_exchange_rate ERROR:", e)
