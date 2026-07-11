import telebot
import requests
from datetime import datetime
from io import BytesIO
import logging
import os

# ================= التوكن =================
BOT_TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"
bot = telebot.TeleBot(BOT_TOKEN)

# ========= روابط الـ API =========
INFO_API = "https://nirob-x-info.vercel.app/info?uid={uid}"
OUTFIT_API = "https://nirob-free-fire-outfit.vercel.app/get?uid={uid}"
WELCOME_IMAGE = "https://freeimage.host/i/C07A0Cu"

# ========= إعدادات التسجيل =========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ========= دالة تحويل الوقت =========
def convert_time(timestamp):
    try:
        if not timestamp:
            return "<blockquote>✿ غير موجود</blockquote>"
        ts = int(str(timestamp).strip())
        if ts > 1000000000000:
            ts = ts / 1000
        return datetime.fromtimestamp(ts).strftime("<blockquote>%Y-%m-%d %H:%M:%S</blockquote>")
    except:
        return "<blockquote>✿ غير موجود</blockquote>"

# ========= تنسيق معلومات اللاعب =========
def format_player_info(data, uid):
    basic = data.get("basicInfo", {})
    profile = data.get("profileInfo", {})
    clan = data.get("clanBasicInfo", {})
    captain = data.get("captainBasicInfo", {})
    pet = data.get("petInfo", {})
    social = data.get("socialInfo", {})
    credit = data.get("creditScoreInfo", {})
    diamond = data.get("diamondCostRes", {})

    skills = profile.get("equipedSkills", [])
    weapons = basic.get("weaponSkinShows", [])
    clothes = profile.get("clothes", [])

    rank_names = {0:'⌘ برونز ⌘',1:'⌘ فضي ⌘',2:'⌘ ذهبي ⌘',3:'⌘ بلاتيني ⌘',4:'⌘ ماسي ⌘',5:'⌘ أسطوري ⌘',6:'⌘ سيد ⌘',301:'⌘ محترف ⌘'}
    br_rank = rank_names.get(basic.get("rank"), basic.get("rank", "✿ غير معروف"))
    cs_rank = rank_names.get(basic.get("csRank"), basic.get("csRank", "✿ غير معروف"))

    account_age = "✿ غير معروف"
    if basic.get("createAt"):
        created = datetime.fromtimestamp(int(basic.get("createAt")))
        days = (datetime.now() - created).days
        if days < 30:
            account_age = f"✿ {days} يوم"
        elif days < 365:
            account_age = f"✿ {days//30} شهر"
        else:
            account_age = f"✿ {days//365} سنة"

    text = f"""
<blockquote>╭━━━〔 ✿ ياسين TX ✿ 〕━━━╮</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ بوت معلومات فري فاير</blockquote>
<blockquote>┃  </blockquote>
<blockquote>┃  ✪ *معلومات اللاعب*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✿ *الاسم:* `{basic.get('nickname', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *المعرف (UID):* `{uid}`</blockquote>
<blockquote>┃  ⌬ *المنطقة:* `{basic.get('region', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✪ *نوع الحساب:* `{'⌘ عادي ⌘' if basic.get('accountType') == 1 else '⌘ زائر ⌘'}`</blockquote>
<blockquote>┃  ✿ *المستوى:* `{basic.get('level', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *الخبرة:* `{basic.get('exp', 0):,}`</blockquote>
<blockquote>┃  ⌬ *الإعجابات:* `{basic.get('liked', 0):,}`</blockquote>
<blockquote>┃  ✪ *عمر الحساب:* `{account_age}`</blockquote>
<blockquote>┃  ✿ *الإصدار:* `{basic.get('releaseVersion', 'OB')}`</blockquote>
<blockquote>┃  ⌘ *تاريخ الإنشاء:* `{convert_time(basic.get('createAt'))}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *الرتب*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *رتبة باتل رويال:* `{basic.get('rank', '✿ غير معروف')} ({br_rank})`</blockquote>
<blockquote>┃  ✿ *نقاط باتل رويال:* `{basic.get('rankingPoints', 0):,}`</blockquote>
<blockquote>┃  ⌘ *أعلى رتبة باتل رويال:* `{basic.get('maxRank', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌬ *رتبة كلايش سكوا:* `{basic.get('csRank', '✿ غير معروف')} ({cs_rank})`</blockquote>
<blockquote>┃  ✪ *نقاط كلايش سكوا:* `{basic.get('csRankingPoints', 0):,}`</blockquote>
<blockquote>┃  ✿ *أعلى رتبة كلايش سكوا:* `{basic.get('csMaxRank', '✿ غير معروف')}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌘ *الملف الشخصي*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *صورة الملف:* `{basic.get('headPic', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✪ *الشارة:* `{basic.get('badgeId', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✿ *اللقب:* `{basic.get('title', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *الدبوس:* `{basic.get('pinId', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌬ *الموسم:* `{basic.get('seasonId', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✪ *نجمة مميزة:* `{'⌘ نعم ⌘' if profile.get('isMarkedStar') else '⌘ لا ⌘'}`</blockquote>
<blockquote>┃  ✿ *سلاح PVE:* `{profile.get('pvePrimaryWeapon', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *تاريخ الانتهاء:* `{convert_time(profile.get('endTime'))}`</blockquote>
<blockquote>┃  ⌬ *المهارات:* `{', '.join(map(str, skills)) if skills else '✿ لا يوجد'}`</blockquote>
<blockquote>┃  ✪ *الأسلحة:* `{', '.join(map(str, weapons)) if weapons else '✿ لا يوجد'}`</blockquote>
<blockquote>┃  ✿ *الملابس:* `{', '.join(map(str, clothes)) if clothes else '✿ لا يوجد'}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *النادي*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *اسم النادي:* `{clan.get('clanName', '✿ لا يوجد نادي')}`</blockquote>
<blockquote>┃  ✿ *معرف النادي:* `{clan.get('clanId', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *مستوى النادي:* `{clan.get('clanLevel', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌬ *الأعضاء:* `{clan.get('memberNum', 0)} / {clan.get('capacity', 0)}`</blockquote>
<blockquote>┃  ✪ *الكابتن:* `{captain.get('nickname', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✿ *مستوى الكابتن:* `{captain.get('level', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *إعجابات الكابتن:* `{captain.get('liked', 0):,}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *الحيوان الأليف*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *معرف الحيوان:* `{pet.get('id', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✿ *المستوى:* `{pet.get('level', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ⌘ *الخبرة:* `{pet.get('exp', 0)}`</blockquote>
<blockquote>┃  ⌬ *الجلد:* `{pet.get('skinId', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✪ *المهارة:* `{pet.get('selectedSkillId', '✿ غير معروف')}`</blockquote>
<blockquote>┃  ✿ *مختار:* `{'⌘ نعم ⌘' if pet.get('isSelected') else '⌘ لا ⌘'}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *تواصل اجتماعي*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *اللغة:* `{social.get('language', 'EN').replace('Language_', '')}`</blockquote>
<blockquote>┃  ✿ *وقت النشاط:* `{social.get('timeActive', 'DAY').replace('TimeActive_', '')}`</blockquote>
<blockquote>┃  ⌘ *التوقيع:* `{social.get('signature', '✿ لا يوجد توقيع')}`</blockquote>
<blockquote>┃  ⌬ *الرتبة الظاهرة:* `{social.get('rankShow', 'BR').replace('RankShow_', '')}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *الحساب*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✿ *درجة الائتمان:* `{credit.get('creditScore', '100')}/100`</blockquote>
<blockquote>┃  ⌘ *تكلفة الماس:* `{diamond.get('diamondCost', '✿ غير معروف')} 💎`</blockquote>
<blockquote>┃  ⌬ *تاريخ الانتهاء:* `{convert_time(credit.get('periodicSummaryEndTime'))}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *الجدول الزمني*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *تاريخ الإنشاء:* `{convert_time(basic.get('createAt'))}`</blockquote>
<blockquote>┃  ✿ *آخر تسجيل دخول:* `{convert_time(basic.get('lastLoginAt'))}`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌘ *المطور:* `ياسين X6`</blockquote>
<blockquote>┃  ⌬ *البوت:* `@Yacine_X6_Bot`</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✪ *جميع الحقوق محفوظة ©*</blockquote>
<blockquote>╰━━━━━━━━━━━━━━━━━━━━━━━━━╯</blockquote>
"""
    return text

