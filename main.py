import time
import json
import content
import config as cf
import telebot as tb
from telebot_users import UsersCRUD
from datetime import datetime as dt, timedelta
from colorama import Fore as pFore, Back as pBack, init as init_colorama
from telebot.types import InlineKeyboardMarkup as tbMarkup, InlineKeyboardButton as tbButton
from matplotlib import pyplot as plt
import matplotlib
import openai
import requests
import easyocr
import soundfile as sf
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import yahoo_fin.stock_info as si
import yoomoney as ym
import psutil
import sys
import os


bot = tb.TeleBot(cf.TELEGRAM_API_KEY)


def cprint(text: str, color: str = None):
    try:
        print({"r": pFore.RED, "g": pFore.GREEN, "wr": pBack.RED, "wg": pBack.GREEN}[color] + text)
    except KeyError:
        print(text)


def logging(data, path: str = cf.LOGS_DIR):
    with open(path, "a") as file:
        file.write(f"{data}//datetime: {dt.now()}\n")


def get_dir_size(path: str):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total


def token_price():
    if "usd_to_rub_live_price" in CACHE and (dt.now() - CACHE["usd_to_rub_live_price"]["update"]).seconds <= 86000:
        usd_to_rub = CACHE["usd_to_rub_live_price"]["price"]
    else:
        try:
            usd_to_rub = si.get_live_price("USDRUB=X")
        except Exception as ex:
            usd_to_rub = CACHE["usd_to_rub_live_price"]["price"] if ex else ...
        CACHE["usd_to_rub_live_price"] = {"price": usd_to_rub, "update": dt.now()}
    return round(usd_to_rub * 0.002 / 1000 * cf.TOKEN_RATE_MULTIPLIER, 8)


