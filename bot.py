import telebot
import requests
from datetime import datetime
from io import BytesIO
import logging

# ================= الإعدادات =================
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
            return "غير موجود"
        ts = int(str(timestamp).strip())
        if ts > 1000000000000:
            ts = ts / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "غير موجود"

# ========= دالة تنسيق المعلومات مع اقتباس تيليجرام =========
def format_player_info(data, uid):
    basic = data.get("basicInfo", {})
    profile = data.get("profileInfo", {})
    clan = data.get("clanBasicInfo", {})
    captain = data.get("captainBasicInfo", {})
    pet = data.get("petInfo", {})
    social = data.get("socialInfo", {})
    credit = data.get("creditScoreInfo", {})
    diamond = data.get("diamondCostRes", {})
    external = basic.get("externalIconInfo", {})

    skills = profile.get("equipedSkills", [])
    weapons = basic.get("weaponSkinShows", [])
    clothes = profile.get("clothes", [])

    rank_names = {0:'برونز',1:'فضي',2:'ذهبي',3:'بلاتيني',4:'ماسي',5:'أسطوري',6:'سيد',301:'محترف'}
    br_rank = rank_names.get(basic.get("rank"), basic.get("rank", "غير معروف"))
    cs_rank = rank_names.get(basic.get("csRank"), basic.get("csRank", "غير معروف"))

    account_age = "غير معروف"
    if basic.get("createAt"):
        created = datetime.fromtimestamp(int(basic.get("createAt")))
        days = (datetime.now() - created).days
        if days < 30:
            account_age = f"{days} يوم"
        elif days < 365:
            account_age = f"{days//30} شهر"
        else:
            account_age = f"{days//365} سنة"

    # ===== تصميم مع اقتباس تيليجرام (> في بداية كل سطر) =====
    text = f"""
> *✦ ── 〔🔥 𝒀𝑨𝑪𝑰𝑵𝑬 𝑿𝟔 🔥〕 ── ✦*

> *▸ الاسم:* `{basic.get('nickname', 'غير معروف')}`
> *▸ المعرف (UID):* `{uid}`
> *▸ المنطقة:* `{basic.get('region', 'غير معروف')}`
> *▸ نوع الحساب:* `{'عادي' if basic.get('accountType') == 1 else 'زائر'}`
> *▸ المستوى:* `{basic.get('level', 'غير معروف')}`
> *▸ الخبرة:* `{basic.get('exp', 0):,}`
> *▸ الإعجابات:* `{basic.get('liked', 0):,}`
> *▸ عمر الحساب:* `{account_age}`
> *▸ الإصدار:* `{basic.get('releaseVersion', 'OB')}`
> *▸ تاريخ الإنشاء:* `{convert_time(basic.get('createAt'))}`

> *✦ ── 〔🏆 الرتب〕 ── ✦*

> *▸ رتبة BR:* `{basic.get('rank', 'غير معروف')} ({br_rank})`
> *▸ نقاط BR:* `{basic.get('rankingPoints', 0):,}`
> *▸ أعلى رتبة BR:* `{basic.get('maxRank', 'غير معروف')}`
> *▸ رتبة CS:* `{basic.get('csRank', 'غير معروف')} ({cs_rank})`
> *▸ نقاط CS:* `{basic.get('csRankingPoints', 0):,}`
> *▸ أعلى رتبة CS:* `{basic.get('csMaxRank', 'غير معروف')}`

> *✦ ── 〔🧩 الملف الشخصي〕 ── ✦*

> *▸ معرض الصورة:* `{basic.get('headPic', 'غير معروف')}`
> *▸ الشارة:* `{basic.get('badgeId', 'غير معروف')}`
> *▸ العنوان:* `{basic.get('title', 'غير معروف')}`
> *▸ الدبوس:* `{basic.get('pinId', 'غير معروف')}`
> *▸ الموسم:* `{basic.get('seasonId', 'غير معروف')}`
> *▸ علامة مميزة:* `{'نعم' if profile.get('isMarkedStar') else 'لا'}`
> *▸ سلاح PVE:* `{profile.get('pvePrimaryWeapon', 'غير معروف')}`
> *▸ تاريخ الانتهاء:* `{convert_time(profile.get('endTime'))}`
> *▸ المهارات:* `{', '.join(map(str, skills)) if skills else 'لا يوجد'}`
> *▸ الأسلحة:* `{', '.join(map(str, weapons)) if weapons else 'لا يوجد'}`
> *▸ الملابس:* `{', '.join(map(str, clothes)) if clothes else 'لا يوجد'}`

> *✦ ── 〔🏰 النادي〕 ── ✦*

> *▸ اسم النادي:* `{clan.get('clanName', 'لا يوجد نادي')}`
> *▸ معرف النادي:* `{clan.get('clanId', 'غير معروف')}`
> *▸ مستوى النادي:* `{clan.get('clanLevel', 'غير معروف')}`
> *▸ الأعضاء:* `{clan.get('memberNum', 0)} / {clan.get('capacity', 0)}`
> *▸ الكابتن:* `{captain.get('nickname', 'غير معروف')}`
> *▸ مستوى الكابتن:* `{captain.get('level', 'غير معروف')}`
> *▸ إعجابات الكابتن:* `{captain.get('liked', 0):,}`

> *✦ ── 〔🐾 الحيوان الأليف〕 ── ✦*

> *▸ معرف الحيوان:* `{pet.get('id', 'غير معروف')}`
> *▸ المستوى:* `{pet.get('level', 'غير معروف')}`
> *▸ الخبرة:* `{pet.get('exp', 0)}`
> *▸ الجلد:* `{pet.get('skinId', 'غير معروف')}`
> *▸ المهارة:* `{pet.get('selectedSkillId', 'غير معروف')}`
> *▸ مختار:* `{'نعم' if pet.get('isSelected') else 'لا'}`

> *✦ ── 〔💬 اجتماعي〕 ── ✦*

> *▸ اللغة:* `{social.get('language', 'EN').replace('Language_', '')}`
> *▸ وقت النشاط:* `{social.get('timeActive', 'DAY').replace('TimeActive_', '')}`
> *▸ التوقيع:* `{social.get('signature', 'لا يوجد توقيع')}`
> *▸ الرتبة الظاهرة:* `{social.get('rankShow', 'BR').replace('RankShow_', '')}`

> *✦ ── 〔💰 الحساب〕 ── ✦*

> *▸ درجة الائتمان:* `{credit.get('creditScore', '100')}/100`
> *▸ تكلفة الماس:* `{diamond.get('diamondCost', 'غير معروف')} 💎`
> *▸ تاريخ الانتهاء:* `{convert_time(credit.get('periodicSummaryEndTime'))}`

> *✦ ── 〔📅 الجدول الزمني〕 ── ✦*

> *▸ تاريخ الإنشاء:* `{convert_time(basic.get('createAt'))}`
> *▸ آخر تسجيل دخول:* `{convert_time(basic.get('lastLoginAt'))}`

> *✦ ── 〔🛡️ المطور〕 ── ✦*
> *▸ المطور:* `YACINE_X6`
> *▸ البوت:* `@Yacine_X6_Bot`

> *✦ ── 〔✨ شكراً لاستخدامك البوت ✨〕 ── ✦*
"""
    return text