# ================= أمر البدء =================
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        welcome_text = f"""
<blockquote>╭━━━〔 ✿ ياسين TX ✿ 〕━━━╮</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ بوت معلومات فري فاير</blockquote>
<blockquote>┃  </blockquote>
<blockquote>┃  ✪ البوت الأكثر تطوراً للحصول على</blockquote>
<blockquote>┃  معلومات لاعبي فري فاير بكل دقة</blockquote>
<blockquote>┃  وسرعة.</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *الخدمات*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✿ معلومات الحساب.</blockquote>
<blockquote>┃  ⌘ صورة الأوتفيت.</blockquote>
<blockquote>┃  ⌬ رتبة اللاعب.</blockquote>
<blockquote>┃  ✪ إحصائيات متقدمة.</blockquote>
<blockquote>┃  ✿ واجهة احترافية.</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *الأوامر*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /info <المعرف></blockquote>
<blockquote>┃  ✿ معلومات اللاعب.</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /outfit <المعرف></blockquote>
<blockquote>┃  ⌘ صورة الأوتفيت.</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /help</blockquote>
<blockquote>┃  ⌬ جميع الأوامر.</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /start</blockquote>
<blockquote>┃  ✪ الصفحة الرئيسية.</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ✿ *مثال*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /info 9097982134</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  👨‍💻 *المطور:* `ياسين X6`</blockquote>
<blockquote>┃  ⌬ جميع الحقوق محفوظة</blockquote>
<blockquote>╰━━━━━━━━━━━━━━━━━━━━━━━━━╯</blockquote>
"""
        try:
            image_response = requests.get(WELCOME_IMAGE, timeout=15)
            if image_response.status_code == 200:
                photo = BytesIO(image_response.content)
                photo.name = "welcome.png"
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=welcome_text,
                    parse_mode='HTML'
                )
            else:
                bot.reply_to(message, welcome_text, parse_mode='HTML')
        except:
            bot.reply_to(message, welcome_text, parse_mode='HTML')
            
    except Exception as e:
        logging.error(f"✿ خطأ في أمر البدء: {e}")
        bot.reply_to(message, "<blockquote>❌ حدث خطأ، يرجى المحاولة لاحقاً.</blockquote>", parse_mode='HTML')

