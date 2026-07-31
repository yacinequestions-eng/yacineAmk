#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام - إيميلات مؤقتة + ستايلات نصوص
ملف واحد - يدعم Bot API 9.4 (أزرار ملونة)
"""

import re
import html
from typing import Dict, Optional, List
from collections import defaultdict

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==================== التكوين ====================
BOT_TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"

# ==================== البيانات المؤقتة ====================
user_data: Dict[int, Dict] = defaultdict(lambda: {
    "sid_token": None,
    "email": None,
    "emails": [],
    "email_user": None
})

user_stretch_level: Dict[int, int] = defaultdict(lambda: 1)
user_waiting_for_username: Dict[int, bool] = defaultdict(lambda: False)

# ==================== دوال Guerrilla Mail API ====================
GUERRILLA_API_BASE = "https://api.guerrillamail.com/ajax.php"

async def guerrilla_request(params: Dict) -> Dict:
    params["ip"] = "127.0.0.1"
    params["agent"] = "Mozilla_telegram_bot"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GUERRILLA_API_BASE,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

async def create_email(sid_token: Optional[str] = None) -> Dict:
    params = {"f": "get_email_address"}
    if sid_token:
        params["sid_token"] = sid_token
    return await guerrilla_request(params)

async def set_email_user(sid_token: str, email_user: str) -> Dict:
    params = {
        "f": "set_email_user",
        "sid_token": sid_token,
        "email_user": email_user
    }
    return await guerrilla_request(params)

async def get_email_list(sid_token: str, offset: int = 0) -> Dict:
    params = {
        "f": "get_email_list",
        "sid_token": sid_token,
        "offset": offset
    }
    return await guerrilla_request(params)

async def fetch_email(sid_token: str, email_id: int) -> Dict:
    params = {
        "f": "fetch_email",
        "sid_token": sid_token,
        "email_id": email_id
    }
    return await guerrilla_request(params)

# ==================== دوال ستايل النصوص ====================
def apply_bold(text: str) -> str:
    bold_map = {
        'ا': '𝗔', 'ب': '𝗕', 'ت': '𝗧', 'ث': '𝗧𝗛', 'ج': '𝗝',
        'ح': '𝗛', 'خ': '𝗞𝗛', 'د': '𝗗', 'ذ': '𝗭', 'ر': '𝗥',
        'ز': '𝗭', 'س': '𝗦', 'ش': '𝗦𝗛', 'ص': '𝗦', 'ض': '𝗗',
        'ط': '𝗧', 'ظ': '𝗭', 'ع': '𝗔', 'غ': '𝗚', 'ف': '𝗙',
        'ق': '𝗤', 'ك': '𝗞', 'ل': '𝗟', 'م': '𝗠', 'ن': '𝗡',
        'ه': '𝗛', 'و': '𝗪', 'ي': '𝗬',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
    return ''.join(bold_map.get(char, char) for char in text)

def apply_italic(text: str) -> str:
    italic_map = {
        'ا': '𝘢', 'ب': '𝘣', 'ت': '𝘵', 'ث': '𝘵𝘩', 'ج': '𝘫',
        'ح': '𝘩', 'خ': '𝘬𝘩', 'د': '𝘥', 'ذ': '𝘻', 'ر': '𝘳',
        'ز': '𝘻', 'س': '𝘴', 'ش': '𝘴𝘩', 'ص': '𝘴', 'ض': '𝘥',
        'ط': '𝘵', 'ظ': '𝘻', 'ع': '𝘢', 'غ': '𝘨', 'ف': '𝘧',
        'ق': '𝘲', 'ك': '𝘬', 'ل': '𝘭', 'م': '𝘮', 'ن': '𝘯',
        'ه': '𝘩', 'و': '𝘸', 'ي': '𝘺'
    }
    return ''.join(italic_map.get(char, char) for char in text)

def apply_stretch(text: str, level: int = 1) -> str:
    multiplier = {1: 2, 2: 3, 3: 4}.get(level, 2)
    return ''.join(char * multiplier for char in text)

def apply_quote(text: str) -> str:
    lines = text.split('\n')
    return '\n'.join(f'❝ {line} ❞' for line in lines)

def apply_fancy_arabic(text: str) -> str:
    fancy_map = {
        'ا': 'ﯦ', 'ب': 'ﯨ', 'ت': 'ﯩ', 'ث': 'ﯪ', 'ج': 'ﯫ',
        'ح': 'ﯬ', 'خ': 'ﯭ', 'د': 'ﯮ', 'ذ': 'ﯯ', 'ر': 'ﯰ',
        'ز': 'ﯱ', 'س': 'ﯲ', 'ش': 'ﯳ', 'ص': 'ﯴ', 'ض': 'ﯵ',
        'ط': 'ﯶ', 'ظ': 'ﯷ', 'ع': 'ﯸ', 'غ': 'ﯹ', 'ف': 'ﯺ',
        'ق': 'ﯻ', 'ك': 'ﯼ', 'ل': 'ﯽ', 'م': 'ﯾ', 'ن': 'ﯿ',
        'ه': 'ﰀ', 'و': 'ﰁ', 'ي': 'ﰂ'
    }
    return ''.join(fancy_map.get(char, char) for char in text)

# ==================== دوال المساعدة ====================
def format_email_list(emails: List[Dict]) -> str:
    if not emails:
        return "📭 لا توجد رسائل في صندوق الوارد"
    
    result = "📩 <b>صندوق الوارد:</b>\n\n"
    for i, email in enumerate(emails[:10], 1):
        mail_from = email.get('mail_from', 'غير معروف')
        subject = email.get('mail_subject', 'بدون موضوع')
        date = email.get('mail_date', '')
        result += f"{i}. من: {mail_from}\n"
        result += f"   الموضوع: {subject}\n"
        if date:
            result += f"   📅 {date}\n"
        result += f"   🆔 {email.get('mail_id')}\n\n"
    return result

def format_email_content(email_data: Dict) -> str:
    if not email_data or 'error' in email_data:
        return "❌ تعذر قراءة الرسالة"
    
    mail_from = email_data.get('mail_from', 'غير معروف')
    subject = email_data.get('mail_subject', 'بدون موضوع')
    date = email_data.get('mail_date', '')
    body = email_data.get('mail_body', '')
    
    body = re.sub(r'<[^>]+>', '', body)
    body = html.unescape(body)
    
    result = f"📧 <b>من:</b> {mail_from}\n"
    result += f"📌 <b>الموضوع:</b> {subject}\n"
    if date:
        result += f"📅 {date}\n"
    result += f"\n📝 <b>المحتوى:</b>\n{body}\n"
    return result

# ==================== أزرار القوائم ====================
def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📧 بريد مؤقت", callback_data="email_menu", style="primary"),
            InlineKeyboardButton("✨ ستايل نصوص", callback_data="style_menu", style="success"),
        ],
        [
            InlineKeyboardButton("ℹ️ معلومات", callback_data="info", style="primary"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_email_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📧 إنشاء بريد", callback_data="create_email", style="success"),
            InlineKeyboardButton("✏️ تعيين اسم", callback_data="set_username", style="primary"),
        ],
        [
            InlineKeyboardButton("📩 صندوق الوارد", callback_data="inbox", style="primary"),
            InlineKeyboardButton("🔄 تحديث", callback_data="refresh_inbox", style="success"),
        ],
        [
            InlineKeyboardButton("📋 نسخ البريد", callback_data="copy_email", style="success"),
            InlineKeyboardButton("🗑️ حذف البريد", callback_data="delete_email", style="danger"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="primary"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_style_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔤 تغليض", callback_data="style_bold", style="success"),
            InlineKeyboardButton("📏 تمطيط", callback_data="style_stretch", style="success"),
        ],
        [
            InlineKeyboardButton("❝ اقتباس", callback_data="style_quote", style="primary"),
            InlineKeyboardButton("✒️ مائل", callback_data="style_italic", style="primary"),
        ],
        [
            InlineKeyboardButton("✨ مزخرف عربي", callback_data="style_fancy", style="success"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="primary"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stretch_level_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🟢 خفيف", callback_data="stretch_1", style="success"),
            InlineKeyboardButton("🟡 متوسط", callback_data="stretch_2", style="primary"),
        ],
        [
            InlineKeyboardButton("🔴 قوي", callback_data="stretch_3", style="danger"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="style_menu", style="primary"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== معالجات الأوامر ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = f"""