class TelebotUser:
    def __init__(self, user_id, user_name):
        self.id = user_id
        self.name = user_name

    def get_profile(self):
        return TU.read_user(f"{self.id}")

    def get_history(self):
        return TU.read_user_history(f"{self.id}")

    def get_profile_text_info(self):
        p = self.get_profile()
        days = (dt.strptime(p["last_limit_reset"], "%Y-%m-%d %H:%M:%S.%f") -
                dt.strptime(p["last_limit_reset"], "%Y-%m-%d %H:%M:%S.%f")
                + timedelta(days=p["days_before_resetting_tokens"])).days
        return f"🔐 <b><i>Личный кабинет:</i></b>\n\n" \
               f"👤 Имя: <b>{self.name} (ID: {self.id})</b>\n\n" \
               f"💎 Баланс токенов: <b>{p['tokens']}</b>\n" \
               f"💰 Внутренний баланс: <b>{p['balance']}</b>\n" \
               f"👥 Прямые реферралы: <b>{len(p['ref_users'])}</b>\n" \
               f"🫂 Дочерние реферралы: <b>{len(p['sub_ref_users'])}</b>\n" \
               f"📍 Реферальный баланс: <b>{p['ref_balance']}</b>\n" \
               f"💸 Получено от рефералов: <b>{p['ref_amount']}</b>\n" \
               f"🗓 Дней до начисления токенов: <b>{days}</b>\n" \
               f"🗃 Буфер контекста: <b>{len(p['context'])}/{p['max_context_size']}</b>\n" \
               f"ℹ️ Статус: <b>{p['status']}</b>\n"

    def get_settings_text_info(self):
        p = self.get_profile()
        return f"⚙️ <b><i>Настройки:</i></b>\n\n" \
               f"🔥 Параметр температуры: <b>{p['temperature']}</b>\n"  \
               f"🈂️ Автоматический перевод: <b>{'ON' if p['translation'] else 'OFF'}</b>\n"  \
               f"🗣 Озвучка бота: <b>{'ON' if p['voice_acting'] else 'OFF'}</b>\n"  \
               f"🎭 Роль бота: <b>{p['role']}</b>"

    def get_settings_markup(self):
        p = self.get_profile()
        return tbMarkup().add(
                tbButton("🔥Изменить параметр температуры", callback_data="temperature"),
                tbButton("🟥Откл. автоматический перевод" if p["translation"] else "🟩Вкл. автоматический перевод",
                         callback_data="translation"),
                tbButton("🔇Отключить озвучку бота" if p["voice_acting"] else "🔊Включить озвучку бота",
                         callback_data="voice_acting"),
                tbButton(f"🎭Выбрать роль бота", callback_data="roles_page=0"), row_width=1).add(
                tbButton("⬅️ Назад", callback_data="client"))

    def get_text_balance(self):
        p = self.get_profile()
        return f"💎 Баланс токенов: <b>{p['tokens']}</b>\n" \
               f"💰 Внутренний баланс: <b>{p['balance']}</b>\n" \
               f"📍 Реферальный баланс: <b>{p['ref_balance']}</b>"

    def get_top_up_balance_markup(self):
        p = self.get_profile()
        if f"{len(p['payments'])}_{self.id}" in CACHE:
            payments = CACHE[f"{len(p['payments'])}_{self.id}"]
        else:
            payments = []
            for i in content.PAYMENTS_BUTTONS:
                payments.append(tbButton(i, url=ym.Quickpay(
                    receiver=ym_receiver, quickpay_form="shop", targets="Sponsor this project", paymentType="SB",
                    sum=content.PAYMENTS_BUTTONS[i], label=f"{len(p['payments'])}_{self.id}").base_url))
            CACHE[f"{len(p['payments'])}_{self.id}"] = payments
        return tbMarkup().add(
            *payments, row_width=2).add(tbButton("🔄 Проверить оплату", callback_data="payment_verification")).add(
            tbButton("⬅️ Назад", callback_data="payment"),
            tbButton("🔄 Обновить", callback_data="top_up_balance"), row_width=2)

    def get_context_text_info(self):
        p = self.get_profile()
        context_info = "Сохраненный контекст:\n\n" if len(p["context"]) > 0 \
            else f"Сохраненный контекст:\n\nБуфер: <b>0/{p['max_context_size']}</b>\n<b>Пусто</b>\n"
        context_total_tokens = 0
        for n, c in enumerate(p["context"]):
            context_info += f"Буфер: <b>{n+1}/{p['max_context_size']}</b>\nПользователь: " \
                            f"{c['request'][:40]}...\nАссистент: {c['response'][:40]}...\n"
            context_total_tokens += c["total_tokens"]
        context_info += f"\nОбщая стоимость контекста: <b>{context_total_tokens}</b> токена\n" \
                        f"Максимальный буфер контекста: <b>{p['max_context_size']}</b>"
        return context_info

    def context_buffer_markup(self):
        p = self.get_profile()
        mcs, mcb = p["max_context_size"], p["max_context_buffer"]
        return tbMarkup().add(
            tbButton("🟢 0 (Откл.)" if mcs == 0 else "0 (Откл.)", callback_data="max_context_size=0"),
            tbButton("🟢 1" if mcs == 1 else "1" if mcb >= 1 else "1🔒",
                     callback_data="max_context_size=" + ("1" if mcb >= 1 else "None")),
            tbButton("🟢 2" if mcs == 2 else "2" if mcb >= 2 else "2🔒",
                     callback_data="max_context_size=" + ("2" if mcb >= 2 else "None")),
            tbButton("🟢 3" if mcs == 3 else "3" if mcb >= 3 else "3🔒",
                     callback_data="max_context_size=" + ("3" if mcb >= 3 else "None")),
            tbButton("🟢 4" if mcs == 4 else "4" if mcb >= 4 else "4🔒",
                     callback_data="max_context_size=" + ("4" if mcb >= 4 else "None")),
            tbButton("🟢 5" if mcs == 5 else "5" if mcb >= 5 else "5🔒",
                     callback_data="max_context_size=" + ("5" if mcb >= 5 else "None")),
            tbButton("⬅️ Назад", callback_data="context"), row_width=2)

    def get_temperature_markup(self):
        p = self.get_profile()
        return tbMarkup().add(
            tbButton("🟢 0" if p["temperature"] == 0 else "0", callback_data="temperature=0"),
            tbButton("🟢 0.1" if p["temperature"] == 0.1 else "0.1", callback_data="temperature=0.1"),
            tbButton("🟢 0.2" if p["temperature"] == 0.2 else "0.2", callback_data="temperature=0.2"),
            tbButton("🟢 0.3" if p["temperature"] == 0.3 else "0.3", callback_data="temperature=0.3"),
            tbButton("🟢 0.4" if p["temperature"] == 0.4 else "0.4", callback_data="temperature=0.4"),
            tbButton("🟢 0.5" if p["temperature"] == 0.5 else "0.5", callback_data="temperature=0.5"),
            tbButton("🟢 0.6" if p["temperature"] == 0.6 else "0.6", callback_data="temperature=0.6"),
            tbButton("🟢 0.7" if p["temperature"] == 0.7 else "0.7", callback_data="temperature=0.7"),
            tbButton("🟢 0.8" if p["temperature"] == 0.8 else "0.8", callback_data="temperature=0.8"),
            tbButton("🟢 0.9" if p["temperature"] == 0.9 else "0.9", callback_data="temperature=0.9"),
            row_width=2).add(tbButton("⬅️ Назад", callback_data="settings"))

    def get_roles_markup(self):
        p = self.get_profile()
        with open(cf.ROLES_DIR, "r") as f:
            roles = json.load(f)
        roles_list, markups = list(roles.keys()), {}
        n_pages = int(str(len(roles_list) / 10).split(".")[0]) + 1
        for n in range(n_pages):
            markups[str(n)] = []
            for i in range(0 + (n * 10), 10 + (n * 10)):
                try:
                    markups[str(n)].append(tbButton(f"🟢 {roles_list[i]}" if p['role'] == roles_list[i]
                                                    else roles_list[i], callback_data=f"role={roles_list[i]}={n}"))
                except IndexError:
                    markups[str(n)].append(tbButton("None", callback_data="None"))
            markups[str(n)] = tbMarkup().add(*markups[str(n)], row_width=2)
            if n < n_pages - 1:
                markups[str(n)].add(tbButton("Следующая страница ➡️", callback_data=f"roles_page={n + 1}"))
            markups[str(n)].add(tbButton(
                "⬅️ Назад", callback_data="settings" if n == 0 else f"roles_page={n - 1}"))
        return markups

    def checking_token_balance(self):
        p = self.get_profile()
        days_after_token_reset = (dt.now() - dt.strptime(p["last_limit_reset"], "%Y-%m-%d %H:%M:%S.%f")).days
        if days_after_token_reset >= p["days_before_resetting_tokens"]:
            p["tokens"] = max([p["limit_tokens"], p["tokens"]])
            p["last_limit_reset"] = str(dt.now())
            TU.update_user(f"{self.id}", p)
        if p["tokens"] <= 0:
            bot.send_message(self.id, f"⚠️  У вас не осталось токенов! Токены обновятся через "
                                      f"{p['days_before_resetting_tokens'] - days_after_token_reset} дней.")
            cprint(f"{self.name}_{self.id} not enough tokens...", "r")
            return False
        return True

    def get_statistics(self):
        def compilation_statistics(s):
            return {"text": f"📈 Всего запросов: <b>{s['total_requests']}</b>\n"
                            f"💬 Количество запросов Chat GPT: <b>{s['gpt_requests']}</b>\n" 
                            f"🖼 Количество запросов на генерацию картинок: <b>{s['image_requests']}</b>\n\n" 
                            f"📍 Всего потрачено токенов: <b>{s['sum_total_tokens']}</b>\n" 
                            f"📍 Среднее значение токенов на один запрос: <b>{s['avg_total_tokens']}</b>\n\n" 
                            f"💬 Средняя длина запроса: <b>{s['avg_requests']} симв.</b>\n" 
                            f"💬 Средняя длина ответа: <b>{s['avg_responses']} симв.</b>\n\n" 
                            f"🗣 Голосовых запросов: <b>{s['voice_request_method_count']}</b>\n" 
                            f"🗣 Голосовых ответов: <b>{s['voice_response_method_count']}</b>\n" 
                            f"📝 Текстовых запросов: <b>{s['text_request_method_count']}</b>\n" 
                            f"📝 Текстовых ответов: <b>{s['text_response_method_count']}</b>\n\n" 
                            f"⏱  Дата и время первого/последнего запроса:\n"
                            f"<b>{s['first_request_dt']}/{s['last_request_dt']}</b>\n",
                    "plt_path": s["plt_statistics_queries_path"],
                    "total_tokens_plt_path": s["plt_total_tokens_queries_path"]}
        h = self.get_history()
        if len(h) < 1:
            return None
        cache_key = f"{self.id}_history_{h[-1]['datetime']}"
        if cache_key in CACHE:
            return compilation_statistics(CACHE[cache_key])
        stat = {"total_requests": len(h), "gpt_requests": 0, "image_requests": 0,
                "dt_list": [], "dt_requests": None, "sum_total_tokens": 0, "sum_requests": 0,
                "sum_responses": 0, "voice_request_method_count": 0, "text_request_method_count": 0,
                "voice_response_method_count": 0, "text_response_method_count": 0,
                "first_request_dt": h[0]["datetime"].split(".")[0],
                "last_request_dt": h[-1]["datetime"].split(".")[0], "total_tokens_list": [0]}
        for i in h:
            stat["dt_list"].append(dt.strptime(i["datetime"].split(" ")[0], "%Y-%m-%d"))
            stat["total_tokens_list"].append(i["total_tokens"])
            stat["sum_total_tokens"] += i["total_tokens"]
            stat["sum_requests"] += len(i["request"])
            stat["sum_responses"] += len(i["response"])
            if i["type"] == "gpt":
                stat["gpt_requests"] += 1
            elif i["type"] == "image":
                stat["image_requests"] += 1
            if i["request_method"] == "voice":
                stat["voice_request_method_count"] += 1
            elif i["request_method"] == "text":
                stat["text_request_method_count"] += 1
            if i["response_method"] == "voice":
                stat["voice_response_method_count"] += 1
            elif i["response_method"] == "text":
                stat["text_response_method_count"] += 1
        stat["set_dt"] = list(set(stat["dt_list"]))
        stat["dt_requests"] = [stat["dt_list"].count(i) for i in stat["set_dt"]]
        stat["avg_total_tokens"] = round(stat["sum_total_tokens"] / stat["total_requests"])
        stat["avg_requests"] = round(stat["sum_requests"] / stat["total_requests"])
        stat["avg_responses"] = round(stat["sum_responses"] / stat["gpt_requests"])
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        ax.bar(stat["set_dt"], stat["dt_requests"], color="#666666")
        plt.gcf().autofmt_xdate()
        ax.set_title('Дневная гистограмма запросов')
        plt.xlabel("Дата")
        plt.ylabel("Количество запросов")
        plt.savefig(f"{TU.users_dir}//{self.id}//plt_statistics_queries.png")
        stat["plt_statistics_queries_path"] = f"{TU.users_dir}//{self.id}//plt_statistics_queries.png"
        plt.close(fig)
        if stat["total_requests"] > 100:
            stat["total_tokens_list"] = stat["total_tokens_list"][stat["total_requests"] - 100:]
            plt.title("График расхода токенов\n100 последних запросов")
        else:
            plt.title("График расхода токенов")
        plt.plot(range(len(stat["total_tokens_list"])), stat["total_tokens_list"], color="#ffffff")
        plt.xlabel("Номер запроса")
        plt.ylabel("Количество токенов")
        plt.savefig(f"{TU.users_dir}//{self.id}//plt_total_tokens_queries.png")
        plt.close()
        stat["plt_total_tokens_queries_path"] = f"{TU.users_dir}//{self.id}//plt_total_tokens_queries.png"
        if sys.getsizeof(CACHE) < cf.CACHE_MAX_SIZE:
            CACHE[cache_key] = stat
        else:
            CACHE.clear()
            CACHE[cache_key] = stat
        return compilation_statistics(CACHE[cache_key])


