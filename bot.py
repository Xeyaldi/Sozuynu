import telebot
import random
import json
import os
from telebot import types

# --- ⚙️ CONFIG (Məlumatları Heroku Config Vars-dan götürür) ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/example")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/example")
OWNER_URL = os.getenv("OWNER_URL", "https://t.me/example")

bot = telebot.TeleBot(TOKEN)

# --- 📂 DATA İDARƏETMƏSİ ---
DATA_FILE = "words_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # İlk dəfə işləyəndə boş baza yaradır
    return {"easy": ["alma", "nar"], "medium": ["kitabxana"], "hard": ["milli-meclis"]}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

words_db = load_data()
user_current_word = {}

# --- 🧩 KÖMƏKÇİ FUNKSİYA ---
def shuffle_word(word):
    word_list = list(word)
    random.shuffle(word_list)
    return "".join(word_list).upper()

# --- 🚀 START KOMANDASI ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Səviyyə butonları (söz sayını göstərir)
    btn1 = types.InlineKeyboardButton(f"🟢 Asan ({len(words_db['easy'])} söz)", callback_data="level_easy")
    btn2 = types.InlineKeyboardButton(f"🟡 Orta ({len(words_db['medium'])} söz)", callback_data="level_medium")
    btn3 = types.InlineKeyboardButton(f"🔴 Çətin ({len(words_db['hard'])} söz)", callback_data="level_hard")
    
    # Alt link butonları
    row_btns = [
        types.InlineKeyboardButton("📢 Kanal", url=CHANNEL_URL),
        types.InlineKeyboardButton("🆘 Qrup", url=SUPPORT_URL)
    ]
    btn_own = types.InlineKeyboardButton("👨‍💻 Sahib", url=OWNER_URL)
    
    markup.add(btn1, btn2, btn3)
    markup.row(*row_btns)
    markup.add(btn_own)
    
    bot.send_message(message.chat.id, 
                     f"👋 **Xoş gəldin, {message.from_user.first_name}!**\n\n"
                     "Qarışıq hərflərdən düzgün sözü düzəldə bilərsən?\n"
                     "Səviyyəni seç və başla!", 
                     reply_markup=markup, parse_mode="Markdown")

# --- ➕ GİZLİ SÖZ ƏLAVƏ ETMƏ (Görünməyən komandalar) ---
@bot.message_handler(commands=['elaveasan', 'elaveorta', 'elavecetin'])
def add_custom_word(message):
    if message.from_user.id != OWNER_ID:
        return # Başqası yazsa cavab verməyəcək (gizli qalacaq)

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        return

    new_word = command_parts[1].lower().strip()
    cmd = command_parts[0].lower()
    
    level = "easy" if "asan" in cmd else "medium" if "orta" in cmd else "hard"

    if new_word not in words_db[level]:
        words_db[level].append(new_word)
        save_data(words_db)
        bot.reply_to(message, f"✅ '{new_word}' əlavə edildi.")

# --- 🎮 OYUN MEXANİKASI ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("level_"))
def handle_levels(call):
    level = call.data.split("_")[1]
    
    if not words_db[level]:
        bot.answer_callback_query(call.id, "Bu səviyyə hələ boşdur!", show_alert=True)
        return

    word = random.choice(words_db[level])
    shuffled = shuffle_word(word)
    user_current_word[call.message.chat.id] = word
    
    bot.edit_message_text(chat_id=call.message.chat.id, 
                          message_id=call.message.message_id,
                          text=f"🧩 Səviyyə: **{level.upper()}**\n\n**Hərflər:** `{shuffled}`\n\nDüzgün sözü yazın:",
                          parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.chat.id in user_current_word)
def check_answer(message):
    correct_answer = user_current_word[message.chat.id]
    if message.text.strip().lower() == correct_answer:
        bot.reply_to(message, "🎉 Doğrudur! Yeni oyun üçün /start yazın.")
        del user_current_word[message.chat.id]
    else:
        bot.reply_to(message, "❌ Yanlışdır, yenidən yoxla.")

bot.infinity_polling()
