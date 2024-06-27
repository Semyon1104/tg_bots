import telebot
import random
import os
import sqlite3
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

bot = telebot.TeleBot('7484269079:AAHYtTK1-7bVoBe6-J3Ez6JHj89Z2iNm3fk')

# Функция для загрузки слов из файлов
def load_words():
    words_dict = {}
    for letter in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя":
        file_path = f'words/{letter}.txt'
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                words_dict[letter] = [line.strip().lower() for line in file]
        else:
            words_dict[letter] = []
    return words_dict

words_dict = load_words()

# Хранение последней буквы
last_letter = None

# Функция для создания клавиатуры с командами
def create_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = KeyboardButton('/start')
    btn_help = KeyboardButton('/help')
    btn_reset = KeyboardButton('/reset')
    markup.add(btn_start, btn_help, btn_reset)
    return markup

def load_phrases_letter(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        phrases = [line.strip() for line in file]
    return phrases

# Загружаем фразы
phrases_letter = load_phrases_letter('phrases/error_in_letter.txt')

def load_phrases_repeat(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        phrases = [line.strip() for line in file]
    return phrases

# Загружаем фразы
phrases_repeat = load_phrases_repeat('phrases/repeat_word.txt')

def get_last_valid_letter(word):
    for char in reversed(word):
        if char not in 'ьы':
            return char
    return word[-1]

# Функция для создания таблицы в базе данных SQLite
def create_table():
    conn = sqlite3.connect('game_words0.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS used_words (
            id INTEGER PRIMARY KEY,
            word TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Вызов функции создания таблицы при запуске скрипта
create_table()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global last_letter
    last_letter = None
    conn = sqlite3.connect('game_words0.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM used_words')  # Очистим таблицу использованных слов при начале новой игры
    conn.commit()
    conn.close()
    markup = create_markup()
    bot.reply_to(message, "Привет! Давай сыграем в игру в слова. Напиши любое слово!\n Если забыл букву - нажми нажми /help", reply_markup=markup)

@bot.message_handler(commands=['reset'])
def reset_game(message):
    global last_letter
    last_letter = None
    conn = sqlite3.connect('game_words0.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM used_words')  # Очистим таблицу использованных слов при начале новой игры
    conn.commit()
    conn.close()
    bot.reply_to(message, "Игра завершена, пошел нахуй. Для начала новой игры введите /start.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (last_letter)
    if last_letter is None:
        help_text = ("Начни сначала игру, мудачье")

    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
def play_word_game(message):
    global last_letter
    user_word = message.text.lower().strip()
    if ' ' in user_word:
        bot.reply_to(message, "Словами не бросайся, одно надо")
        return
    # Проверка на недопустимые символы и пустую строку
    if not user_word or not re.match('^[а-яё]+$', user_word):
        bot.reply_to(message, "По-русски ээ бля пиши, шандон.")
        return


    # Проверка на повторение слов пользователя
    conn = sqlite3.connect('game_words0.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM used_words WHERE word = ?', (user_word,))
    if cursor.fetchone():
        phrase = random.choice(phrases_repeat)
        bot.reply_to(message, phrase)
        conn.close()
        return

    if last_letter:
        expected_letter = get_last_valid_letter(user_word)
        if user_word[0] != last_letter:
            phrase = random.choice(phrases_letter).replace('{letter}', last_letter.upper())
            bot.reply_to(message, phrase)
            conn.close()
            return
    else:
        expected_letter = get_last_valid_letter(user_word)

    last_letter = expected_letter

    # Добавление использованного слова в базу данных
    cursor.execute('INSERT OR IGNORE INTO used_words (word) VALUES (?)', (user_word,))
    conn.commit()
    conn.close()

    # Найти слова, начинающиеся с последней буквы
    conn = sqlite3.connect('game_words0.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT word FROM used_words')
    used_words = {row[0] for row in cursor.fetchall()}
    suitable_words = [word for word in words_dict.get(last_letter, []) if word not in used_words]
    conn.close()

    if suitable_words:
        bot_word = random.choice(suitable_words)
        bot.reply_to(message, bot_word)
        last_letter = get_last_valid_letter(bot_word)

        # Добавление использованного слова бота в базу данных
        conn = sqlite3.connect('game_words0.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO used_words (word) VALUES (?)', (bot_word,))
        conn.commit()
        conn.close()
    else:
        bot.reply_to(message, "Не могу найти слово на эту букву. Ты выиграл! Начнем заново? Напиши любое слово.")
        last_letter = None

bot.polling()