class TelebotAdmin:
    def __init__(self, admin_id):
        self.id = admin_id

    def get_admin_panel(self):
        stat = {"reg_dt": [], "ref_amount": [], "balance": [], "payments": []}
        users = TU.read_oll_users()
        for i in users:
            stat["ref_amount"].append(users[i]["ref_amount"])
            stat["balance"].append(users[i]["balance"])
            stat["reg_dt"].append(dt.strptime(users[i]["registration_date"].split(" ")[0], "%Y-%m-%d"))
            for p in users[i]["payments"]:
                stat["payments"].append(users[i]["payments"][p])
        stat["dt_users"] = [stat["reg_dt"].count(i) for i in set(stat["reg_dt"])]
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        ax.bar(list(set(stat["reg_dt"])), stat["dt_users"], color="#666666")
        plt.gcf().autofmt_xdate()
        ax.set_title("Дневная гистограмма регистраций")
        plt.xlabel("Дата")
        plt.ylabel("Количество регистраций")
        plt.savefig(f"{TU.users_dir}//{self.id}//plt_users.png")
        plt.close(fig)
        with open(cf.OPENAI_KEYS_DIR, "r") as f:
            openai_keys = json.load(f)
        divider = 1024**3
        memory_use = round(psutil.Process(os.getpid()).memory_info()[0] / divider, 2)
        users_dir_size = round(get_dir_size(TU.users_dir) / divider, 4)
        text = f"👥 Всего пользователей: {len(TU.users)}\n" \
               f"Сумма реферального баланса пользователей: {sum(stat['ref_amount'])}\n" \
               f"Сумма внутреннего баланса пользователей: {sum(stat['balance'])}\n" \
               f"Сумма пополнений баланса пользователей: {sum(stat['payments'])}\n" \
               f"Всего пополнений: {len(stat['payments'])}\n" \
               f"🔑 Осталось ключей openai: {len(openai_keys)}\n" \
               f"💰 YooMoney баланс: {YMc.account_info().balance}\n" \
               f"📁 Размер директории пользователей: {users_dir_size} GB\n" \
               f"🖥 Потребление оперативной памяти: {memory_use} GB\n"
        return {"text": text, "plt_users_path": f"{TU.users_dir}//{self.id}//plt_users.png"}

    def get_oll_users_txt(self):
        users = TU.read_oll_users()
        with open(f"{TU.users_dir}//{self.id}//read_oll_users.txt", "w") as f:
            f.write(f"{json.dumps(users, indent=4, sort_keys=True, ensure_ascii=False)}")
        return f"{TU.users_dir}//{self.id}//read_oll_users.txt"

    def get_users_history_txt(self):
        users_history = TU.read_oll_users_history()
        with open(f"{TU.users_dir}//{self.id}//read_oll_users_history.txt", "w") as f:
            f.write(f"{json.dumps(users_history, indent=4, sort_keys=True, ensure_ascii=False)}")
        return f"{TU.users_dir}//{self.id}//read_oll_users_history.txt"


class GPT(Translator):
    def __init__(self):
        super().__init__()
        with open(cf.OPENAI_KEYS_DIR, "r") as f:
            self.api_keys = json.load(f)
        openai.api_key = self.api_keys[0]

    def request(self, prompt: str, translation: bool = False, context: list = None,
                role: str = "Без роли", temperature: float = 0.1, max_tokens: int = 1200):
        def t(text: str):
            if not translation:
                return text
            return self.translate(text, dest="en").text if self.detect(text).lang != "en" else text
        messages = []
        with open(cf.ROLES_DIR, "r") as f:
            roles = json.load(f)
        if roles[role]:
            messages.append({"role": "system", "content": roles[role]})
        if context:
            for i in context:
                messages.append({"role": "user", "content": t(i["request"])})
                messages.append({"role": "assistant", "content": t(i["response"])})
        messages.append({"role": "user", "content": t(prompt)})
        try:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages,
                                                    temperature=temperature, max_tokens=max_tokens)
        except openai.error.RateLimitError:
            self.delete_current_key()
            openai.api_key = self.api_keys[0]
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages,
                                                    temperature=temperature, max_tokens=max_tokens)
        re_content = response["choices"][0]["message"]["content"]
        return {"content": self.translate(re_content, dest="ru").text if translation else re_content,
                "total_tokens": int(response["usage"]["total_tokens"])}

    def image_request(self, prompt: str, translation: bool = False):
        if translation:
            prompt = self.translate(prompt, dest="en").text \
                if self.detect(prompt).lang != "en" else prompt
        try:
            url = openai.Image.create(prompt=prompt, n=1, size="1024x1024", )["data"][0]["url"]
        except openai.error.RateLimitError:
            self.delete_current_key()
            openai.api_key = self.api_keys[0]
            url = openai.Image.create(prompt=prompt, n=1, size="1024x1024", )["data"][0]["url"]
        return url

    def delete_current_key(self):
        self.api_keys = self.api_keys[1:]
        with open(cf.OPENAI_KEYS_DIR, "w") as f:
            json.dump(self.api_keys, f, indent=4)


