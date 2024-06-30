import asyncio
import base64
import hashlib
import json
import os
import requests
import time
from functools import wraps
from typing import Dict, Callable, Awaitable


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


# Пример использования
async def main():
    payment_api = CryptomusPaymentAPI(merchant_id="cryptomus_merchant_id", api_key="cryptomus_api_key")

    @payment_api.handle_payment
    async def payment_handler(order_id: str, amount: str, currency: str):
        user_id = order_id.split("_")[0]
        print(f"Payment completed: User_id={user_id}, Amount={amount}, Currency={currency}")

    await payment_api.run()

    # Создание платежа и получение URL
    try:
        payment_url = await asyncio.to_thread(payment_api.get_payment_url, user_id="123", amount="15.00", currency="RUB")
        print(f"Payment URL: {payment_url}")
    except Exception as e:
        print(f"Error creating payment: {e}")

    await asyncio.sleep(600)


if __name__ == "__main__":
    asyncio.run(main())