👋 مرحباً {user.first_name}!

أنا بوت متكامل يوفر لك:
📧 بريد إلكتروني مؤقت
✨ ستايلات نصوص احترافية

استخدم الأزرار أدناه للتنقل:
"""
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user = user_data[user_id]
    
    # ---------- القائمة الرئيسية ----------
    if data == "back_main":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = None
        await query.edit_message_text(
            "🏠 القائمة الرئيسية:",
            reply_markup=get_main_menu()
        )
    
    elif data == "email_menu":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = None
        
        if not user.get('sid_token'):
            result = await create_email()
            if 'error' not in result:
                user['sid_token'] = result.get('sid_token')
                user['email'] = result.get('email_addr')
        
        email_info = user.get('email') or "لا يوجد بريد"
        
        await query.edit_message_text(
            f"📧 <b>البريد الإلكتروني:</b>\n<code>{email_info}</code>\n\nاختر إحدى الخيارات:",
            reply_markup=get_email_menu(),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_menu":
        user_waiting_for_username[user_id] = False
        await query.edit_message_text(
            "✨ اختر ستايل النص الذي تريده:\n\n💡 يمكنك الرد على أي رسالة وتطبيق الستايل عليها",
            reply_markup=get_style_menu()
        )
    
    elif data == "info":
        info_text = """