@bot.message_handler(commands=cf.TB_COMMANDS)
def commands_handler(m):
    user = TelebotUser(m.chat.id, m.chat.username)
    cprint(f"{user.name}_{user.id} {m.text} command request processing attempt...")
    logging(f"{user.name}_{user.id} {m.text.rstrip()}  command request...")
    read_user = user.get_profile()
    if read_user["status"] == "ban":
        bot.send_message(user.id, "❗️ Пользователь заблокирован ❗️")
        return
    if "/start" in m.text:
        read_user["user_name"] = user.name
        TU.update_user(f"{user.id}", read_user)
        ref_id = m.text.replace("/start", "").replace(" ", "")
        if len(ref_id) > 4 and ref_id in TU.users and ref_id != f"{user.id}" and not read_user["ref_parent"] \
                and (dt.now() - dt.strptime(read_user["registration_date"], "%Y-%m-%d %H:%M:%S.%f")).seconds < 60:
            read_user["ref_parent"] = ref_id
            TU.update_user(f"{user.id}", read_user)
            ref_parent = TU.read_user(ref_id)
            if f"{user.id}" not in ref_parent["ref_users"]:
                ref_parent["ref_users"].append(f"{user.id}")
            TU.update_user(ref_id, ref_parent)
            if ref_parent["ref_parent"]:
                sub_ref_parent = TU.read_user(ref_parent["ref_parent"])
                if f"{user.id}" not in sub_ref_parent["sub_ref_users"]:
                    sub_ref_parent["sub_ref_users"].append(f"{user.id}")
                TU.update_user(ref_parent["ref_parent"], sub_ref_parent)
        bot.send_message(m.chat.id, f"{content.START_MESSAGE}", reply_markup=content.START_MESSAGE_MARKUP)
    elif m.text == "/client":
        bot.send_message(m.chat.id, user.get_profile_text_info(),
                         reply_markup=content.CLIENT_MARKUP, parse_mode="HTML")
    elif m.text == "/a":
        if read_user["status"] == "admin":
            admin = TelebotAdmin(user.id)
            admin_panel = admin.get_admin_panel()
            with open(admin_panel["plt_users_path"], 'rb') as f:
                bot.send_photo(m.chat.id, f, caption=admin_panel["text"], reply_markup=content.ADMIN_PANEL_MARKUP)
    elif "/cmd" in m.text:
        try:
            def send_oll(message_, photo_url_=None):
                for u_ in TU.users:
                    try:
                        if photo_url_:
                            resource = requests.get(photo_url_)
                            with open(f"{TU.users_dir}//{user.id}//send_img.jpg", "wb") as f_:
                                f_.write(resource.content)
                            with open(f"{TU.users_dir}//{user.id}//send_img.jpg", 'rb') as f_:
                                bot.send_photo(int(u_), f_, caption=message_)
                        else:
                            bot.send_message(int(u_), message_)
                    except tb.apihelper.ApiTelegramException:
                        pass
                return "send_oll"

            def ban_user(id_):
                read_user_ = TU.read_user(f"{id_}")
                read_user_["status"] = "ban"
                TU.update_user(f"{id_}", read_user_)
                return f"the user {id_} is blocked"

            def unban_user(id_):
                read_user_ = TU.read_user(f"{id_}")
                read_user_["status"] = cf.START_USER_STATUS
                TU.update_user(f"{id_}", read_user_)
                return f"user {id_} unlocked"

            def set_user(id_, key_, set_):
                read_user_ = TU.read_user(f"{id_}")
                read_user_[key_] = set_
                TU.update_user(f"{id_}", read_user_)
                return f"user {id_} {key_} = {set_}\n" \
                       f"{json.dumps(read_user_, indent=4, sort_keys=True, ensure_ascii=False)}"

            def get_user(id_):
                return f"{json.dumps(TU.read_user(f'{id_}'), indent=4, sort_keys=True, ensure_ascii=False)}"

            def get_user_history(id_):
                return f"{json.dumps(TU.read_user_history(f'{id_}'), indent=4, sort_keys=True, ensure_ascii=False)}"

            def get_oll_users_id():
                return f"{json.dumps(TU.users, indent=4, sort_keys=True, ensure_ascii=False)}"

            def add_role(key_, promt_):
                with open(cf.ROLES_DIR, "r") as f_:
                    roles_ = json.load(f_)
                roles_[key_] = promt_
                with open(cf.ROLES_DIR, "w") as f_:
                    json.dump(roles_, f_, indent=4)
                return f"{json.dumps(roles_, indent=4, ensure_ascii=False)}"

            def dell_role(key_):
                with open(cf.ROLES_DIR, "r") as f_:
                    roles_ = json.load(f_)
                del roles_[key_]
                with open(cf.ROLES_DIR, "w") as f_:
                    json.dump(roles_, f_, indent=4)
                return f"{json.dumps(roles_, indent=4, ensure_ascii=False)}"

            def get_roles():
                with open(cf.ROLES_DIR, "r") as f_:
                    return f"{json.dumps(json.load(f_), indent=4, ensure_ascii=False)}"

            if read_user["status"] == "admin":
                try_eval = m.text.replace("/cmd", "")
                while try_eval[0] == " ":
                    try_eval = try_eval[1:]
                try:
                    try_eval = eval(try_eval, {
                        "bot": bot, "users": TU, "send_oll": send_oll, "send": bot.send_message,
                        "ban": ban_user, "unban": unban_user, "set_user": set_user, "get_user": get_user,
                        "get_user_history": get_user_history, "get_oll_users_id": get_oll_users_id,
                        "add_role": add_role, "dell_role": dell_role, "get_roles": get_roles, })
                    try:
                        bot.send_message(m.chat.id, f"Вывод консоли: {try_eval}")
                    except tb.apihelper.ApiTelegramException:
                        with open(f"{TU.users_dir}//{user.id}//send_document.txt", "w") as f:
                            f.write(f"{try_eval}")
                        with open(f"{TU.users_dir}//{user.id}//send_document.txt", "r") as f:
                            bot.send_document(m.chat.id, f)
                except Exception as ex:
                    bot.send_message(m.chat.id, f"Вывод консоли: {ex}")
        except Exception as ex:
            bot.send_message(m.chat.id, f"Вывод консоли: {ex}")
    elif m.text == "/clear_context":
        if len(read_user["context"]) > 0:
            read_user["context"].clear()
            TU.update_user(f"{user.id}", read_user)
            bot.send_message(m.chat.id, f"✅ Контекст очищен!")
        else:
            bot.send_message(m.chat.id, f"⚠️ Контекст уже очищен!")
    elif "/create_image" in m.text:
        try:
            if not user.checking_token_balance():
                return
            image_prompt = m.text.replace("/create_image", "")
            if len(image_prompt) < 4:
                cprint(f"{user.id} insufficient request length...", "r")
                bot.send_message(m.chat.id, f"⚠️  Количество символов для запроса должно быть больше 3!\n"
                                            f"Пример: /create_image Звездное небо.")
                return
            while image_prompt[0] == " ":
                image_prompt = image_prompt[1:]
            if read_user["tokens"] < cf.TOKENS_PER_PICTURE:
                cprint(f"{m.chat.username}_{user.id} not enough tokens...", "r")
                bot.send_message(m.chat.id, f"⚠️  Недостаточно токенов для генерации изображения!")
                return
            bot.send_message(m.chat.id, "⏳  Генерация изображения...")
            bot.send_chat_action(m.chat.id, "upload_photo", 7)
            url_image = GPTc.image_request(image_prompt, read_user["translation"])
            bot.send_message(m.chat.id, f"🖼  Ссылка на готовое изображение: {url_image}",
                             reply_markup=content.REMAKE_IMAGE_MARKUP)
            user_history = user.get_history()
            user_history.append({"type": "gpt", "datetime": str(dt.now()), "role": None, "request": image_prompt,
                                 "response": url_image, "total_tokens": cf.TOKENS_PER_PICTURE,
                                 "request_method": "text", "response_method": "url"})
            TU.update_user_history(f"{user.id}", user_history)
            read_user["tokens"] -= cf.TOKENS_PER_PICTURE
            TU.update_user(f"{user.id}", read_user)
            cprint(f"{user.name}_{user.id} gpt request completed:\n"
                   f"prompt='{image_prompt}'\nimage_response='{url_image}'", "g")
        except Exception as ex:
            logging(f"ERROR: {ex}")
            cprint(f"{m.chat.username}_{user.id} the image request failed: {ex}", "r")
            bot.send_message(m.chat.id, f"⚠️  Что-то пошло не так! Попробуйте повторить попытку позже.\n"
                                        f"ERROR: {ex.__str__()}")
    elif "/pay" in m.text:
        try:
            pay = float(m.text.replace("/pay", ""))
            bot.send_message(m.chat.id, f"Invoice:", reply_markup=tbMarkup().add(
                tbButton(f"Оплатить {pay}", url=ym.Quickpay(
                    receiver=ym_receiver, quickpay_form="shop", targets="Sponsor this project", paymentType="SB",
                    sum=pay, label=f"{len(read_user['payments'])}_{user.id}").base_url),
                tbButton("🔄 Проверить оплату", callback_data="payment_verification"), row_width=1))
        except Exception as ex:
            if ex:
                bot.send_message(m.chat.id, f"⚠️  Параметр donat не определен!\n"
                                            f"Укажите сумму оплаты через пробел после команды pay.\n"
                                            f"Пример: /pay 74.45")
    cprint(f"{user.name}_{user.id} {m.text} command processing completed", "g")