# ================= أمر البدء =================
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_name = message.from_user.first_name or "صديقي"
        
        welcome_text = f"""
> *✦ ── 〔✨ مرحباً {user_name} ✨〕 ── ✦*

> *🤖 بوت معلومات فري فاير*
> *👨‍💻 المطور: YACINE_X6*

> *✦ ── 〔📌 الأوامر〕 ── ✦*

> *▸ /info <المعرف> - للحصول على معلومات اللاعب*
> *▸ /outfit <المعرف> - للحصول على صورة الأوتفيت*
> *▸ /start - رسالة الترحيب*
> *▸ /help - لعرض المساعدة*

> *✦ ── 〔🎯 مثال〕 ── ✦*
> *`/info 9097982134`*

> *✦ ── 〔💡 استخدم /help للمزيد〕 ── ✦*

> *✦ ── 〔🛡️ YACINE_X6〕 ── ✦*
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
                    parse_mode='Markdown'
                )
            else:
                bot.reply_to(message, welcome_text, parse_mode='Markdown')
        except:
            bot.reply_to(message, welcome_text, parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"خطأ في أمر البدء: {e}")
        bot.reply_to(message, "> ❌ *حدث خطأ، يرجى المحاولة لاحقاً.*", parse_mode='Markdown')

# ================= أمر المساعدة =================
@bot.message_handler(commands=['help'])
def help_command(message):
    text = """
> *✦ ── 〔📖 دليل الأوامر〕 ── ✦*

> *▸ /info <المعرف>* - عرض معلومات اللاعب
> *▸ /outfit <المعرف>* - عرض صورة الأوتفيت
> *▸ /start* - رسالة الترحيب
> *▸ /help* - عرض هذه القائمة

> *✦ ── 〔📊 ماذا تحصل؟〕 ── ✦*

