from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import asyncio
import time


class Discord_User:
    def __init__(self, username_on_this_server, driver=None, login="", password=""):
        if driver is None:
            self.driver = driver = webdriver.Chrome()
            driver.get(f"https://discord.com/channels/@me")
        else:
            self.driver = driver

        self.messages_was = []
        self.username_on_this_server = username_on_this_server

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.markup_a7e664.editor__66464.slateTextArea__0661c.fontSize16Padding__48818"))
            )
            print("[DS-LOGIN] Уже выполнен вход")
            return
        except:
            pass

        print("[DS-LOGIN] Вход...")

        try:
            continue_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                'button.marginTop8__83d4b.marginCenterHorz__4cf72.linkButton_ba7970.button_afdfd9.lookLink__93965.lowSaturationUnderline__95e71.colorLink_b651e5.sizeMin__94642.grow__4c8a4'))
            )
            continue_button.click()
            time.sleep(0.5)
        except Exception:
            # print("no continue key")
            pass

        try:
            login_button_1 = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                'button.button_afdfd9.lookFilled__19298.colorPrimary__6ed40.sizeMedium_c6fa98.grow__4c8a4'))
            )
            login_button_1.click()
            print("[DS-LOGIN] Нужно войти снова")
            time.sleep(0.5)
        except Exception as e:
            # print("no need enter", e)
            pass

        try:
            email_input = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                     'input.inputDefault__80165.input_d266e7'))
            )[0]
            email_input.click()

            email_input.send_keys(login)

            driver.save_screenshot("QR.png")
            print("[DS-LOGIN] QR сохранён")

            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                     'input.inputDefault__80165.input_d266e7'))
            )[1]
            password_field.click()
            password_field.send_keys(password)

            login_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                'button.marginBottom8_f4aae3.button__47891.button_afdfd9.lookFilled__19298.colorBrand_b2253e.sizeLarge__9049d.fullWidth__7c3e8.grow__4c8a4'))
            )
            login_button.click()

            # если есть 2-х факторка
            try:
                time.sleep(0.75)
                auth_code_field = driver.find_element(By.CSS_SELECTOR, "input.inputDefault__80165.input_d266e7")
                auth_code_field.send_keys(input("6-значный код подтверждения:"))
                time.sleep(3)
                button = driver.find_element(By.CSS_SELECTOR,
                                             "button.button_afdfd9.lookFilled__19298.colorBrand_b2253e.sizeMedium_c6fa98.grow__4c8a4")
                button.click()
            except Exception as e:
                # print("no auth code", str(e)[:50])
                pass

        except Exception:
            print("[DS-LOGIN] Не требуется вход")
            return
        if login is None or password is None:
            raise "Не указан логин или пароль в параметрах login, password"

    async def write_imitate(self):
        chat_keyboard = self.driver.find_element(By.CSS_SELECTOR,
                                                 "div.markup_a7e664.editor__66464.slateTextArea__0661c.fontSize16Padding__48818")
        chat_keyboard.click()

        chat_keyboard.send_keys(" ")
        while True:
            chat_keyboard.send_keys(" ")
            await asyncio.sleep(1)
            chat_keyboard.send_keys(Keys.BACKSPACE)

    async def write(self, text, mension=None):
        driver = self.driver

        chat_keyboard = driver.find_element(By.CSS_SELECTOR,
                                            "div.markup_a7e664.editor__66464.slateTextArea__0661c.fontSize16Padding__48818")
        chat_keyboard.click()
        for i in range(4):
            chat_keyboard.send_keys(Keys.BACKSPACE)

        if mension:
            try:
                actions = ActionChains(driver)
                actions.move_to_element(mension).perform()
                await asyncio.sleep(0.1)
                reply_buttons_ui = mension.find_elements(By.CSS_SELECTOR,
                                                         "div.button_d553e5")
                for reply_button_ui in reply_buttons_ui:
                    try:
                        # print(reply_button_ui.get_attribute('aria-label'))
                        if reply_button_ui.get_attribute('aria-label') == "Ответить":
                            reply_button_ui.click()
                    except:
                        print("error id(3)")
                try:
                    mention_button = driver.find_element(By.CSS_SELECTOR,
                                                         "div.text-sm-bold__33e9d.mentionButton_a470c4")
                    mention_button.click()
                except Exception:
                    print("Нет кнопки упоминания, это личные сообщения.")
                    chat_keyboard.send_keys("@silent ")
            except Exception:
                print("Не удалось нажать на кнопку ответа")
                # continue
        chat_keyboard.send_keys(text)
        chat_keyboard.send_keys(Keys.ENTER)

    async def get_new_local_messages(self):
        messages_was = self.messages_was
        driver = self.driver

        # список
        users_list = driver.find_elements(By.CSS_SELECTOR, "li.channel_c21703.container__8759a")
        for user in users_list:
            try:
                # панели пользователей
                check_item = user.find_element(By.CSS_SELECTOR, "a.link__2e8e1")
                label = check_item.get_attribute('aria-label')
                if "не прочитано" in label:
                    print("Найдено непрочитанное сообщение!")
                    # переход в чат
                    check_item.click()

                    username = user.find_element(By.CSS_SELECTOR, "div.overflow__87fe8").text

                    # ждём минуту, пока загрузятся сообщения
                    messages = WebDriverWait(driver, 60).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                             "li.messageListItem__6a4fb")))

                    for message in messages:
                        part_message = message.find_element(By.CSS_SELECTOR, "div.contents_f41bb2")
                        message_from_user = part_message.find_element(By.CSS_SELECTOR,
                                                                      "div.markup_a7e664.messageContent__21e69").text
                        if message == messages[:-1]:
                            last_message = message_from_user

                        message_time = await self.get_message_time(message)

                        messages_was.append({message_from_user, message_time})
                    print(messages_was)
                    return username, last_message
            except Exception as e:
                return None, None

    async def get_new_chat_message(self, limit=10):
        """
                        message_from_user = message_data['message_from_user']
                        message_username = message_data['message_username']
                        username_reply = message_data['username_reply']
                        user_reply = message_data['user_reply']
                        message_time = message_data['message_time']
                        current_message = message_found # webdriver element
        """
        driver = self.driver
        messages_was = self.messages_was

        messages = driver.find_elements(By.CSS_SELECTOR, "li.messageListItem__6a4fb")[-limit:]

        for message in messages:
            try:
                part_message = message.find_element(By.CSS_SELECTOR, "div.contents_f41bb2")
                message_from_user = part_message.find_element(By.CSS_SELECTOR,
                                                              "div.markup_a7e664.messageContent__21e69").text

                message_time = await self.get_message_time(message)

                if {message_from_user, message_time} in messages_was:
                    continue

                try:
                    message_username = part_message.find_element(By.CSS_SELECTOR,
                                                                 "span.username_d30d99.desaturateUserColors_b72bd3.clickable_d866f1").text
                except:
                    # если отправлено пару сообщений подряд
                    messages_last = driver.find_elements(By.CSS_SELECTOR, "li.messageListItem__6a4fb")[
                                    ::-1]

                    for message_temp in messages_last:
                        try:
                            message_username = message_temp.find_element(By.CSS_SELECTOR,
                                                                         "span.username_d30d99.desaturateUserColors_b72bd3.clickable_d866f1").text
                            break
                        except:
                            pass
                        # странно, если будет ошибка
                        message_username = ""

                # новое сообщение
                messages_was.append({message_from_user, message_time})

                # если есть ответ на какое-то сообщение
                user_reply, username_reply = "", ""
                try:
                    part_reply = message.find_element(By.CSS_SELECTOR, "div.repliedMessage_e2bf4a")
                    user_reply = \
                        part_reply.find_elements(By.CSS_SELECTOR, "div.markup_a7e664.messageContent__21e69")[
                            0].text
                    username_reply = part_reply.find_element(By.CSS_SELECTOR,
                                                             "span.username_d30d99.desaturateUserColors_b72bd3.clickable_d866f1").text
                    print(
                        f"({message_time}) Сообщение от {message_username}:{message_from_user}, ответ на: {username_reply}: {user_reply}")
                except:
                    print(f"({message_time}) Сообщение от {message_username}:{message_from_user}")

                message_data = {
                    'message_from_user': message_from_user,
                    'message_username': message_username,
                    'username_reply': username_reply,
                    'user_reply': user_reply,
                    'message_time': message_time
                }

                message_found = message
            except:
                pass

            return message_data, message_found

    def solve_capha(self):
        driver = self.driver
        captcha_frame = driver.find_element(By.CSS_SELECTOR, "iframe")
        captcha_frame.click()

        submit_button = driver.find_element(by=By.CSS_SELECTOR, value="iframe").click()
        captcha_check = driver.find_element(by=By.CSS_SELECTOR, value="body.no-selection")
        x_coordinate, y_coordinate = 344, 537
        driver.execute_script(f"window.scrollTo({x_coordinate}, {y_coordinate});")

    async def get_new_chat_messages(self, limit=10):
        """
            for i, message_data in enumerate(messages_data):
                message_from_user = message_data['message_from_user']
                message_username = message_data['message_username']
                username_reply = message_data['username_reply']
                user_reply = message_data['user_reply']
                message_time = message_data['message_time']
                current_message = messages_found[i] # webdriver element
        """

        driver = self.driver
        messages_was = self.messages_was

        messages = driver.find_elements(By.CSS_SELECTOR, "li.messageListItem__6a4fb")[-limit:]

        message_data = []
        messages_found = []

        for message in messages:
            try:
                part_message = message.find_element(By.CSS_SELECTOR, "div.contents_f41bb2")
                message_from_user = part_message.find_element(By.CSS_SELECTOR,
                                                              "div.markup_a7e664.messageContent__21e69").text

                message_time = await self.get_message_time(message)
                if {message_from_user, message_time} in messages_was:
                    continue

                try:
                    message_username = part_message.find_element(By.CSS_SELECTOR,
                                                                 "span.username_d30d99.desaturateUserColors_b72bd3.clickable_d866f1").text
                except:
                    # если отправлено пару сообщений подряд
                    messages_last = driver.find_elements(By.CSS_SELECTOR, "li.messageListItem__6a4fb")[
                                    ::-1]

                    for message_temp in messages_last:
                        try:
                            message_username = message_temp.find_element(By.CSS_SELECTOR,
                                                                         "span.username_d30d99.desaturateUserColors_b72bd3.clickable_d866f1").text
                            break
                        except:
                            pass
                        # странно, если будет ошибка
                        message_username = "", "???"

                # новое сообщение
                messages_was.append({message_from_user, message_time})

                # если есть ответ на какое-то сообщение
                user_reply, username_reply = "", ""
                try:
                    part_reply = message.find_element(By.CSS_SELECTOR, "div.repliedMessage_e2bf4a")
                    user_reply = \
                        part_reply.find_elements(By.CSS_SELECTOR, "div.markup_a7e664.messageContent__21e69")[
                            0].text
                    username_reply = part_reply.find_element(By.CSS_SELECTOR,
                                                             "span.username_d30d99.desaturateUserColors_b72bd3.clickable_d866f1").text
                    print(
                        f"({message_time}) Сообщение от {message_username}:{message_from_user}, ответ на: {username_reply}: {user_reply}")
                except:
                    print(f"({message_time}) Сообщение от {message_username}:{message_from_user}")

                message_data.append({
                    'message_from_user': message_from_user,
                    'message_username': message_username,
                    'username_reply': username_reply,
                    'user_reply': user_reply,
                    'message_time': message_time
                })
                messages_found.append(message)
            except:
                pass

        return message_data, messages_found

    async def append_old_messages(self, limit=20):
        driver = self.driver
        messages_was = self.messages_was

        try:
            messages = driver.find_elements(By.CSS_SELECTOR, "li.messageListItem__6a4fb")[-limit:]
            for message in messages:
                part_message = message.find_element(By.CSS_SELECTOR, "div.contents_f41bb2")
                message_from_user = part_message.find_element(By.CSS_SELECTOR,
                                                              "div.markup_a7e664.messageContent__21e69").text
                message_time = await self.get_message_time(message)
                messages_was.append({message_from_user, message_time})
            print(messages_was)
        except Exception as e:
            print("error!", e)

    async def get_message_time(self, message):
        message_time = '???'
        try:
            message_time = message.find_element(By.CSS_SELECTOR, "span.timestamp_cdbd93.timestampInline__470e0").text
        except:
            try:
                message_time = message.find_element(By.CSS_SELECTOR, "time").get_attribute('aria-label')
            except Exception as e:
                print(e)
                pass
        message_time = message_time[message_time.rfind(" ") + 1:]

        # print("time", message_time)

        return message_time

    async def set_reaction(self, message, req_reaction, find_with_filter=True):
        driver = self.driver

        actions = ActionChains(driver)
        actions.move_to_element(message).perform()
        driver.execute_script("arguments[0].click();", message)
        await asyncio.sleep(0.5)

        message_buttons = message.find_elements(by=By.CSS_SELECTOR, value="div.button_d553e5")
        for message_button in message_buttons:
            if message_button.get_attribute('aria-label') == "Добавить реакцию":
                driver.execute_script("arguments[0].click();", message_button)

        await asyncio.sleep(0.5)
        if find_with_filter:
            keyboard_emoji = driver.find_element(By.CSS_SELECTOR, "input.input_f4043f")
            keyboard_emoji.send_keys(req_reaction)
        await asyncio.sleep(1.5)

        # ЭТО 1-ЫЙ РЯД РЕАКЦИЙ, ТАК ЧТО ДОБАВЬТЕ НУЖНУЮ В "ИЗБРАННОЕ"
        reaction_lists = driver.find_elements(by=By.CSS_SELECTOR,
                                              value="ul.emojiListRow__3f54c.emojiListRowMediumSize_ebc612")

        for reaction_list in reaction_lists:
            for reaction in reaction_list.find_elements(by=By.CSS_SELECTOR, value="li"):
                try:
                    text_reaction_row = reaction.find_element(by=By.CSS_SELECTOR,
                                                              value="button.emojiItem_b15dee.emojiItemMedium_a97ee4")
                    text_reaction = text_reaction_row.get_attribute('data-name')
                    print(text_reaction)
                    if text_reaction in req_reaction:
                        text_reaction_row.click()
                        print("pressed", text_reaction)
                        break
                except Exception:
                    pass