@bot.callback_query_handler(func=lambda call: True)
def callback(c):
    user = TelebotUser(c.message.chat.id, c.message.chat.username)
    cprint(f"{user.name}_{user.id} {c.data} callback request attempt...")
    logging(f"{user.name}_{user.id} {c.data.rstrip()} callback request...")
    read_user = user.get_profile()
    if read_user["status"] == "ban":
        bot.send_message(user.id, "❗️ Пользователь заблокирован ❗️")
        return
    if c.data == "client":
        bot.edit_message_text(user.get_profile_text_info(), user.id, c.message.message_id,
                              reply_markup=content.CLIENT_MARKUP, parse_mode="HTML")
    elif c.data == "statistics":
        try:
            user_statistics = user.get_statistics()
            bot.delete_message(c.message.chat.id, c.message.message_id)
            if user_statistics:
                with open(user_statistics["plt_path"], "rb") as f:
                    bot.send_photo(c.message.chat.id, f, user_statistics["text"],
                                   reply_markup=content.STATISTICS_MARKUP, parse_mode="HTML")
            else:
                bot.send_message(c.message.chat.id, "⚠️  Недостаточно данных для формирования статистики!",
                                 reply_markup=content.STAT_BACK_CLIENT_MARKUP)
        except Exception as ex:
            bot.send_message(c.message.chat.id, f"⚠️  Что-то пошло не так! Попробуйте повторить попытку позже.\n"
                                                f"ERROR: {ex.__str__()}", reply_markup=content.STAT_BACK_CLIENT_MARKUP)
    elif c.data == "plt_total_tokens":
        user_statistics = user.get_statistics()
        with open(user_statistics["total_tokens_plt_path"], "rb") as f:
            bot.edit_message_media(tb.types.InputMediaPhoto(f, user_statistics["text"], parse_mode="HTML"),
                                   c.message.chat.id, c.message.message_id,
                                   reply_markup=content.STAT_BACK_CLIENT_MARKUP)
    elif c.data == "statistics_back_client":
        bot.delete_message(c.message.chat.id, c.message.message_id)
        bot.send_message(c.message.chat.id, user.get_profile_text_info(),
                         reply_markup=content.CLIENT_MARKUP, parse_mode="HTML")
    elif c.data == "payment":
        bot.edit_message_text(f"{user.get_text_balance()}\n\n{content.PAYMENT_INFO}", user.id,
                              c.message.message_id, reply_markup=content.PAYMENT_MARKUP, parse_mode="HTML")
    elif c.data == "top_up_balance":
        try:
            bot.edit_message_text(f"{user.get_text_balance()}\n\n{content.TOP_UP_BALANCE_INFO}",
                                  user.id, c.message.message_id,
                                  reply_markup=user.get_top_up_balance_markup(), parse_mode="HTML")
        except tb.apihelper.ApiTelegramException:
            pass
    elif c.data == "buy_tokens":
        try:
            bot.edit_message_text(f"{user.get_text_balance()}\n\n📉 Курс токена на сегодня: "
                                  f"{round(token_price() * 1000, 2)} руб. за 1000 токенов.\n\n🛒 Купить токены:",
                                  user.id, c.message.message_id,
                                  reply_markup=content.BUY_TOKENS_MARKUP, parse_mode="HTML")
        except tb.apihelper.ApiTelegramException:
            pass
    elif "confirm_buy_tokens=" in c.data:
        buy_tokens = int(c.data.split("=")[1])
        price = token_price() * buy_tokens
        if read_user["balance"] >= price:
            read_user["balance"] = round(read_user["balance"] - token_price() * buy_tokens, 2)
            read_user["tokens"] += buy_tokens
            TU.update_user(f"{user.id}", read_user)
            bot.edit_message_text(f"✅ Покупка подтверждена!\nНа счет зачислено {buy_tokens} токенов.", user.id,
                                  c.message.message_id, reply_markup=content.CLOSE_MARKUP)
        else:
            bot.edit_message_text(f"❗️ Недостаточно средств!", user.id,
                                  c.message.message_id, reply_markup=content.INSUFFICIENT_FUNDS_MARKUP)
    elif "buy_tokens=" in c.data:
        buy_tokens = int(c.data.split("=")[1])
        bot.send_message(user.id, f"Цена: {round(token_price() * buy_tokens, 2)} руб.\n"
                                  f"Подтвердите покупку {buy_tokens} токенов:",
                         reply_markup=tbMarkup().add(
                             tbButton("✅ Подтвердить", callback_data=f"confirm_buy_tokens={buy_tokens}"),
                             tbButton("⛔️ Отклонить", callback_data="close"), row_width=2))
    elif c.data == "withdrawal_of_funds":
        bot.edit_message_text(f"{user.get_text_balance()}\n\n{content.WITHDRAWAL_OF_FUNDS_INFO}",
                              user.id, c.message.message_id,
                              reply_markup=content.WITHDRAWAL_OF_FUNDS_MARKUP, parse_mode="HTML")
    elif c.data == "settings":
        bot.edit_message_text(user.get_settings_text_info(), user.id, c.message.message_id,
                              reply_markup=user.get_settings_markup(), parse_mode="HTML")
    elif c.data == "temperature":
        bot.edit_message_text(f"{user.get_settings_text_info()}\n\n{content.TEMPERATURE_INFO}",
                              user.id, c.message.message_id,
                              reply_markup=user.get_temperature_markup(), parse_mode="HTML")
    elif "temperature=" in c.data:
        if read_user["temperature"] != float(c.data.split("=")[1]):
            read_user["temperature"] = float(c.data.split("=")[1])
            TU.update_user(f"{user.id}", read_user)
            bot.edit_message_text(f"{user.get_settings_text_info()}\n\n{content.TEMPERATURE_INFO}", user.id,
                                  c.message.message_id, reply_markup=user.get_temperature_markup(), parse_mode="HTML")
    elif c.data == "translation":
        read_user["translation"] = not read_user["translation"]
        TU.update_user(f"{user.id}", read_user)
        bot.edit_message_text(user.get_settings_text_info(), user.id, c.message.message_id,
                              reply_markup=user.get_settings_markup(), parse_mode="HTML")
    elif c.data == "voice_acting":
        read_user["voice_acting"] = not read_user["voice_acting"]
        TU.update_user(f"{user.id}", read_user)
        bot.edit_message_text(user.get_settings_text_info(), user.id, c.message.message_id,
                              reply_markup=user.get_settings_markup(), parse_mode="HTML")
    elif "roles_page=" in c.data:
        bot.edit_message_text(f"{user.get_settings_text_info()}\n\n{content.ROLE_INFO}", user.id, c.message.message_id,
                              reply_markup=user.get_roles_markup()[c.data.split("=")[1]], parse_mode="HTML")
    elif "role=" in c.data:
        if read_user["role"] != c.data.split("=")[1]:
            read_user["role"] = c.data.split("=")[1]
            TU.update_user(f"{user.id}", read_user)
            bot.edit_message_text(f"{user.get_settings_text_info()}\n\n{content.ROLE_INFO}",
                                  user.id, c.message.message_id,
                                  reply_markup=user.get_roles_markup()[c.data.split("=")[2]], parse_mode="HTML")
    elif c.data == "context":
        bot.edit_message_text(f"{content.CONTEXT_INFO}\n\n{user.get_context_text_info()}",
                              c.message.chat.id, c.message.message_id,
                              reply_markup=content.CONTEXT_MARKUP, parse_mode="HTML")
    elif c.data == "clear_context":
        if len(read_user["context"]) > 0:
            read_user["context"].clear()
            TU.update_user(f"{user.id}", read_user)
            bot.edit_message_text(f"{content.CONTEXT_INFO}\n\n{user.get_context_text_info()}",
                                  c.message.chat.id, c.message.message_id,
                                  reply_markup=content.CONTEXT_MARKUP, parse_mode="HTML")
    elif c.data == "context_buffer":
        bot.edit_message_text(f"{c.message.text}\n\n{content.CONTEXT_BUFFER_INFO}", c.message.chat.id,
                              c.message.message_id, reply_markup=user.context_buffer_markup(), parse_mode="HTML")
    elif "max_context_size" in c.data:
        try:
            if read_user["max_context_size"] != int(c.data.split("=")[1]):
                read_user["max_context_size"] = int(c.data.split("=")[1])
                TU.update_user(f"{user.id}", read_user)
                bot.edit_message_text(f"{content.CONTEXT_INFO}\n\n{user.get_context_text_info()}\n\n"
                                      f"{content.CONTEXT_BUFFER_INFO}",
                                      c.message.chat.id, c.message.message_id,
                                      reply_markup=user.context_buffer_markup(), parse_mode="HTML")
        except ValueError:
            pass
    elif c.data == "check_channel_sub":
        if not read_user["channel_subscription"]:
            try:
                bot.get_chat_member(cf.CHANNEL_TELEGRAM_ID, user.id)
                bot.send_message(c.message.chat.id, f"✅ Подписка подтверждена!\n"
                                                    f"На ваш баланс зачислено {cf.SUBSCRIPTION_REWARD} руб.")
                read_user["channel_subscription"] = True
                read_user["balance"] += cf.SUBSCRIPTION_REWARD
                TU.update_user(f"{user.id}", read_user)
            except tb.apihelper.ApiTelegramException:
                bot.send_message(c.message.chat.id, f"⛔️ Подпишитесь на канал!",
                                 reply_markup=content.CHANNEL_SUBSCRIPTION_MARKUP)
    elif c.data == "bot_info":
        bot.edit_message_text(content.BOT_INFO, user.id, c.message.message_id,
                              reply_markup=content.BOT_INFO_MARKUP)
    elif c.data == "ref_info":
        bot.edit_message_text(content.REF_INFO, user.id, c.message.message_id,
                              reply_markup=content.REF_INFO_MARKUP)
    elif c.data == "voice_to_text":
        read_user_history = TU.read_user_history(f"{user.id}")
        bot.send_message(c.message.chat.id, read_user_history[-1]["response"])
    elif c.data == "close":
        bot.delete_message(user.id, c.message.message_id)
    elif c.data == "ref_url":
        bot.send_message(user.id, f"https://t.me/{bot.get_me().username}?start={user.id}")
    elif c.data == "settings_info":
        bot.edit_message_text(content.SETTINGS_INFO, user.id, c.message.message_id,
                              reply_markup=content.TO_BOT_INFO_MARKUP)
    elif c.data == "request_info":
        bot.edit_message_text(content.REQUEST_INFO, user.id, c.message.message_id,
                              reply_markup=content.TO_BOT_INFO_MARKUP)
    elif c.data == "support_info":
        bot.edit_message_text(content.SUPPORT_INFO, user.id, c.message.message_id,
                              reply_markup=content.SUPPORT_INFO_MARKUP)
    elif c.data == "payment_verification":
        if (dt.now() - dt.strptime(read_user["last_payment_verification"], "%Y-%m-%d %H:%M:%S.%f")).seconds >= 30:
            operations = {i.label: i.amount for i in YMc.operation_history().operations if i.label}
            if f"{len(read_user['payments'])}_{user.id}" in operations:
                amount = operations[f"{len(read_user['payments'])}_{user.id}"]
                read_user["payments"][f"{len(read_user['payments'])}_{user.id}"] = amount
                read_user["balance"] += amount
                if read_user["ref_parent"]:
                    ref_parent = TU.read_user(f"{read_user['ref_parent']}")
                    ref_amount = round(amount / 100 * read_user["ref_percent"], 2)
                    ref_parent["ref_balance"] += ref_amount
                    ref_parent["ref_amount"] += ref_amount
                    bot.send_message(read_user['ref_parent'],
                                     f"🔊 На реферальный баланс поступило {ref_amount} руб.")
                    TU.update_user(f"{read_user['ref_parent']}", ref_parent)
                    if ref_parent["ref_parent"]:
                        sub_ref_parent = TU.read_user(f"{ref_parent['ref_parent']}")
                        ref_amount = round(amount / 100 * read_user["sub_ref_percent"], 2)
                        sub_ref_parent["ref_balance"] += ref_amount
                        sub_ref_parent["ref_amount"] += ref_amount
                        bot.send_message(ref_parent['ref_parent'],
                                         f"🔊 На реферальный баланс поступило {ref_amount} руб.")
                        TU.update_user(f"{ref_parent['ref_parent']}", sub_ref_parent)
                bot.send_message(user.id, f"✅ Оплата прошла проверку.\nНа счет зачислено {amount} руб.")
            else:
                bot.send_message(user.id, f"⛔️ Оплата не прошла проверку.")
            read_user["last_payment_verification"] = str(dt.now())
            TU.update_user(f"{user.id}", read_user)
        else:
            bot.send_message(user.id, f"❗️ Запрос на проверку оплаты временно не доступен. Повторите попытку позже.")
    elif c.data == "remake_image":
        try:
            if not user.checking_token_balance():
                return
            image_prompt = c.message.text.replace("/create_image", "")
            if len(image_prompt) < 4:
                cprint(f"{user.id} insufficient request length...", "r")
                bot.edit_message_text(f"⚠️  Количество символов для запроса должно быть больше 3!\n"
                                      f"Пример: /create_image Звездное небо.", user.id, c.message.message_id)
                return
            while image_prompt[0] == " ":
                image_prompt = image_prompt[1:]
            if read_user["tokens"] < cf.TOKENS_PER_PICTURE:
                cprint(f"{c.message.chat.username}_{user.id} not enough tokens...", "r")
                bot.edit_message_text(f"⚠️  Недостаточно токенов для генерации изображения!",
                                      user.id, c.message.message_id)
                return
            bot.edit_message_text("⏳  Генерация изображения...", user.id, c.message.message_id)
            bot.send_chat_action(c.message.chat.id, "upload_photo", 7)
            url_image = GPTc.image_request(image_prompt, read_user["translation"])
            bot.edit_message_text(f"🖼  Ссылка на готовое изображение: {url_image}", user.id, c.message.message_id,
                                  reply_markup=content.REMAKE_IMAGE_MARKUP)
            user_history = user.get_history()
            user_history.append({"type": "gpt", "datetime": str(dt.now()), "role": None, "request": image_prompt,
                                 "response": url_image, "total_tokens": cf.TOKENS_PER_PICTURE,
                                 "request_method": "text", "response_method": "url"})
            TU.update_user_history(f"{user.id}", user_history)
            read_user["tokens"] -= cf.TOKENS_PER_PICTURE
            TU.update_user(f"{user.id}", read_user)
            cprint(f"{user.name}_{user.id} gpt request completed:\n"
                   f"prompt='{image_prompt}'\nimage_response='{url_image}'", "g")
        except Exception as ex:
            logging(f"ERROR: {ex}")
            cprint(f"{c.message.chat.username}_{user.id} the image request failed: {ex}", "r")
            bot.edit_message_text(f"⚠️  Что-то пошло не так! Попробуйте повторить попытку позже.\n"
                                  f"ERROR: {ex.__str__()}", user.id, c.message.message_id)
    elif c.data == "admin_panel":
        if user.get_profile()["status"] == "admin":
            admin = TelebotAdmin(user.id)
            admin_panel = admin.get_admin_panel()
            with open(admin_panel["plt_users_path"], 'rb') as f:
                bot.delete_message(user.id, c.message.message_id)
                bot.send_photo(c.message.chat.id, f, caption=admin_panel["text"],
                               reply_markup=admin_panel["markup"])
    elif c.data == "admin_panel_doc":
        if user.get_profile()["status"] == "admin":
            bot.send_message(user.id, f"📄 Документация консоли:\n\n{content.CMD_DOC}",
                             reply_markup=content.CLOSE_MARKUP)
    elif c.data == "get_user_profiles":
        if user.get_profile()["status"] == "admin":
            admin = TelebotAdmin(user.id)
            with open(admin.get_oll_users_txt(), "rb") as f:
                bot.send_document(user.id, f)
    elif c.data == "get_users_history":
        if user.get_profile()["status"] == "admin":
            admin = TelebotAdmin(user.id)
            with open(admin.get_users_history_txt(), "rb") as f:
                bot.send_document(user.id, f)
    elif c.data == "get_logs":
        if user.get_profile()["status"] == "admin":
            with open(cf.LOGS_DIR, "rb") as f:
                bot.send_document(user.id, f)
    elif c.data == "clear_logs":
        if user.get_profile()["status"] == "admin":
            try:
                os.remove(cf.LOGS_DIR)
                bot.send_message(user.id, f"✅ Логи очищены!")
            except Exception as ex:
                bot.send_message(user.id, f"{ex}")
    cprint(f"{user.name}_{user.id} {c.data} callback request completed", "g")


