import random
import requests
import string


class Imsys_Text_Models:
    claude_3_haiku_20240307 = "claude-3-haiku-20240307"
    claude_3_sonnet_20240229 = "claude-3-sonnet-20240229"
    claude_3_opus_20240229 = "claude-3-opus-20240229"
    claude_2_1 = "claude-2.1"
    command_r_plus = "command-r-plus"
    command_r = "command-r"
    gemma_1_1_7b_it = "gemma-1.1-7b-it"
    gemma_7b_it = "gemma-7b-it"
    mixtral_8x7b_instruct_v0_1 = "mixtral-8x7b-instruct-v0.1"
    mistral_large_2402 = "mistral-large-2402"
    mistral_medium = "mistral-medium"
    mistral_7b_instruct_v0_2 = "mistral-7b-instruct-v0.2"
    qwen1_5_72b_chat = "qwen1.5-72b-chat"
    qwen1_5_32b_chat = "qwen1.5-32b-chat"
    qwen1_5_14b_chat = "qwen1.5-14b-chat"
    qwen1_5_7b_chat = "qwen1.5-7b-chat"
    qwen1_5_4b_chat = "qwen1.5-4b-chat"
    dbrx_instruct = "dbrx-instruct"
    starling_lm_7b_beta = "starling-lm-7b-beta"
    gemini_pro_dev_api = "gemini-pro-dev-api"
    gpt_4_turbo_2024_04_09 = "gpt-4-turbo-2024-04-09"
    gpt_4_1106_preview = "gpt-4-1106-preview"
    gpt_3_5_turbo_0125 = "gpt-3.5-turbo-0125"
    gpt_3_5_turbo_0613 = "gpt-3.5-turbo-0613"
    llama_2_70b_chat = "llama-2-70b-chat"
    llama_2_13b_chat = "llama-2-13b-chat"
    llama_2_7b_chat = "llama-2-7b-chat"
    olmo_7b_instruct = "olmo-7b-instruct"
    vicuna_33b = "vicuna-33b"
    vicuna_13b = "vicuna-13b"
    yi_34b_chat = "yi-34b-chat"
    codellama_70b_instruct = "codellama-70b-instruct"
    openchat_3_5_0106 = "openchat-3.5-0106"
    deepseek_llm_67b_chat = "deepseek-llm-67b-chat"
    openhermes_2_5_mistral_7b = "openhermes-2.5-mistral-7b"
    zephyr_7b_beta = "zephyr-7b-beta"


class Imsys_API:
    def __init__(self, history_id=0, text_model=Imsys_Text_Models.claude_3_opus_20240229):
        random.seed(history_id)
        self.session_hash = "hlle038h65l" #''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        self.cookie = "_gid=GA1.2.995177409.1712817245; __cf_bm=qVFlvI7gD2DUehhTvYtFjHdrhwyBhLwsIXnxXbm6FIY-1712824552-1.0.1.1-R4B1jUE1OTPwiUog.d4xejaUy_e6qDs4vSxJCZ7jKGZlxD.el9bSJA5kAPpQBLvU0J3okLB80iSiaySWXalp5g; cf_clearance=lqemFtpKmqEtgxDO2Uh.5B9wbbUVc.ROB9PCXTkVseo-1712824593-1.0.1.1-MS0BKMpovy9wKAFff5zBnSYHrT0nEi.FiJJ_.gzfQj1x4XIgtvIlXPANnG6qS0kDxwZ.XnZc1oD06HE8EkgRiA; _ga=GA1.1.425464416.1712817241; _ga_R1FN4KJKJH=GS1.1.1712823431.3.1.1712824600.0.0.0; _ga_K6D24EE9ED=GS1.1.1712823431.3.1.1712824663.0.0.0; SERVERID=S4|ZhehX"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        self.text_model = text_model

        if self.text_model is None:
            self.trigger_id = 32
        else:
            self.trigger_id = 93

        self.fn_index = 12
    def r_join(self, prompt=None):
        url = "https://chat.lmsys.org/queue/join"


        if prompt is None:
            data = [None, 0.7, 1, 1024]
            querystring = {"": ""}
        else:
            querystring = None
            if self.text_model is None:
                data = [None, None, "", "", prompt]
            else:
                data = [None, self.text_model, prompt, None]
        print(data)
        payload = {
            "data": data,
            "event_data": None,
            "fn_index": self.fn_index,
            "trigger_id": self.trigger_id,
            "session_hash": self.session_hash
        }
        self.fn_index += 1

        headers = {
            "cookie": self.cookie,
            "user-agent": self.user_agent
        }

        print("Send")
        if querystring:
            print("has queue ")
            response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        else:
            response = requests.request("POST", url, json=payload, headers=headers)

        print(response.text)

        # if prompt is None and self.text_model is None:
        #     self.check_answer()
        #     payload = {
        #         "data": [],
        #         "event_data": None,
        #         "fn_index": self.fn_index,
        #         "trigger_id": self.trigger_id,
        #         "session_hash": self.session_hash
        #     }
        #     self.fn_index += 1
        #     print("Send")
        #     response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        #     print(response.text)

    def check_answer(self):
        print("check answer")
        url = "https://chat.lmsys.org/queue/data"

        querystring = {"session_hash": self.session_hash}

        payload = ""
        headers = {
            "cookie": self.cookie,
            "accept": "text/event-stream",
            "user-agent": self.user_agent
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        print(response.text)

    def get_answer(self):
        import requests

        url = "https://chat.lmsys.org/queue/data"

        querystring = {"session_hash": self.session_hash}

        payload = ""
        headers = {
            "cookie": self.cookie,
            "accept": "text/event-stream",
            "user-agent": self.user_agent
        }

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        if "RATE LIMIT OF THIS MODEL IS REACHED" in response.text:
            raise Exception("Лимит запросов. Используйте 'text_model=None', чтобы обойти ограничение!")

        print("GET_ANSWER", response.text)


def run_imsys(prompt, history_id=2, text_model=None):
    for model in [None]:
        try:
            test = Imsys_API(history_id=history_id, text_model=model)
            test.r_join(prompt)
            test.check_answer()
            test.r_join()
            test.check_answer()
            return test.get_answer()
        except Exception as e:
            print("Ignote error:", e)

run_imsys("HELLO!")