# ================= أمر المساعدة =================
@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
<blockquote>╭━━━〔 ✿ ياسين TX ✿ 〕━━━╮</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *دليل الأوامر*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌬ *الأوامر المتاحة:*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /info <المعرف> ✿ معلومات اللاعب</blockquote>
<blockquote>┃  /outfit <المعرف> ⌘ صورة الأوتفيت</blockquote>
<blockquote>┃  /start ✪ الصفحة الرئيسية</blockquote>
<blockquote>┃  /help ⌬ عرض هذه القائمة</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ⌘ *مثال:*</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  /info 9097982134</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  ━━━━━━━━━━━━━━━━━━━━</blockquote>
<blockquote>┃</blockquote>
<blockquote>┃  👨‍💻 *المطور:* `ياسين X6`</blockquote>
<blockquote>┃  ⌬ جميع الحقوق محفوظة</blockquote>
<blockquote>╰━━━━━━━━━━━━━━━━━━━━━━━━━╯</blockquote>
"""
    bot.reply_to(message, text, parse_mode='HTML')

# ================= أمر المعلومات =================
@bot.message_handler(commands=['info'])
def info_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<blockquote>❌ استخدم: /info <المعرف>\nمثال: /info 9097982134</blockquote>", parse_mode='HTML')
        return

    uid = parts[1].strip()
    if not uid.isdigit():
        bot.reply_to(message, "<blockquote>❌ معرف غير صحيح! يرجى إدخال أرقام فقط.</blockquote>", parse_mode='HTML')
        return

    processing = bot.reply_to(message, f"<blockquote>⏳ جاري جلب المعلومات للمعرف {uid}...</blockquote>", parse_mode='HTML')

    try:
        url = INFO_API.format(uid=uid)
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            bot.edit_message_text("<blockquote>❌ خطأ في الـ API! يرجى المحاولة لاحقاً.</blockquote>", message.chat.id, processing.message_id, parse_mode='HTML')
            return

        data = response.json()

        if "basicInfo" not in data:
            bot.edit_message_text("<blockquote>❌ اللاعب غير موجود! يرجى التحقق من المعرف.</blockquote>", message.chat.id, processing.message_id, parse_mode='HTML')
            return

        formatted_text = format_player_info(data, uid)

        bot.delete_message(message.chat.id, processing.message_id)
        bot.reply_to(message, formatted_text, parse_mode='HTML')

        outfit_url = OUTFIT_API.format(uid=uid)
        outfit_response = requests.get(outfit_url, timeout=30)

        if outfit_response.status_code == 200:
            photo = BytesIO(outfit_response.content)
            photo.name = "outfit.png"
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"<blockquote>⌬ صورة الأوتفيت\n🎮 {data.get('basicInfo', {}).get('nickname', 'غير معروف')} | 🆔 {uid}</blockquote>",
                parse_mode='HTML',
                reply_to_message_id=message.message_id
            )

    except Exception as e:
        logging.error(f"✿ خطأ في أمر المعلومات: {e}")
        bot.edit_message_text(f"<blockquote>❌ خطأ: {str(e)}</blockquote>", message.chat.id, processing.message_id, parse_mode='HTML')

# ================= أمر الأوتفيت =================
@bot.message_handler(commands=['outfit'])
def outfit_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<blockquote>❌ استخدم: /outfit <المعرف>\nمثال: /outfit 9097982134</blockquote>", parse_mode='HTML')
        return

    uid = parts[1].strip()
    if not uid.isdigit():
        bot.reply_to(message, "<blockquote>❌ معرف غير صحيح! يرجى إدخال أرقام فقط.</blockquote>", parse_mode='HTML')
        return

    processing = bot.reply_to(message, f"<blockquote>⏳ جاري تحضير صورة الأوتفيت للمعرف {uid}...</blockquote>", parse_mode='HTML')

    try:
        outfit_url = OUTFIT_API.format(uid=uid)
        response = requests.get(outfit_url, timeout=30)

        if response.status_code != 200:
            bot.edit_message_text("<blockquote>❌ صورة الأوتفيت غير متوفرة!</blockquote>", message.chat.id, processing.message_id, parse_mode='HTML')
            return

        photo = BytesIO(response.content)
        photo.name = "outfit.png"

        bot.delete_message(message.chat.id, processing.message_id)
        bot.send_photo(
            message.chat.id,
            photo,
            caption=f"<blockquote>⌬ صورة الأوتفيت\n🆔 المعرف: {uid}</blockquote>",
            parse_mode='HTML',
            reply_to_message_id=message.message_id
        )

    except Exception as e:
        logging.error(f"✿ خطأ في أمر الأوتفيت: {e}")
        bot.edit_message_text(f"<blockquote>❌ خطأ: {str(e)}</blockquote>", message.chat.id, processing.message_id, parse_mode='HTML')

# ================= التشغيل الرئيسي =================
if __name__ == "__main__":
    print("=" * 50)
    print("✿ بوت ياسين X6 للمعلومات")
    print("⌘ المطور: ياسين X6")
    print("⌬ جميع الحقوق محفوظة")
    print("✪ يعمل الآن...")
    print("=" * 50)

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"✿ خطأ: {e}")