@bot.message_handler(content_types=["photo", "video", "document"])
def any_content_types_handler(m):
    user = TelebotUser(m.chat.id, m.chat.username)
    cprint(f"{user.name}_{user.id} {m.content_type} request processing attempt...")
    logging(f"{user.name}_{user.id} {m.content_type} request...")
    read_user = user.get_profile()
    if read_user["status"] == "ban":
        bot.send_message(user.id, "❗️ Пользователь заблокирован ❗️")
        return
    if m.content_type == "photo":
        if not user.checking_token_balance():
            return
        info_message_id = bot.send_message(m.chat.id, f"⏳  Обработка запроса...").message_id
        bot.send_chat_action(m.chat.id, "record_voice" if read_user["voice_acting"] else "typing", 9)
        with open(f"{TU.users_dir}//{user.id}//ocr.jpg", "wb") as new_file:
            new_file.write(bot.download_file(bot.get_file(m.photo[len(m.photo)-1].file_id).file_path))
        ocr_result = easyocr.Reader(["en", "ru"]).readtext(f"{TU.users_dir}//{user.id}//ocr.jpg", detail=0)
        prompt = f"{m.caption}\n" + "\n".join(ocr_result)
        gpt_response = GPTc.request(prompt, read_user["translation"], None, read_user["role"],
                                    read_user["temperature"], read_user["max_tokens"])
        txt_content, total_tokens = gpt_response["content"], gpt_response["total_tokens"]
        if read_user["voice_acting"]:
            try:
                tts = gTTS(txt_content, lang=Translator().detect(gpt_response).lang)
                tts.save(f"{TU.users_dir}//{user.id}//voice_response.mp3")
                with open(f"{TU.users_dir}//{user.id}//voice_response.mp3", 'rb') as f:
                    bot.delete_message(m.chat.id, info_message_id)
                    bot.send_voice(m.chat.id, f, reply_markup=content.VOICE_TO_TEXT_MARKUP)
                response_method = "voice"
            except Exception as ex:
                response_method = "text"
                cprint(f"{user.name}_{user.id} the text was not spoken...", "r")
                logging(f"ERROR: {ex}")
                bot.edit_message_text(f"⚠️  Что-то пошло не так! Текст не был озвучен.\n"
                                      f"ERROR: {ex.__str__()}\ngpt_response:\n\n"
                                      f"{gpt_response}", m.chat.id, info_message_id)
        else:
            try:
                bot.edit_message_text(txt_content, m.chat.id, info_message_id)
                response_method = "text"
            except tb.apihelper.ApiTelegramException:
                response_method = "document"
                with open(f"{TU.users_dir}//{user.id}//send_document.txt", "w") as f:
                    f.write(f"{txt_content}")
                with open(f"{TU.users_dir}//{user.id}//send_document.txt", "r") as f:
                    bot.send_document(m.chat.id, f, caption="⚠️  Текст слишком большой для отправки!")
        user_history = user.get_history()
        user_history.append({"type": "gpt", "datetime": str(dt.now()), "role": read_user["role"],
                             "request": prompt, "response": txt_content, "total_tokens": total_tokens,
                             "request_method": m.content_type, "response_method": response_method})
        TU.update_user_history(f"{user.id}", user_history)
        read_user["tokens"] -= total_tokens
        TU.update_user(f"{user.id}", read_user)
        cprint(f"{user.name}_{user.id} gpt request completed:\nprompt='{prompt}'\ngpt_response='{gpt_response}'", "g")
    elif m.content_type == "video":
        bot.send_message(m.chat.id, f"⚠️  Я еще не умею обрабатывать видео!")
    elif m.content_type == "document":
        bot.send_message(m.chat.id, f"⚠️  Я еще не умею обрабатывать документы!")
    cprint(f"{user.name}_{user.id} {m.content_type} request processing completed...", "g")