> ✅ المعلومات الأساسية
> ✅ تفاصيل الرتب
> ✅ معلومات النادي
> ✅ تفاصيل الحيوان الأليف
> ✅ المعلومات الاجتماعية
> ✅ الجدول الزمني للحساب
> ✅ معلومات الائتمان والماس
> ✅ صورة الأوتفيت

> *✦ ── 〔🛡️ المطور〕 ── ✦*
> *▸ YACINE_X6*
> *▸ @Yacine_X6_Bot*

> *✦ ── 〔✨ شكراً لاستخدامك البوت ✨〕 ── ✦*
"""
    bot.reply_to(message, text, parse_mode='Markdown')

# ================= أمر المعلومات =================
@bot.message_handler(commands=['info'])
def info_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "> ❌ *استخدم: /info <المعرف>*\n> مثال: `/info 9097982134`", parse_mode='Markdown')
        return

    uid = parts[1].strip()
    if not uid.isdigit():
        bot.reply_to(message, "> ❌ *معرف غير صحيح! يرجى إدخال أرقام فقط.*", parse_mode='Markdown')
        return

    processing = bot.reply_to(message, f"> ⏳ *جاري جلب المعلومات للمعرف {uid}...*", parse_mode='Markdown')

    try:
        url = INFO_API.format(uid=uid)
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            bot.edit_message_text("> ❌ *خطأ في الـ API! يرجى المحاولة لاحقاً.*", message.chat.id, processing.message_id, parse_mode='Markdown')
            return

        data = response.json()

        if "basicInfo" not in data:
            bot.edit_message_text("> ❌ *اللاعب غير موجود! يرجى التحقق من المعرف.*", message.chat.id, processing.message_id, parse_mode='Markdown')
            return

        formatted_text = format_player_info(data, uid)

        bot.delete_message(message.chat.id, processing.message_id)
        bot.reply_to(message, formatted_text, parse_mode='Markdown')

        outfit_url = OUTFIT_API.format(uid=uid)
        outfit_response = requests.get(outfit_url, timeout=30)

        if outfit_response.status_code == 200:
            photo = BytesIO(outfit_response.content)
            photo.name = "outfit.png"
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"> *👕 صورة الأوتفيت*\n> 🎮 {data.get('basicInfo', {}).get('nickname', 'غير معروف')} | 🆔 {uid}",
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

    except Exception as e:
        logging.error(f"خطأ في أمر المعلومات: {e}")
        bot.edit_message_text(f"> ❌ *خطأ: {str(e)}*", message.chat.id, processing.message_id, parse_mode='Markdown')

# ================= أمر الأوتفيت =================
@bot.message_handler(commands=['outfit'])
def outfit_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "> ❌ *استخدم: /outfit <المعرف>*\n> مثال: `/outfit 9097982134`", parse_mode='Markdown')
        return

    uid = parts[1].strip()
    if not uid.isdigit():
        bot.reply_to(message, "> ❌ *معرف غير صحيح! يرجى إدخال أرقام فقط.*", parse_mode='Markdown')
        return

    processing = bot.reply_to(message, f"> ⏳ *جاري تحضير صورة الأوتفيت للمعرف {uid}...*", parse_mode='Markdown')

    try:
        outfit_url = OUTFIT_API.format(uid=uid)
        response = requests.get(outfit_url, timeout=30)

        if response.status_code != 200:
            bot.edit_message_text("> ❌ *صورة الأوتفيت غير متوفرة!*", message.chat.id, processing.message_id, parse_mode='Markdown')
            return

        photo = BytesIO(response.content)
        photo.name = "outfit.png"

        bot.delete_message(message.chat.id, processing.message_id)
        bot.send_photo(
            message.chat.id,
            photo,
            caption=f"> *👕 صورة الأوتفيت*\n> 🆔 المعرف: {uid}",
            parse_mode='Markdown',
            reply_to_message_id=message.message_id
        )

    except Exception as e:
        logging.error(f"خطأ في أمر الأوتفيت: {e}")
        bot.edit_message_text(f"> ❌ *خطأ: {str(e)}*", message.chat.id, processing.message_id, parse_mode='Markdown')

# ================= التشغيل الرئيسي =================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 بوت YACINE_X6 للمعلومات")
    print("👨‍💻 المطور: YACINE_X6")
    print("=" * 50)
    print("✅ INFO API: https://nirob-x-info.vercel.app/info")
    print("✅ OUTFIT API: https://nirob-free-fire-outfit.vercel.app/get")
    print("🤖 البوت يعمل الآن...")
    print("=" * 50)

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ خطأ: {e}")
