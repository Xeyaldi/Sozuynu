import telebot
import random
import json
import os
from telebot import types

# --- ⚙️ CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
CHANNEL_URL = os.getenv("CHANNEL_URL")
SUPPORT_URL = os.getenv("SUPPORT_URL")
OWNER_URL = os.getenv("OWNER_URL")

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "words_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"easy": ["alma"], "medium": ["kitabxana"], "hard": ["azerbaycan"]}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

words_db = load_data()
user_current_word = {}

def shuffle_word(word):
    word_list = list(word)
    random.shuffle(word_list)
    return "".join(word_list).upper()

# --- 🚀 START KOMANDASI ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Səviyyə butonları (əvvəlki kimi qalır)
    btn1 = types.InlineKeyboardButton(f"🟢 Asan ({len(words_db['easy'])} söz)", callback_data="level_easy")
    btn2 = types.InlineKeyboardButton(f"🟡 Orta ({len(words_db['medium'])} söz)", callback_data="level_medium")
    btn3 = types.InlineKeyboardButton(f"🔴 Çətin ({len(words_db['hard'])} söz)", callback_data="level_hard")
    
    row_btns = [
        types.InlineKeyboardButton("📢 Kanal", url=CHANNEL_URL),
        types.InlineKeyboardButton("🆘 Qrup", url=SUPPORT_URL)
    ]
    btn_own = types.InlineKeyboardButton("👨‍💻 Sahib", url=OWNER_URL)
    
    markup.add(btn1, btn2, btn3)
    markup.row(*row_btns)
    markup.add(btn_own)
    
    info_text = (
        f"👋 **Xoş gəldin, {message.from_user.first_name}!**\n\n"
        "🎮 **Oyun haqqında:** Mən sizə hərfləri qarışıq sözlər verirəm, siz isə onları tapmalısınız.\n"
        "👥 **Qrupda oynamaq üçün:** Qrupda `/oyunabasla` komandasını yazın.\n\n"
        "Zəhmət olmasa səviyyəni seçin:"
    )
    bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode="Markdown")

# --- 🕹 Qrup üçün xüsusi komanda ---
@bot.message_handler(commands=['oyunabasla'])
def start_game_group(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ Bu komanda yalnız qruplarda oyuna başlamaq üçündür!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🟢 Asan Səviyyə", callback_data="level_easy"),
        types.InlineKeyboardButton("🟡 Orta Səviyyə", callback_data="level_medium"),
        types.InlineKeyboardButton("🔴 Çətin Səviyyə", callback_data="level_hard")
    )
    bot.send_message(message.chat.id, "🎯 **Zəhmət olmasa səviyyəni seçin:**", reply_markup=markup, parse_mode="Markdown")

# --- ➕ TOPLU SÖZ ƏLAVƏ ETMƏ (Sənin istədiyin kimi yan-yana) ---
@bot.message_handler(commands=['elaveasan', 'elaveorta', 'elavecetin'])
def add_words_bulk(message):
    if message.from_user.id != OWNER_ID:
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "⚠️ Nümunə: `/elaveasan alma nar armud`")
        return

    # Komandadan sonrakı bütün hissələri (sözləri) götürür
    new_words_list = command_parts[1:]
    cmd = command_parts[0].lower()
    
    level = "easy" if "asan" in cmd else "medium" if "orta" in cmd else "hard"

    added = 0
    for s in new_words_list:
        s = s.lower().strip()
        if s not in words_db[level]:
            words_db[level].append(s)
            added += 1
    
    if added > 0:
        save_data(words_db)
        bot.reply_to(message, f"✅ {added} yeni söz **{level}** siyahısına əlavə olundu.")

# --- 🎮 OYUN MEXANİKASI (CALLBACK) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("level_"))
def handle_levels(call):
    level = call.data.split("_")[1]
    
    if not words_db[level]:
        bot.answer_callback_query(call.id, "Bu səviyyədə hələ söz yoxdur!", show_alert=True)
        return

    word = random.choice(words_db[level])
    shuffled = shuffle_word(word)
    user_current_word[call.message.chat.id] = word
    
    bot.edit_message_text(chat_id=call.message.chat.id, 
                          message_id=call.message.message_id,
                          text=f"🧩 **Sözü tapın:** `{shuffled}`\n\nCavabı aşağıdan yazın 👇",
                          parse_mode="Markdown")

# --- 📝 CAVAB YOXLAMA ---
@bot.message_handler(func=lambda m: m.chat.id in user_current_word)
def check_answer(message):
    correct_answer = user_current_word[message.chat.id]
    if message.text.strip().lower() == correct_answer:
        bot.reply_to(message, f"🎉 **DOĞRU!**\n\nQalib: {message.from_user.first_name}\nSöz: **{correct_answer.upper()}**\n\nYeni oyun üçün: /oyunabasla")
        del user_current_word[message.chat.id]

bot.infinity_polling()