@bot.message_handler(content_types=["text", "voice"])
def message_processing(m):
    user = TelebotUser(m.chat.id, m.chat.username)
    cprint(f"{user.name}_{user.id} {m.content_type} gpt request attempt...")
    logging(f"{user.name}_{user.id} {m.content_type} gpt request attempt...")
    read_user, prompt = user.get_profile(), None
    if read_user["status"] == "ban":
        bot.send_message(user.id, "❗️ Пользователь заблокирован ❗️")
        return
    if not user.checking_token_balance():
        return
    if m.content_type == "voice":
        try:
            with open(f"{TU.users_dir}//{user.id}//voice_request.ogg", 'wb') as f:
                f.write(bot.download_file(bot.get_file(m.voice.file_id).file_path))
            data, samplerate = sf.read(f"{TU.users_dir}//{user.id}//voice_request.ogg")
            sf.write(f"{TU.users_dir}//{user.id}//voice_request.wav", data, samplerate)
            rec = sr.Recognizer()
            with sr.AudioFile(f"{TU.users_dir}//{user.id}//voice_request.wav") as af:
                audio_content = rec.record(af)
            prompt = rec.recognize_google(audio_content, language="ru-RU")
        except Exception as ex:
            logging(f"ERROR: {ex}")
            cprint(f"{user.name}_{user.id} the request failed: {ex}", "r")
            bot.send_message(m.chat.id, f"⚠️  Что-то пошло не так! Ваш голос не был распознан.\n"
                                        f"ERROR: {ex.__str__()}")
    elif m.content_type == "text":
        prompt = m.text
    if not prompt:
        return
    if prompt[0] == "/":
        cprint(f"{user.name}_{user.id} command does not exist...", "r")
        bot.send_message(m.chat.id, f"⚠️  Команды {prompt} не существует!")
        return
    try:
        info_message_id = bot.send_message(m.chat.id,
                                           f"🎭 Роль бота: {read_user['role']}\n"
                                           f"🈂️ Авто перевод: {'ON' if read_user['translation'] else 'OFF'}\n"
                                           f"🗃 Буфер контекста: {len(read_user['context'])}/"
                                           f"{read_user['max_context_size']}\n\n"
                                           f"⏳  Обработка запроса...").message_id
        bot.send_chat_action(m.chat.id, "record_voice" if read_user["voice_acting"] else "typing", 9)
        gpt_response = GPTc.request(prompt, read_user["translation"], read_user["context"], read_user["role"],
                                    read_user["temperature"], read_user["max_tokens"])
        txt_content, total_tokens = gpt_response["content"], gpt_response["total_tokens"]
        if read_user["voice_acting"]:
            try:
                tts = gTTS(txt_content, lang=Translator().detect(gpt_response).lang)
                tts.save(f"{TU.users_dir}//{user.id}//voice_response.mp3")
                with open(f"{TU.users_dir}//{user.id}//voice_response.mp3", 'rb') as f:
                    bot.delete_message(m.chat.id, info_message_id)
                    bot.send_voice(m.chat.id, f, reply_markup=content.VOICE_TO_TEXT_MARKUP)
                response_method = "voice"
            except Exception as ex:
                response_method = "text"
                cprint(f"{user.name}_{user.id} the text was not spoken...", "r")
                logging(f"ERROR: {ex}")
                bot.edit_message_text(f"⚠️  Что-то пошло не так! Текст не был озвучен.\n"
                                      f"ERROR: {ex.__str__()}\ngpt_response:\n\n"
                                      f"{gpt_response}", m.chat.id, info_message_id)
        else:
            try:
                bot.edit_message_text(txt_content, m.chat.id, info_message_id)
                response_method = "text"
            except tb.apihelper.ApiTelegramException:
                response_method = "document"
                with open(f"{TU.users_dir}//{user.id}//send_document.txt", "w") as f:
                    f.write(f"{txt_content}")
                with open(f"{TU.users_dir}//{user.id}//send_document.txt", "r") as f:
                    bot.send_document(m.chat.id, f, caption="⚠️  Текст слишком большой для отправки!")
        user_history = user.get_history()
        user_history.append({"type": "gpt", "datetime": str(dt.now()), "role": read_user["role"],
                             "request": prompt, "response": txt_content, "total_tokens": total_tokens,
                             "request_method": m.content_type, "response_method": response_method})
        TU.update_user_history(f"{user.id}", user_history)
        read_user["context"].clear()
        if read_user["max_context_size"] > 0:
            for i in user_history[::-1]:
                if i["type"] == "gpt":
                    read_user["context"].append(i)
                    if len(read_user["context"]) == read_user["max_context_size"]:
                        read_user["context"] = read_user["context"][::-1]
                        break
        read_user["tokens"] -= total_tokens
        TU.update_user(f"{user.id}", read_user)
        cprint(f"{user.name}_{user.id} gpt request completed:\n"
               f"prompt='{prompt}'\ngpt_response='{gpt_response}'", "g")
    except Exception as ex:
        logging(f"ERROR: {ex}")
        cprint(f"ERROR: {ex}", "r")
        bot.send_message(m.chat.id, f"⚠️  Что-то пошло не так! Попробуйте повторить попытку позже.\n"
                                    f"ERROR: {ex.__str__()[:220]}")


def main():
    try:
        cprint(f"bot start polling...", "g")
        bot.polling(none_stop=True)
    except Exception as ex:
        logging(f"ERROR: {ex}\nmain restart...")
        cprint(f"ERROR: {ex}\nmain restart...", "r")
        bot.stop_polling()
        time.sleep(2)
        main()


if __name__ == "__main__":
    cprint("project initialization...")
    CACHE = {}
    init_colorama(autoreset=True)
    matplotlib.use("agg")
    YMc = ym.Client(cf.YOOMONEY_TOKEN)
    ym_receiver = YMc.account_info().account
    bot.set_my_commands(content.MY_COMMANDS)
    TU = UsersCRUD()
    GPTc = GPT()
    main()
