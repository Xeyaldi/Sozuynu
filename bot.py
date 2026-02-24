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

# Hər dəfə fərqli söz gəlməsi üçün bazanı yükləyirik
words_db = load_data()
user_current_word = {}

def get_random_prompt():
    prompts = [
        "🧐 Görək bu hərflərdən nə düzəldəcəksən:",
        "🚀 Beyin gimnastikasına hazırsan?",
        "🧩 Hərflər bir-birinə qarışıb, gəl düzəldək:",
        "💎 Bu sözü tapan əsl dühadır:",
        "🔥 Sürətini göstər, bu nə sözdür?"
    ]
    return random.choice(prompts)

def shuffle_word(word):
    word_list = list(word)
    random.shuffle(word_list)
    return "".join(word_list).upper()

# --- 🚀 START KOMANDASI (Şəxsi Mesajda) ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != "private":
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_play = types.InlineKeyboardButton("🎮 Şəxside Oyna", callback_data="start_private_game")
    btn_chan = types.InlineKeyboardButton("📢 Kanal", url=CHANNEL_URL)
    btn_supp = types.InlineKeyboardButton("🆘 Qrup", url=SUPPORT_URL)
    btn_own = types.InlineKeyboardButton("👨‍💻 Sahib", url=OWNER_URL)
    
    markup.add(btn_play, btn_chan, btn_supp, btn_own)
    
    text = (
        f"👋 **Salam, {message.from_user.first_name}!**\n\n"
        "Mən ən kreativ söz oyunuyam! 🧠\n\n"
        "🕹 Şəxside oynamaq üçün aşağıdakı düyməyə bas, qrupda oynamaq üçün isə adminlər `/oyunabasla` yazmalıdır."
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# --- 🕹 OYUNA BAŞLA (Yalnız Adminlər) ---
@bot.message_handler(commands=['oyunabasla'])
def start_game_group(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ Şəxside oynamaq üçün /start yazıb butona basın.")
        return

    # Admin yoxlaması
    user_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    if user_status not in ['administrator', 'creator'] and message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ Bu oyunu yalnız qrup adminləri başlada bilər!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🟢 Asan", callback_data="level_easy"),
        types.InlineKeyboardButton("🟡 Orta", callback_data="level_medium"),
        types.InlineKeyboardButton("🔴 Çətin", callback_data="level_hard")
    )
    bot.send_message(message.chat.id, "🎮 **Oyunu yalnız adminlər başlada və bitirə bilər.**\n\n🎯 Səviyyəni seçin:", reply_markup=markup, parse_mode="Markdown")

# --- 🛑 OYUNU BİTİR (Yalnız Adminlər) ---
@bot.message_handler(commands=['oyunubitir'])
def stop_game(message):
    if message.chat.id not in user_current_word:
        bot.reply_to(message, "🤔 Onsuz da aktiv bir oyun yoxdur.")
        return

    user_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    if user_status not in ['administrator', 'creator'] and message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ Oyunu yalnız qrup adminləri dayandıra bilər!")
        return

    correct = user_current_word[message.chat.id]
    del user_current_word[message.chat.id]
    bot.send_message(message.chat.id, f"🛑 **Oyun dayandırıldı!**\n\nGizli sözümüz: **{correct.upper()}** idi. Kim daha tez tapardı görəsən? 😏")

# --- ➕ TOPLU SÖZ ƏLAVƏ ETMƏ ---
@bot.message_handler(commands=['elaveasan', 'elaveorta', 'elavecetin'])
def add_words_bulk(message):
    if message.from_user.id != OWNER_ID:
        return
    parts = message.text.split()
    if len(parts) < 2: return
    new_words = parts[1:]
    cmd = parts[0].lower()
    level = "easy" if "asan" in cmd else "medium" if "orta" in cmd else "hard"
    added = 0
    for s in new_words:
        s = s.lower().strip()
        if s not in words_db[level]:
            words_db[level].append(s)
            added += 1
    if added > 0:
        save_data(words_db)
        bot.reply_to(message, f"✅ {added} söz bazaya atıldı.")

# --- 🎮 CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "start_private_game":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🟢 Asan", callback_data="level_easy"),
            types.InlineKeyboardButton("🟡 Orta", callback_data="level_medium"),
            types.InlineKeyboardButton("🔴 Çətin", callback_data="level_hard")
        )
        bot.edit_message_text("Səviyyəni seç, hünərini görək: 😎", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        return

    if call.data.startswith("level_"):
        level = call.data.split("_")[1]
        word = random.choice(words_db[level])
        shuffled = shuffle_word(word)
        user_current_word[call.message.chat.id] = word
        
        bot.edit_message_text(f"{get_random_prompt()}\n\n🧩 **HƏRFLƏR:** `{shuffled}`", 
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id, 
                              parse_mode="Markdown")

# --- 📝 CAVAB YOXLAMA ---
@bot.message_handler(func=lambda m: m.chat.id in user_current_word)
def check_answer(message):
    correct_answer = user_current_word[message.chat.id]
    if message.text.strip().lower() == correct_answer:
        responses = [
            f"🎉 **Halaldır!** Düzgün tapdınız: **{correct_answer.upper()}**",
            f"⚡️ **Müthiş sürət!** Sözümüz **{correct_answer.upper()}** idi.",
            f"🏆 **Qalib gəldin!** Sən əsl söz ustasısan."
        ]
        bot.reply_to(message, random.choice(responses), parse_mode="Markdown")
        del user_current_word[message.chat.id]

bot.infinity_polling()
