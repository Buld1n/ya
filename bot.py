import json
import os
import telebot

from telebot import types
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

ADMIN_ID = os.getenv("ADMIN_ID")

MAX_FILE_SIZE = 50 * 1024 * 1024
DATA_DIR = "data"
NEXT_STEPS_FILE = "data/next_steps.txt"


def load_data(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_data(filename, data):
    dir_name = os.path.dirname(filename)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filename, "w") as file:
        json.dump(data, file)


admin_upload = load_data("admin_upload.json")
awaiting_next_step_input = load_data("awaiting_next_step_input.json")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("/selfie")
    item2 = types.KeyboardButton("/oldphoto")
    item3 = types.KeyboardButton("/newphoto")
    item4 = types.KeyboardButton("/hobbypost")
    item5 = types.KeyboardButton("/explaingpt")
    item6 = types.KeyboardButton("/explainSQLvsNoSQL")
    item7 = types.KeyboardButton("/firstlovestory")
    item8 = types.KeyboardButton("/repolink")
    markup.add(item1, item2, item3, item4, item5, item6, item7, item8)

    if str(message.from_user.id) == ADMIN_ID:
        item9 = types.KeyboardButton("/upload")
        markup.add(item9)

    bot.send_message(
        message.chat.id,
        "Привет! Вот команды, которые ты можешь использовать: \n"
        "/selfie - для получения селфи\n"
        "/oldphoto - чтобы увидеть старое фото\n"
        "/newphoto - чтобы увидеть новое фото\n"
        "/hobbypost - чтобы узнать о хобби\n"
        "/explaingpt - чтобы услышать объяснение GPT\n"
        "/explainSQLvsNoSQL - чтобы услышать разницу SQL и NoSQL\n"
        "/firstlovestory - чтобы услышать историю любви\n"
        "/repolink - чтобы получить реп этого бота\n\n"
        "Также доступен текстовый ввод: \n"
        "селфи\n"
        "старое фото\n"
        "новое фото\n"
        "хобби\n"
        "гитхаб",
        reply_markup=markup,
    )


@bot.message_handler(commands=["upload"])
def upload(message=None):
    chat_id = ADMIN_ID if message is None else message.chat.id
    if str(chat_id) == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Selfie", callback_data="selfie")
        item2 = types.InlineKeyboardButton("Old Photo", callback_data="oldphoto")
        item3 = types.InlineKeyboardButton("New Photo", callback_data="newphoto")
        item4 = types.InlineKeyboardButton(
            "GPT Explanation", callback_data="explaingpt"
        )
        item5 = types.InlineKeyboardButton(
            "SQL vs NoSQL Explanation", callback_data="explainSQLvsNoSQL"
        )
        item6 = types.InlineKeyboardButton(
            "First Love Story", callback_data="firstlovestory"
        )
        item7 = types.InlineKeyboardButton("Repo Link", callback_data="repolink")
        item8 = types.InlineKeyboardButton("Hobby Message", callback_data="hobbypost")
        item9 = types.InlineKeyboardButton("Cancel", callback_data="cancel")
        markup.add(item1, item2, item3, item4, item5, item6, item7, item8, item9)

        bot.send_message(chat_id, "Что вы хотите загрузить?", reply_markup=markup)
    else:
        bot.reply_to(message, "Эта команда доступна только админу")


@bot.message_handler(
    func=lambda message: not message.text.startswith("/"), content_types=["text"]
)
def handle_text_messages(message):
    if str(message.from_user.id) == ADMIN_ID and message.chat.id in admin_upload:
        if admin_upload[message.chat.id] == "repolink":
            save_data(os.path.join(DATA_DIR, "repolink.txt"), message.text)
            bot.reply_to(message, "Ссылка на репозиторий обновлена")
            upload()
        elif admin_upload[message.chat.id] == "hobbypost":
            save_data(os.path.join(DATA_DIR, "hobbypost.txt"), message.text)
            bot.reply_to(message, "Сообщение о хобби обновлено")
            upload()
        else:
            handle_docs_photo(message)
    else:
        if message.chat.id in awaiting_next_step_input:
            next_step_input(message)
        else:
            text = message.text.lower()
            if text == "селфи":
                send_selfie(message)
            elif text == "старое фото":
                send_old_photo(message)
            elif text == "новое фото":
                send_new_photo(message)
            elif text == "хобби":
                send_hobby_post(message)
            elif text == "гитхаб":
                send_repo_link(message)
            else:
                bot.send_message(
                    message.chat.id,
                    f"Сори, для такого ввода доступны только: "
                    f"селфи, старое фото, новое фото, хобби, гитхаб",
                )


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data in [
            "selfie",
            "oldphoto",
            "newphoto",
            "explaingpt",
            "explainSQLvsNoSQL",
            "firstlovestory",
        ]:
            admin_upload[call.message.chat.id] = call.data
            save_data("admin_upload.json", admin_upload)
            bot.send_message(call.message.chat.id, "Это должен быть файл")
        elif call.data in ["hobbypost", "repolink"]:
            admin_upload[call.message.chat.id] = call.data
            save_data("admin_upload.json", admin_upload)
            bot.send_message(call.message.chat.id, "Это должен быть текст")
        elif call.data == "cancel":
            bot.send_message(call.message.chat.id, "Загрузка завершена")
        elif call.data == "cancel_next_step":
            if call.message.chat.id in awaiting_next_step_input:
                del awaiting_next_step_input[call.message.chat.id]
                save_data("awaiting_next_step_input.json", awaiting_next_step_input)
                bot.send_message(call.message.chat.id, "Ввод следующего шага отменен")


