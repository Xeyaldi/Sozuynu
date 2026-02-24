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

# --- 🆕 MENYU KOMANDALARI ---
bot.set_my_commands([
    types.BotCommand("start", "Əsas menyu"),
    types.BotCommand("oyun", "Şəxsidə oyuna başla"),
    types.BotCommand("durdur", "Şəxsidə oyunu dayandır"),
    types.BotCommand("oyunabasla", "Qrupda oyuna başla (Admin)"),
    types.BotCommand("oyunubitir", "Qrupda oyunu bitir (Admin)")
])

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
    shuffled = "".join(word_list).upper()
    return " ".join(list(shuffled))

# --- 🚀 START KOMANDASI ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Yeni əlavə edilən "Qrupa Əlavə Et" butonu
    bot_info = bot.get_me()
    add_to_group_url = f"https://t.me/{bot_info.username}?startgroup=true"
    
    btn_add = types.InlineKeyboardButton("➕ Məni Qrupa Əlavə Et", url=add_to_group_url)
    btn_info = types.InlineKeyboardButton("ℹ️ Kömək və Qaydalar", callback_data="game_info")
    btn_chan = types.InlineKeyboardButton("📢 Kanal", url=CHANNEL_URL)
    btn_supp = types.InlineKeyboardButton("🆘 Qrup", url=SUPPORT_URL)
    btn_own = types.InlineKeyboardButton("👨‍💻 Sahib", url=OWNER_URL)
    
    # Butonları ardıcıllıqla düzürük
    markup.add(btn_add, btn_info, btn_chan, btn_supp, btn_own)
    
    text = (
        f"👋 **Salam, {message.from_user.first_name}!**\n\n"
        "🕹 Şəxside oynamaq üçün `/oyun` yazın, dayandırmaq üçün `/durdur` yazın.\n\n"
        "👥 Qrupda oynamaq üçün adminlər `/oyunabasla` yazmalıdır."
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# --- 🕹 ŞƏXSİDƏ KOMANDALAR ---
@bot.message_handler(commands=['oyun'])
def start_private(message):
    if message.chat.type == "private":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🟢 Asan", callback_data="level_easy"),
            types.InlineKeyboardButton("🟡 Orta", callback_data="level_medium"),
            types.InlineKeyboardButton("🔴 Çətin", callback_data="level_hard")
        )
        bot.send_message(message.chat.id, "🎯 **Zəhmət olmasa oyunun səviyyəsini seçin:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['durdur'])
def stop_private(message):
    if message.chat.type == "private" and message.chat.id in user_current_word:
        del user_current_word[message.chat.id]
        bot.reply_to(message, "🛑 Oyun dayandırıldı.")

# --- 🕹 QRUPDA OYUNA BAŞLA ---
@bot.message_handler(commands=['oyunabasla'])
def start_game_group(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ Şəxside oynamaq üçün /oyun yazın.")
        return

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
    
    bot.reply_to(message, f"👤 **{message.from_user.first_name}** tərəfindən oyun başladıldı.\n\n🎮 **Zəhmət olmasa oyunun səviyyəsini seçin:**", reply_markup=markup, parse_mode="Markdown")

# --- 🛑 OYUNU BİTİR ---
@bot.message_handler(commands=['oyunubitir'])
def stop_game(message):
    if message.chat.id not in user_current_word:
        bot.reply_to(message, "🤔 Aktiv oyun yoxdur.")
        return

    user_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    if user_status not in ['administrator', 'creator'] and message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ Bu komanda adminlər üçündür!")
        return

    correct = user_current_word[message.chat.id]["word"]
    del user_current_word[message.chat.id]
    bot.send_message(message.chat.id, f"🛑 **Oyun dayandırıldı!**\n\nGizli söz: **{correct.upper()}** idi.")

# --- ➕ SÖZ ƏLAVƏ ETMƏ ---
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
    if call.data == "game_info":
        info_msg = (
            "📖 **OYUN QAYDALARI**\n\n"
            "• Botun qarışıq verdiyi hərfləri birləşdirib sözü tapın.\n"
            "• Şəxsidə: `/oyun` və `/durdur` komandaları.\n"
            "• Qrupda: `/oyunabasla` və `/oyunubitir` komandaları.\n"
            "• Sözü tapan kimi yeni söz gəlir!"
        )
        bot.send_message(call.message.chat.id, info_msg, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if call.data.startswith("level_"):
        level = call.data.split("_")[1]
        word = random.choice(words_db[level])
        shuffled = shuffle_word(word)
        user_current_word[call.message.chat.id] = {"word": word.lower(), "level": level}
        
        bot.edit_message_text(f"{get_random_prompt()}\n\n🧩 **HƏRFLƏR:** `{shuffled}`", 
                              chat_id=call.message.chat.id, 
                              message_id=call.message.message_id, 
                              parse_mode="Markdown")

# --- 📝 CAVAB YOXLAMA VƏ TƏK MESAJDA DAVAM ---
@bot.message_handler(func=lambda m: m.chat.id in user_current_word)
def check_answer(message):
    game_data = user_current_word[message.chat.id]
    correct_answer = game_data["word"]
    level = game_data["level"]

    if message.text.strip().lower() == correct_answer:
        new_word = random.choice(words_db[level])
        user_current_word[message.chat.id] = {"word": new_word.lower(), "level": level}
        shuffled = shuffle_word(new_word)
        
        response_text = (
            f"🎉 **Halaldır!** Düzgün tapdınız: **{correct_answer.upper()}**\n\n"
            f"______________________________\n\n"
            f"{get_random_prompt()}\n\n"
            f"🧩 **HƏRFLƏR:** `{shuffled}`"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown")

bot.infinity_polling()
