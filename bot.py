# ============================================================
#  ✿ ⌘ ⌬ ✪  بوت فحص الإيميلات – YACINE DEV  ✪ ⌘ ⌬ ✿
#  [يقوم بفحص الإيميلات في فيسبوك وإرسال النتائج]
# ============================================================

import telebot
import requests
import random
import threading
import time
import re
from datetime import datetime

# ================== إعدادات البوت ==================
BOT_TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"  # ← ضع توكن البوت هنا
bot = telebot.TeleBot(BOT_TOKEN)

# ================== المتغيرات العامة ==================
hit = 0
bad_fb = 0
bad_email = 0
is_running = False
threads = []
THREAD_COUNT = 5

# ================== دالة فحص الإيميل في فيسبوك ==================
def check_facebook(email):
    global hit, bad_fb, bad_email
    
    try:
        url = 'https://b-graph.facebook.com/recover_accounts'
        
        headers = {
            'Host': 'b-graph.facebook.com',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = f"q={email}&friend_name=&qs=&summary=true&device_id=d15ef240-9126-44ab-9574-049eb0802d8c&src=fb4a_account_recovery&machine_id=&sfdid=a6ca2f76-0995-4db7-9083-667fc42d836d&fdid=d15ef240-9126-44ab-9574-049eb0802d8c&sim_serials=%5B%5D&sms_retriever=false&cds_experiment_group=-1&oe_aa_experiment_group=-1&oe_aa_experiment_group_immediate_exposure=-1&shared_phone_test_group=&allowlist_email_exp_name=&shared_phone_exp_name=&shared_phone_cp_nonce_code=&shared_phone_number=&is_auto_search=false&is_feo2_api_level_enabled=false&is_sso_like_oauth_search=false&encrypted_msisdn=&locale=en_US&client_country_code=IQ&method=GET&fb_api_req_friendly_name=accountRecoverySearch&fb_api_caller_class=AccountSearchHelper&access_token=350685531728%7C62f8ce9f74b12f84c123cc23437a4a32"
        
        resp = requests.post(url, headers=headers, data=data, timeout=15)
        
        if "network_info" in resp.text:
            hit += 1
            return True
        else:
            bad_fb += 1
            return False
            
    except Exception as e:
        bad_email += 1
        return False

# ================== دالة توليد إيميل عشوائي ==================
def generate_email():
    letters = "abcdefghijklmnopqrstuvwxyz0123456789"
    name = "".join(random.choice(letters) for _ in range(random.randint(5, 10)))
    domains = ["yopmail.com", "guerrillamail.com", "mailinator.com", "10minutemail.com"]
    return f"{name}@{random.choice(domains)}"

# ================== دالة العمل ==================
def worker(chat_id, message_id):
    global hit, bad_fb, bad_email
    
    while is_running:
        try:
            email = generate_email()
            result = check_facebook(email)
            
            if result:
                # إرسال الإيميل الصالح إلى المستخدم
                text = f"""
✿ ⌘ ⌬ ✪ *تم العثور على إيميل صالح* ✪ ⌘ ⌬ ✿

📧 *الإيميل:* `{email}`
📅 *التاريخ:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

✅ *الحالة:* موجود في فيسبوك
"""
                bot.send_message(chat_id, text, parse_mode='Markdown')
            
            # تحديث الإحصائيات
            stats = f"""
✦ *الإحصائيات* ✦
✅ صالح: `{hit}`
❌ غير موجود: `{bad_fb}`
⚠️ فاشل: `{bad_email}`
"""
            bot.edit_message_text(stats, chat_id, message_id, parse_mode='Markdown')
            
            time.sleep(random.uniform(0.5, 2))
            
        except Exception as e:
            time.sleep(1)

# ================== أوامر البوت ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    text = """
✿ ⌘ ⌬ ✪ *بوت فحص الإيميلات* ✪ ⌘ ⌬ ✿

🔥 *بوت خارق لفحص الإيميلات في فيسبوك*

📌 *الأوامر:*
/start  ✿ الصفحة الرئيسية
/scan  ⌘ بدء الفحص
/stop  ⌬ إيقاف الفحص
/stats  ✿ الإحصائيات
/help  ⌘ المساعدة

👨‍💻 *المطور:* `YACINE DEV`
"""
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
✿ ⌘ ⌬ ✪ *المساعدة* ✪ ⌘ ⌬ ✿

/scan  ⌘ بدء فحص الإيميلات
/stop  ⌬ إيقاف الفحص
/stats  ✿ عرض الإحصائيات
/help  ⌘ عرض هذه القائمة

💀 *YACINE DEV* ⚡
"""
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['scan'])
def scan_command(message):
    global is_running, threads, hit, bad_fb, bad_email
    
    if is_running:
        bot.reply_to(message, "⚠️ *الفحص قيد التشغيل بالفعل!*", parse_mode='Markdown')
        return
    
    # إعادة تعيين الإحصائيات
    hit = 0
    bad_fb = 0
    bad_email = 0
    
    is_running = True
    chat_id = message.chat.id
    
    # إرسال رسالة الإحصائيات
    stats_msg = bot.reply_to(message, "⏳ *جاري بدء الفحص...*", parse_mode='Markdown')
    
    # بدء الخيوط
    threads = []
    for _ in range(THREAD_COUNT):
        t = threading.Thread(target=worker, args=(chat_id, stats_msg.message_id))
        t.daemon = True
        t.start()
        threads.append(t)
    
    bot.reply_to(message, f"✅ *تم بدء الفحص بـ {THREAD_COUNT} خيط!*", parse_mode='Markdown')

@bot.message_handler(commands=['stop'])
def stop_command(message):
    global is_running, threads
    
    if not is_running:
        bot.reply_to(message, "⚠️ *الفحص متوقف بالفعل!*", parse_mode='Markdown')
        return
    
    is_running = False
    
    # انتظار انتهاء الخيوط
    for t in threads:
        try:
            t.join(timeout=1)
        except:
            pass
    
    threads = []
    bot.reply_to(message, "🛑 *تم إيقاف الفحص!*", parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    global hit, bad_fb, bad_email
    
    text = f"""
✿ ⌘ ⌬ ✪ *الإحصائيات* ✪ ⌘ ⌬ ✿

✅ *إيميلات صالحة:* `{hit}`
❌ *غير موجودة:* `{bad_fb}`
⚠️ *فاشلة:* `{bad_email}`
📊 *الإجمالي:* `{hit + bad_fb + bad_email}`

👨‍💻 *المطور:* `YACINE DEV`
"""
    bot.reply_to(message, text, parse_mode='Markdown')

# ================== التشغيل ==================
if __name__ == "__main__":
    print("=" * 60)
    print("✿ ⌘ ⌬ ✪  بوت فحص الإيميلات  ✪ ⌘ ⌬ ✿")
    print("👨‍💻 المطور: YACINE DEV")
    print("🔥 يعمل الآن...")
    print("=" * 60)
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("👋 تم الإيقاف")
