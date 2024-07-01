import asyncio
import base64
import hashlib
import json
import os
import requests
import time
from functools import wraps
from typing import Dict, Callable, Awaitable

from discord_tools.translate import Languages


class CryptomusPaymentStatus:
    """
    The payment status comes in the response body of some methods
    and indicates at what stage the payment is at the moment.
    """

    PAID = "paid"
    PAID_OVER = "paid_over"
    WRONG_AMOUNT = "wrong_amount"
    PROCESS = "process"
    CONFIRM_CHECK = "confirm_check"
    WRONG_AMOUNT_WAITING = "wrong_amount_waiting"
    CHECK = "check"
    FAIL = "fail"
    CANCEL = "cancel"
    SYSTEM_FAIL = "system_fail"
    REFUND_PROCESS = "refund_process"
    REFUND_FAIL = "refund_fail"
    REFUND_PAID = "refund_paid"
    LOCKED = "locked"

    successful = [PAID, PAID_OVER]
    not_successful = [WRONG_AMOUNT, PROCESS, CONFIRM_CHECK, WRONG_AMOUNT_WAITING, CHECK, FAIL, CANCEL, SYSTEM_FAIL,
                      REFUND_FAIL, REFUND_PROCESS,
                      REFUND_PAID, LOCKED]


class CryptomusPaymentAPI:
    BASE_URL = "https://api.cryptomus.com/v1"

    def __init__(self, merchant_id: str, api_key: str, json_file="cryptomus_pays.json"):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.payment_handler = None
        self.json_file = json_file

        if not os.path.exists(json_file):
            with open(json_file, "w", encoding="utf-8") as writer:
                writer.write("[]")

    async def run(self, check_time=30):
        asyncio.create_task(self._start_check(check_time=check_time))

    async def _start_check(self, check_time=30):
        while True:
            with open(self.json_file, "r", encoding="utf-8") as reader:
                data = json.loads(reader.read())

            changed = False

            for item in data:
                if item["order_done"]:
                    continue

                order_id = item["order_id"]
                currency = item["currency"]
                amount = item["amount"]

                payment_status = await asyncio.to_thread(self.check_pay, order_id)

                print(f"payment status: {payment_status}, order_id: {order_id}")

                if payment_status in CryptomusPaymentStatus.successful:
                    await self.payment_handler(order_id, amount, currency)
                    item["order_done"] = True
                    changed = True
                elif payment_status == CryptomusPaymentStatus.CANCEL:
                    item["order_done"] = True
                    changed = True

            if changed:
                with open(self.json_file, "w", encoding="utf-8") as writer:
                    writer.write(json.dumps(data, ensure_ascii=False, indent=4))

            await asyncio.sleep(check_time)

    def handle_payment(self, func: Callable[[str, str, str], Awaitable[None]]):
        @wraps(func)
        async def wrapper(order_id, amount, currency):
            return await func(order_id, amount, currency)

        self.payment_handler = wrapper
        return wrapper

    def add_item(self, order_id: str, amount: str, currency: str):
        with open(self.json_file, "r", encoding="utf-8") as reader:
            data = json.load(reader)

        new_item = {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "order_done": False
        }
        data.append(new_item)

        with open(self.json_file, "w", encoding="utf-8") as writer:
            json.dump(data, writer, ensure_ascii=False, indent=4)

    def _create_signature(self, payload: Dict) -> str:
        """
        Генерация подписи для запроса к API Cryptomus.

        :param payload: Данные запроса в формате словаря.
        :return: Сгенерированная подпись.
        """
        data_json = json.dumps(payload)
        data_base64 = base64.b64encode(data_json.encode()).decode()
        sign_str = data_base64 + self.api_key
        sign_hash = hashlib.md5(sign_str.encode()).hexdigest()
        return sign_hash

    def get_payment_url(self, user_id: [str, int], amount: [str, float], currency: str = "RUB", order_id: str = None,
                        add_checker=True) -> str:
        user_id = str(user_id)
        amount = str(amount)

        if order_id is None:
            order_id = f"{user_id}_{int(time.time())}"

        payload = {
            "amount": amount,
            "currency": currency,
            "order_id": order_id,
        }

        headers = {
            "merchant": self.merchant_id,
            "sign": self._create_signature(payload),
            "Content-Type": "application/json"
        }

        response = requests.post(f"{self.BASE_URL}/payment", json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data["state"] == 0:
            if add_checker:
                self.add_item(order_id=order_id, amount=amount, currency=currency)
            return response_data["result"]["url"]
        else:
            raise Exception(f"Failed to create payment: {response_data.get('message', 'Unknown error')}")

    def check_pay(self, order_id: str = None, uuid: str = None):
        if not order_id and not uuid:
            raise ValueError("Either order_id or uuid must be provided")

        payload = {}
        if order_id:
            payload["order_id"] = order_id
        if uuid:
            payload["uuid"] = uuid

        headers = {
            "merchant": self.merchant_id,
            "sign": self._create_signature(payload),
            "Content-Type": "application/json"
        }

        response = requests.post(f"{self.BASE_URL}/payment/info", json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data["state"] == 0:
            return response_data["result"]['status']
        else:
            raise Exception(f"Failed to check payment status: {response_data.get('message', 'Unknown error')}")


class FreeKassaPaymentAPI:
    def __init__(self, merchant_id, secret_word_1, secret_word_2):
        self.merchant_id = merchant_id
        self.secret_word_1 = secret_word_1
        self.secret_word_2 = secret_word_1
        self.payment_handler = None

    def handle_payment(self, func: Callable[[str, str, str], Awaitable[None]]):
        @wraps(func)
        async def wrapper(order_id, amount, currency):
            return await func(order_id, amount, currency)

        self.payment_handler = wrapper
        return wrapper

    def generate_signature_from_server(self, order_amount, order_id):
        data = f"{self.merchant_id}:{order_amount}:{self.secret_word_2}:{order_id}"
        signature = hashlib.md5(data.encode()).hexdigest()
        return signature

    def _generate_signature_to_server(self, order_amount, currency, order_id):
        data = f"{self.merchant_id}:{order_amount}:{self.secret_word_1}:{currency}:{order_id}"
        print("data:", data)
        signature = hashlib.md5(data.encode()).hexdigest()
        return signature

    def get_payment_url(self, order_amount: [float, str, int], user_id: [str, int], currency='RUB', lang=Languages.ru):
        order_id = f"{user_id}_{int(time.time())}"
        signature = self._generate_signature_to_server(order_amount, currency, order_id)
        return f"https://pay.freekassa.ru/?m={self.merchant_id}&oa={order_amount}&o={order_id}&s={signature}&currency={currency}&i=&lang={lang}"


# CRYPTOMUS
async def main():
    payment_api = CryptomusPaymentAPI(merchant_id="cryptomus_merchant_id", api_key="cryptomus_api_key")

    @payment_api.handle_payment
    async def payment_handler(order_id: str, amount: str, currency: str):
        user_id = order_id.split("_")[0]
        print(f"Payment completed: User_id={user_id}, Amount={amount}, Currency={currency}")

    await payment_api.run()

    # Создание платежа и получение URL
    try:
        payment_url = await asyncio.to_thread(payment_api.get_payment_url, user_id="123", amount="15.00",
                                              currency="RUB")
        print(f"Payment URL: {payment_url}")
    except Exception as e:
        print(f"Error creating payment: {e}")

    await asyncio.sleep(600)


if __name__ == "__main__":
    asyncio.run(main())

# FREE KASSA
if __name__ == '__main__':
    free_kassa_payment_api = FreeKassaPaymentAPI(merchant_id="merchant_id",
                                                 secret_word_1="secret_word_1",
                                                 secret_word_2="secret_word_2")
    user_id = '123'
    order_amount = '300'
    payment_link = free_kassa_payment_api.get_payment_url(user_id=user_id, order_amount=order_amount)
    print(payment_link)


    @free_kassa_payment_api.handle_payment
    async def payment_handler(order_id: str, amount: str, currency: str):
        user_id = order_id.split("_")[0]
        print(f"Payment completed: User_id={user_id}, Amount={amount}, Currency={currency}")

    # Add flask server to handle payment

    # @app.route('/notification', methods=['GET'])
    # def notification():
    #     def add_to_json_file(filename, data):
    #         try:
    #             with open(filename, "r") as file:
    #                 existing_data = json.load(file)
    #         except FileNotFoundError:
    #             existing_data = []
    #
    #         existing_data.append(data)
    #
    #         with open(filename, "w") as file:
    #             json.dump(existing_data, file)
    #
    #         # Ваш код для обработки оповещения о платеже
    #         request_json = request.args.to_dict()
    #         # Добавление данных запроса в JSON файл
    #         print(f"Полученные заголовки: {request_json}")
    #
    #         order_id = request_json['MERCHANT_ORDER_ID']
    #         currency = 'RUB'
    #         order_amount = request_json['AMOUNT']
    #
    #         sing_original = free_kassa_payment_api.generate_signature_from_server(order_amount=order_amount,
    #                                                                   order_id=order_id)
    #
    #         if sing_original == request_json['SIGN']:
    #             asyncio.run(free_kassa_payment_api.payment_handler(order_id=order_id, amount=order_amount, currency=currency))
    #
    #         add_to_json_file("notification.json", request_json)
    #         return "YES"
    #
    #
    # def run_flask_server():
    #     app.run(host='0.0.0.0', port=80)
