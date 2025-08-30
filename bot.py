import threading
import requests
from datetime import datetime, timedelta
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import os

# ——— إعداد البوت ———
TOKEN = "8218468639:AAGMcdEuLI8G9J8ttSqxoTxvOpZU_jQVse0"
bot = telebot.TeleBot(TOKEN)

# ——— قائمة 58 ولاية الجزائر مع الإحداثيات ———
wilayas = {
    1: ("أدرار", 27.9, -0.3),
    2: ("الشلف", 36.16, 1.33),
    3: ("الأغواط", 33.8, 2.88),
    4: ("أم البواقي", 35.88, 7.11),
    5: ("باتنة", 35.55, 6.17),
    6: ("بجاية", 36.75, 5.07),
    7: ("بسكرة", 34.85, 5.73),
    8: ("بشار", 31.61, -2.22),
    9: ("البليدة", 36.47, 2.83),
    10: ("البويرة", 36.38, 3.9),
    11: ("تمنراست", 22.79, 5.52),
    12: ("تبسة", 35.4, 8.12),
    13: ("تلمسان", 34.88, -1.32),
    14: ("تيارت", 35.37, 1.32),
    15: ("تيزي وزو", 36.72, 4.05),
    16: ("الجزائر", 36.75, 3.06),
    17: ("الجلفة", 34.68, 3.25),
    18: ("جيجل", 36.82, 5.75),
    19: ("سطيف", 36.19, 5.41),
    20: ("سعيدة", 34.84, 0.15),
    21: ("سكيكدة", 36.88, 6.91),
    22: ("سيدي بلعباس", 35.2, -0.63),
    23: ("عنابة", 36.9, 7.77),
    24: ("قالمة", 36.47, 7.43),
    25: ("قسنطينة", 36.36, 6.61),
    26: ("المدية", 36.27, 2.77),
    27: ("مستغانم", 35.93, 0.09),
    28: ("المسيلة", 35.71, 4.55),
    29: ("معسكر", 35.39, 0.14),
    30: ("ورقلة", 31.97, 5.34),
    31: ("وهران", 35.69, -0.64),
    32: ("البيض", 33.69, 1.01),
    33: ("إليزي", 26.5, 8.47),
    34: ("برج بوعريريج", 36.07, 4.77),
    35: ("بومرداس", 36.77, 3.48),
    36: ("الطارف", 36.77, 8.33),
    37: ("تندوف", 27.67, -8.13),
    38: ("تيسمسيلت", 35.6, 1.81),
    39: ("الوادي", 33.37, 6.87),
    40: ("خنشلة", 35.43, 7.15),
    41: ("سوق أهراس", 36.28, 7.95),
    42: ("تيبازة", 36.59, 2.45),
    43: ("ميلة", 36.45, 6.26),
    44: ("عين الدفلى", 36.26, 1.97),
    45: ("النعامة", 33.27, -0.31),
    46: ("عين تموشنت", 35.3, -1.14),
    47: ("غرداية", 32.29, 3.67),
    48: ("غليزان", 35.74, 0.55),
    49: ("تيميمون", 29.26, 0.23),
    50: ("برج باجي مختار", 21.33, 0.95),
    51: ("أولاد جلال", 34.43, 5.73),
    52: ("بني عباس", 30.13, -2.18),
    53: ("عين صالح", 27.2, 2.47),
    54: ("عين قزام", 19.57, 5.77),
    55: ("تقرت", 33.11, 6.07),
    56: ("جانت", 24.55, 9.48),
    57: ("المغير", 33.95, 5.93),
    58: ("المنيعة", 30.58, 2.87),
}

# ——— رسالة ترحيب مع صورة + أزرار ———
@bot.message_handler(commands=['start'])
def start(message):
    photo_url = "https://i.ibb.co/bMtf1dtn/1756542339800.jpg"  
    caption = (
        "🎒📚 *مرحبا بكم في بوت الطقس والوقت للجزائر* 🌤🕒\n\n"
        "📍 اختر ولايتك من الأزرار بالأسفل للحصول على حالة الطقس والوقت الحالي.\n\n"
        "🤖 هذا البوت مصنوع من طرف *Yacine DZ* للاستعمال الشخصي ✅"
    )
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(f"{num} - {wilayas[num][0]}") for num in wilayas]
    buttons.append(KeyboardButton("ℹ️ عن البوت"))
    markup.add(*buttons)
    bot.send_photo(message.chat.id, photo=photo_url, caption=caption, parse_mode="Markdown", reply_markup=markup)

# ——— استقبال اختيار ولاية من الأزرار ———
@bot.message_handler(func=lambda msg: any(msg.text.startswith(str(num)) for num in wilayas))
def weather_by_button(message):
    try:
        num = int(message.text.split(" - ")[0])
        if num in wilayas:
            name, lat, lon = wilayas[num]
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            resp = requests.get(url, timeout=10).json()
            cw = resp.get("current_weather", {})
            temp = cw.get("temperature")
            wind = cw.get("windspeed")
            local_time = (datetime.utcnow() + timedelta(hours=1)).strftime("%H:%M:%S")
            bot.send_message(
                message.chat.id,
                f"🌍 *{name}*\n\n"
                f"🕒 الوقت الآن: {local_time}\n"
                f"🌡 الحرارة: {temp}°C\n"
                f"💨 سرعة الرياح: {wind} م/ث",
                parse_mode="Markdown"
            )
    except:
        bot.send_message(message.chat.id, "⚠ لم أستطع جلب الطقس الآن.")

# ——— زر "عن البوت" ———
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ عن البوت")
def about(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ *عن البوت*\n\n"
        "✅ هذا البوت مخصص لعرض حالة الطقس والوقت الحالي في كل ولايات الجزائر.\n\n"
        "📌 طريقة الاستخدام:\n"
        "1. اضغط على زر ولايتك من القائمة.\n"
        "2. سيظهر لك الطقس + الوقت المحلي.\n"
        "3. يمكن العودة للوحة الأزرار في أي وقت عبر أمر /start.\n\n"
        "👨‍💻 *بوت من طرف Yacine DZ للاستعمال الشخصي* ✅",
        parse_mode="Markdown"
    )

# ——— Flask Server ———
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # <-- تعديل هنا
    app.run(host="0.0.0.0", port=port)

def run_bot():
    bot.infinity_polling()

# ——— تشغيل البوت + Flask ———
if __name__ == "__main__":
    try:
        threading.Thread(target=run_flask).start()
        print("🤖 البوت يعمل الآن...")
        run_bot()
    except Exception as e:
        print("❌ خطأ أثناء تشغيل البوت:", e)