ℹ️ <b>معلومات البوت</b>

<b>📧 البريد المؤقت</b>
• يستخدم Guerrilla Mail API
• إيميلات مؤقتة
• يمكنك تعيين اسم مستخدم مخصص

<b>✨ ستايلات النصوص</b>
• تغليض (Bold)
• تمطيط - 3 مستويات
• اقتباس
• مائل (Italic)
• مزخرف عربي
"""
        await query.edit_message_text(
            info_text,
            parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="primary")
            ]])
        )
    
    # ---------- قسم البريد ----------
    elif data == "create_email":
        result = await create_email()
        if 'error' not in result:
            user['sid_token'] = result.get('sid_token')
            user['email'] = result.get('email_addr')
            user['emails'] = []
            await query.edit_message_text(
                f"✅ تم إنشاء بريد جديد:\n📧 <code>{user['email']}</code>",
                reply_markup=get_email_menu(),
                parse_mode=constants.ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                f"❌ فشل إنشاء البريد: {result.get('error')}",
                reply_markup=get_email_menu()
            )
    
    elif data == "set_username":
        user_waiting_for_username[user_id] = True
        context.user_data['style_action'] = None
        await query.edit_message_text(
            "✏️ أرسل اسم المستخدم المطلوب (أحرف إنجليزية وأرقام فقط):\n\nمثال: myemail",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 إلغاء", callback_data="email_menu", style="danger")
            ]])
        )
    
    elif data in ("inbox", "refresh_inbox"):
        sid_token = user.get('sid_token')
        if not sid_token:
            await query.edit_message_text(
                "❌ لا يوجد بريد مؤقت. قم بإنشاء بريد أولاً.",
                reply_markup=get_email_menu()
            )
            return
        
        result = await get_email_list(sid_token)
        if 'error' in result:
            await query.edit_message_text(
                f"❌ فشل جلب الرسائل: {result.get('error')}",
                reply_markup=get_email_menu()
            )
            return
        
        emails = result.get('list', [])
        user['emails'] = emails
        
        keyboard = []
        for i, email in enumerate(emails[:5], 1):
            subject = (email.get('mail_subject') or 'بدون موضوع')[:20]
            mail_id = email.get('mail_id')
            keyboard.append([
                InlineKeyboardButton(
                    f"📨 {i}. {subject}",
                    callback_data=f"read_{mail_id}",
                    style="primary"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔄 تحديث", callback_data="refresh_inbox", style="success"),
            InlineKeyboardButton("🔙 رجوع", callback_data="email_menu", style="primary")
        ])
        
        await query.edit_message_text(
            format_email_list(emails),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data.startswith("read_"):
        email_id = int(data.split("_")[1])
        sid_token = user.get('sid_token')
        
        if not sid_token:
            await query.edit_message_text("❌ لا يوجد بريد مؤقت.", reply_markup=get_email_menu())
            return
        
        result = await fetch_email(sid_token, email_id)
        if 'error' in result:
            await query.edit_message_text(
                f"❌ فشل قراءة الرسالة: {result.get('error')}",
                reply_markup=get_email_menu()
            )
            return
        
        await query.edit_message_text(
            format_email_content(result),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 العودة للوارد", callback_data="inbox", style="primary")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="email_menu", style="primary")]
            ]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "copy_email":
        email = user.get('email') or "لا يوجد بريد"
        await query.edit_message_text(
            f"📋 البريد الإلكتروني:\n<code>{email}</code>\n\nاضغط على البريد لنسخه",
            reply_markup=get_email_menu(),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "delete_email":
        if user.get('sid_token'):
            user['sid_token'] = None
            user['email'] = None
            user['emails'] = []
            await query.edit_message_text(
                "🗑️ تم حذف البريد الحالي بنجاح",
                reply_markup=get_email_menu()
            )
        else:
            await query.edit_message_text(
                "❌ لا يوجد بريد لحذفه",
                reply_markup=get_email_menu()
            )
    
    # ---------- قسم الستايلات ----------
    elif data == "style_bold":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'bold'
        await query.edit_message_text(
            "🔤 أرسل النص الذي تريد تطبيق <b>التغليض</b> عليه:\nأو قم بالرد على أي رسالة",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_stretch":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'stretch'
        await query.edit_message_text(
            "📏 اختر مستوى التمطيط:",
            reply_markup=get_stretch_level_menu()
        )
    
    elif data == "style_quote":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'quote'
        await query.edit_message_text(
            "❝ أرسل النص الذي تريد تطبيق <b>الاقتباس</b> عليه:\nأو قم بالرد على أي رسالة",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_italic":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'italic'
        await query.edit_message_text(
            "✒️ أرسل النص الذي تريد تطبيق <b>المائل</b> عليه:\nأو قم بالرد على أي رسالة",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_fancy":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'fancy'
        await query.edit_message_text(
            "✨ أرسل النص الذي تريد تطبيق <b>المزخرف العربي</b> عليه:\nأو قم بالرد على أي رسالة",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data.startswith("stretch_"):
        level = int(data.split("_")[1])
        user_stretch_level[user_id] = level
        context.user_data['style_action'] = 'stretch'
        level_names = {1: "خفيف 🟢", 2: "متوسط 🟡", 3: "قوي 🔴"}
        await query.edit_message_text(
            f"📏 تم اختيار المستوى: {level_names[level]}\n\nأرسل النص أو قم بالرد على رسالة",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 تغيير المستوى", callback_data="style_stretch", style="primary"),
                    InlineKeyboardButton("🔙 رجوع", callback_data="style_menu", style="primary")
                ]
            ])
        )

# ==================== معالج الرسائل ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user_id = update.effective_user.id
    
    # ----- تعيين اسم المستخدم -----
    if user_waiting_for_username[user_id]:
        username = message.text.strip()
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            await message.reply_text(
                "❌ اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام فقط (a-z, 0-9, _)",
                reply_markup=get_email_menu()
            )
            return
        
        sid_token = user_data[user_id].get('sid_token')
        if not sid_token:
            await message.reply_text(
                "❌ لا يوجد بريد مؤقت. قم بإنشاء بريد أولاً.",
                reply_markup=get_email_menu()
            )
            user_waiting_for_username[user_id] = False
            return
        
        result = await set_email_user(sid_token, username)
        if 'error' not in result:
            user_data[user_id]['email'] = result.get('email_addr')
            user_data[user_id]['email_user'] = username
            user_data[user_id]['sid_token'] = result.get('sid_token') or sid_token
            await message.reply_text(
                f"✅ تم تعيين اسم المستخدم: <b>{username}</b>\n📧 البريد الجديد: <code>{result.get('email_addr')}</code>",
                reply_markup=get_email_menu(),
                parse_mode=constants.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"❌ فشل تعيين الاسم: {result.get('error')}",
                reply_markup=get_email_menu()
            )
        
        user_waiting_for_username[user_id] = False
        return
    
    # ----- تطبيق الستايلات -----
    style_action = context.user_data.get('style_action')
    if not style_action:
        return
    
    text_to_style = None
    if message.reply_to_message:
        text_to_style = message.reply_to_message.text or message.reply_to_message.caption
    else:
        text_to_style = message.text
    
    if not text_to_style:
        await message.reply_text("❌ لا يوجد نص لتطبيق الستايل عليه")
        return
    
    try:
        if style_action == 'bold':
            styled_text = apply_bold(text_to_style)
            style_name = "تغليض"
        elif style_action == 'italic':
            styled_text = apply_italic(text_to_style)
            style_name = "مائل"
        elif style_action == 'quote':
            styled_text = apply_quote(text_to_style)
            style_name = "اقتباس"
        elif style_action == 'fancy':
            styled_text = apply_fancy_arabic(text_to_style)
            style_name = "مزخرف عربي"
        elif style_action == 'stretch':
            level = user_stretch_level.get(user_id, 1)
            styled_text = apply_stretch(text_to_style, level)
            level_names = {1: "خفيف", 2: "متوسط", 3: "قوي"}
            style_name = f"تمطيط ({level_names[level]})"
        else:
            return
        
        await message.reply_text(
            f"✨ <b>الستايل: {style_name}</b>\n\n{styled_text}",
            parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع للستايلات", callback_data="style_menu", style="primary")
            ]])
        )
        context.user_data['style_action'] = None
        
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")

# ==================== التشغيل ====================
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_message))
    
    print("🚀 البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