@bot.message_handler(content_types=["document", "photo", "voice"])
def handle_docs_photo(message):
    if str(message.from_user.id) == ADMIN_ID:
        try:
            if message.voice is not None:
                file_info = bot.get_file(message.voice.file_id)
            elif message.photo is not None:
                file_info = bot.get_file(message.photo[-1].file_id)
            else:
                bot.reply_to(message, "Сори, не могу обработать файл")
                return

            if file_info.file_size > MAX_FILE_SIZE:
                bot.reply_to(message, "Файл слишком большой. макс размер - 50 Мб")
                return

            downloaded_file = bot.download_file(file_info.file_path)

            os.makedirs(DATA_DIR, exist_ok=True)

            with open(
                os.path.join(DATA_DIR, f"{admin_upload[message.chat.id]}.jpg")
                if admin_upload[message.chat.id] in ["selfie", "oldphoto"]
                else os.path.join(DATA_DIR, f"{admin_upload[message.chat.id]}.ogg"),
                "wb",
            ) as new_file:
                new_file.write(downloaded_file)

            bot.reply_to(message, "Я получил и загрузил элемент")
            upload()

        except Exception as e:
            bot.reply_to(message, str(e))
    else:
        bot.reply_to(message, "Ты не можешь слать мне данные")


def send_file(message, path):
    if os.path.exists(path):
        with open(path, "rb") as file:
            if path.endswith(".jpg"):
                bot.send_photo(message.chat.id, file)
            elif path.endswith(".ogg"):
                bot.send_voice(message.chat.id, file)
    else:
        bot.reply_to(message, "Файла не существует")


@bot.message_handler(commands=["selfie"])
def send_selfie(message):
    send_file(message, os.path.join(DATA_DIR, "selfie.jpg"))


@bot.message_handler(commands=["oldphoto"])
def send_old_photo(message):
    send_file(message, os.path.join(DATA_DIR, "oldphoto.jpg"))


@bot.message_handler(commands=["newphoto"])
def send_new_photo(message):
    send_file(message, os.path.join(DATA_DIR, "newphoto.jpg"))


@bot.message_handler(commands=["hobbypost"])
def send_hobby_post(message):
    try:
        with open(os.path.join(DATA_DIR, "hobbypost.txt"), "r") as file:
            hobby_message = file.read()
        bot.send_message(message.chat.id, hobby_message)
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Сообщение о хобби не найдено")


@bot.message_handler(commands=["explaingpt"])
def send_explain_gpt(message):
    send_file(message, os.path.join(DATA_DIR, "explaingpt.ogg"))


@bot.message_handler(commands=["explainSQLvsNoSQL"])
def send_explain_sql_vs_nosql(message):
    send_file(message, os.path.join(DATA_DIR, "explainSQLvsNoSQL.ogg"))


@bot.message_handler(commands=["firstlovestory"])
def send_first_love_story(message):
    send_file(message, os.path.join(DATA_DIR, "firstlovestory.ogg"))


@bot.message_handler(commands=["repolink"])
def send_repo_link(message):
    try:
        with open(os.path.join(DATA_DIR, "repolink.txt"), "r") as file:
            repo_link = file.read()
        bot.send_message(message.chat.id, repo_link)
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Ссылка на репозиторий не найдена")


@bot.message_handler(commands=["nextstep"])
def next_step(message):
    split_message = message.text.split(maxsplit=1)

    if len(split_message) > 1:
        text = split_message[1]

        with open(NEXT_STEPS_FILE, "w") as file:
            file.write(f"{text}\n")

        bot.send_message(ADMIN_ID, f"Вам установили следующий шаг {text}")
        bot.send_message(message.chat.id, f"Ваше следующее задание: {text}")
    else:
        awaiting_next_step_input[message.chat.id] = True
        save_data("data/awaiting_next_step_input.json", awaiting_next_step_input)
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Cancel", callback_data="cancel_next_step")
        markup.add(item1)
        bot.send_message(
            message.chat.id,
            f"Вы не предложили следующий шаг. "
            f"Отмените или добавьте следующий шаг сообщением ниже",
            reply_markup=markup,
        )


@bot.message_handler(
    func=lambda message: message.chat.id in awaiting_next_step_input,
    content_types=["text"],
)
def next_step_input(message):
    del awaiting_next_step_input[message.chat.id]
    save_data("data/awaiting_next_step_input.json", awaiting_next_step_input)

    text = message.text

    with open(NEXT_STEPS_FILE, "w") as file:
        file.write(f"{text}\n")

    bot.send_message(ADMIN_ID, f"Вам установили следующий шаг {text}")
    bot.send_message(message.chat.id, f"Ваш следующий шаг {text}")


bot.polling()
