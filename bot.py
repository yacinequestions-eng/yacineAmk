#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام - إيميلات مؤقتة + ستايلات نصوص
"""

import asyncio
import json
import re
import html
import urllib.parse
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
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
    "sid": None,
    "email": None,
    "emails": [],
    "email_user": None
})

user_stretch_level: Dict[int, int] = defaultdict(lambda: 1)

# حالة المستخدمين لتحديد ما إذا كان في وضع تعيين اسم المستخدم
user_waiting_for_username: Dict[int, bool] = defaultdict(lambda: False)

# ==================== دالة تزيين النصوص العربية ====================
def decorate_arabic_text(text: str) -> str:
    """
    تزيين النصوص العربية بإضافة تشكيلات وتطويل الكلمات
    مثال: مرحبا -> مــرحـــبا
    """
    # قائمة الحروف العربية مع تشكيلاتها
    arabic_chars = {
        'ا': 'ا', 'أ': 'أ', 'إ': 'إ', 'آ': 'آ',
        'ب': 'ب', 'ت': 'ت', 'ث': 'ث',
        'ج': 'ج', 'ح': 'ح', 'خ': 'خ',
        'د': 'د', 'ذ': 'ذ', 'ر': 'ر', 'ز': 'ز',
        'س': 'س', 'ش': 'ش', 'ص': 'ص', 'ض': 'ض',
        'ط': 'ط', 'ظ': 'ظ', 'ع': 'ع', 'غ': 'غ',
        'ف': 'ف', 'ق': 'ق', 'ك': 'ك', 'ل': 'ل',
        'م': 'م', 'ن': 'ن', 'ه': 'ه', 'و': 'و', 'ي': 'ي',
        'ة': 'ة', 'ى': 'ى', 'ؤ': 'ؤ', 'ئ': 'ئ'
    }
    
    # علامات التشكيل
    diacritics = ['َ', 'ُ', 'ِ', 'ْ', 'ّ', 'ً', 'ٌ', 'ٍ']
    
    # تشكيلات التطويل
    stretch_marks = ['ـ', 'ـ', 'ـ', 'ـ', 'ـ', 'ـ', 'ـ', 'ـ']
    
    result = []
    for char in text:
        if char in arabic_chars:
            # إضافة الحرف مع تشكيل عشوائي وتطويل
            if char in ['ا', 'و', 'ي', 'ر', 'ل', 'م', 'ن']:
                # حروف يمكن تطويلها
                stretch_count = 2 if len(result) % 2 == 0 else 3
                result.append(char + 'ـ' * stretch_count)
            else:
                # إضافة الحرف مع تشكيل
                import random
                diacritic = diacritics[hash(char + str(len(result))) % len(diacritics)]
                result.append(char + diacritic)
        else:
            result.append(char)
    
    return ''.join(result)

def decorate_text(text: str) -> str:
    """تزيين النص بالكامل مع الحفاظ على الرموز والأرقام"""
    # تقسيم النص إلى كلمات
    words = text.split()
    decorated_words = []
    
    for word in words:
        # التحقق إذا كانت الكلمة عربية
        if any('\u0600' <= c <= '\u06FF' for c in word):
            # تزيين الكلمات العربية
            decorated_words.append(decorate_arabic_text(word))
        else:
            # الحفاظ على الكلمات غير العربية
            decorated_words.append(word)
    
    return ' '.join(decorated_words)

# ==================== دوال Guerrilla Mail API ====================
GUERRILLA_API_BASE = "https://api.guerrillamail.com/ajax.php"

async def guerrilla_request(params: Dict) -> Dict:
    params["ip"] = "127.0.0.1"
    params["agent"] = "telegram_bot"
    
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

async def create_email(sid: Optional[str] = None) -> Dict:
    params = {"f": "get_email_address"}
    if sid:
        params["sid"] = sid
    return await guerrilla_request(params)

async def set_email_user(sid: str, email_user: str) -> Dict:
    params = {
        "f": "set_email_user",
        "sid": sid,
        "email_user": email_user
    }
    return await guerrilla_request(params)

async def get_email_list(sid: str, offset: int = 0) -> Dict:
    params = {
        "f": "get_email_list",
        "sid": sid,
        "offset": offset
    }
    return await guerrilla_request(params)

async def fetch_email(sid: str, email_id: int) -> Dict:
    params = {
        "f": "fetch_email",
        "sid": sid,
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
    if level == 1:
        return ''.join(char * 2 for char in text)
    elif level == 2:
        return ''.join(char * 3 for char in text)
    else:
        return ''.join(char * 4 for char in text)

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
        return "📭 لــا تــوجــد رِســائــل فــي صــنــدوق الــوارِد"
    
    result = "📩 صــنــدوق الــوارِد:\n\n"
    for i, email in enumerate(emails[:10], 1):
        mail_from = email.get('mail_from', 'غــيــر مــعــروف')
        subject = email.get('mail_subject', 'بــدون مــوضــوع')
        date = email.get('mail_date', '')
        result += f"{i}. مــن: {mail_from}\n"
        result += f"   الــمــوضــوع: {subject}\n"
        if date:
            result += f"   📅 {date}\n"
        result += f"   🆔 {email.get('mail_id')}\n\n"
    return result

def format_email_content(email_data: Dict) -> str:
    if not email_data or 'error' in email_data:
        return "❌ تــعــذر قــراءة الــرِّســالــة"
    
    mail_from = email_data.get('mail_from', 'غــيــر مــعــروف')
    subject = email_data.get('mail_subject', 'بــدون مــوضــوع')
    date = email_data.get('mail_date', '')
    body = email_data.get('mail_body', '')
    
    body = re.sub(r'<[^>]+>', '', body)
    body = html.unescape(body)
    
    result = f"📧 مــن: {mail_from}\n"
    result += f"📌 الــمــوضــوع: {subject}\n"
    if date:
        result += f"📅 {date}\n"
    result += f"\n📝 الــمــحــتــوى:\n{body}\n"
    return result

# ==================== أزرار القائمة الرئيسية ====================
def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📧 بــريــد مــؤقــت",
                callback_data="email_menu",
                style="primary"
            ),
            InlineKeyboardButton(
                "✨ ســتــايــل نــصــوص",
                callback_data="style_menu",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ مــعــلــومــات",
                callback_data="info",
                style="primary"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_email_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "📧 إنــشــاء بــريــد",
                callback_data="create_email",
                style="success"
            ),
            InlineKeyboardButton(
                "✏️ تــعــيــيــن اســم",
                callback_data="set_username",
                style="primary"
            ),
        ],
        [
            InlineKeyboardButton(
                "📩 صــنــدوق الــوارِد",
                callback_data="inbox",
                style="primary"
            ),
            InlineKeyboardButton(
                "🔄 تــحــديــث",
                callback_data="refresh_inbox",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 نــســخ الــبــريــد",
                callback_data="copy_email",
                style="success"
            ),
            InlineKeyboardButton(
                "🗑️ حــذف الــبــريــد",
                callback_data="delete_email",
                style="danger"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 رجــوع",
                callback_data="back_main",
                style="primary"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_style_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🔤 تــغــلــيــض",
                callback_data="style_bold",
                style="success"
            ),
            InlineKeyboardButton(
                "📏 تــمــطــيــط",
                callback_data="style_stretch",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                "❝ اقــتــبــاس",
                callback_data="style_quote",
                style="primary"
            ),
            InlineKeyboardButton(
                "✒️ مــائــل",
                callback_data="style_italic",
                style="primary"
            ),
        ],
        [
            InlineKeyboardButton(
                "✨ مــزخــرف عــربــي",
                callback_data="style_fancy",
                style="success"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 رجــوع",
                callback_data="back_main",
                style="primary"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stretch_level_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🟢 خــفــيــف",
                callback_data="stretch_1",
                style="success"
            ),
            InlineKeyboardButton(
                "🟡 مــتــوســط",
                callback_data="stretch_2",
                style="primary"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔴 قــوي",
                callback_data="stretch_3",
                style="danger"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 رجــوع",
                callback_data="style_menu",
                style="primary"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== معالجات الأوامر ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = f"""
👋 مــرحــبــاً {decorate_text(user.first_name)}!

أنا بــوت مــتــكــامــل يــوفــر لــك:
📧 بــريــد إلــكــتــرونــي مــؤقــت
✨ ســتــايــلات نــصــوص احــتــرافــيــة

اســتــخــدم الأزرار أدناه لــلــتــنــقــل:
"""
    await update.message.reply_text(
        decorate_text(welcome_text),
        reply_markup=get_main_menu(),
        parse_mode=constants.ParseMode.HTML
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user = user_data[user_id]
    
    if data == "back_main":
        await query.edit_message_text(
            decorate_text("🏠 الــقــائــمــة الــرئــيــســيــة:"),
            reply_markup=get_main_menu()
        )
    
    elif data == "email_menu":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = None
        
        email_info = user.get('email', 'لا يــوجــد بــريــد')
        sid_info = user.get('sid', 'لا يــوجــد جــلــســة')
        
        if not user.get('sid'):
            result = await create_email()
            if 'error' not in result:
                user['sid'] = result.get('sid')
                user['email'] = result.get('email_addr')
                email_info = user['email']
        
        await query.edit_message_text(
            decorate_text(
                f"📧 الــبــريــد الإلــكــتــرونــي: {email_info}\n"
                f"🆔 مــعــرف الــجــلــســة: {sid_info[:10] if sid_info != 'لا يــوجــد جــلــســة' else 'لا يــوجــد'}...\n\n"
                "اخــتــر إحــدى الــخــيــارات:"
            ),
            reply_markup=get_email_menu()
        )
    
    elif data == "style_menu":
        user_waiting_for_username[user_id] = False
        
        await query.edit_message_text(
            decorate_text(
                "✨ اخــتــر ســتــايــل الــنــص الــذي تــريــده:\n\n"
                "💡 يــمــكــنــك الــرد عــلى أي رِســالــة وتــطــبــيــق الــســتــايــل عــلــيــها"
            ),
            reply_markup=get_style_menu()
        )
    
    elif data == "info":
        info_text = """
ℹ️ <b>مــعــلــومــات الــبــوت</b>

<b>📧 الــبــريــد الــمــؤقــت</b>
• يــســتــخــدم Guerrilla Mail API
• إيــمــيــلات مــؤقــتــة لــمــدة ســاعــة
• يــمــكــنــك تــعــيــيــن اســم مــســتــخــدم مــخــصــص

<b>✨ ســتــايــلات الــنــصــوص</b>
• تــغــلــيــض (Bold)
• تــمــطــيــط - 3 مــســتــويــات
• اقــتــبــاس
• مــائــل (Italic)
• مــزخــرف عــربــي

<b>🔧 الــتــقــنــيــات</b>
• Python 3.10+
• python-telegram-bot 20.0+
• Guerrilla Mail API
        """
        await query.edit_message_text(
            decorate_text(info_text),
            parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجــوع", callback_data="back_main", style="primary")
            ]])
        )
    
    elif data == "create_email":
        result = await create_email()
        if 'error' not in result:
            user['sid'] = result.get('sid')
            user['email'] = result.get('email_addr')
            user['emails'] = []
            await query.edit_message_text(
                decorate_text(
                    f"✅ تــم إنــشــاء بــريــد جــديــد:\n📧 {user['email']}\n\n"
                    f"🆔 مــعــرف الــجــلــســة: {user['sid'][:15]}..."
                ),
                reply_markup=get_email_menu()
            )
        else:
            await query.edit_message_text(
                decorate_text(f"❌ فــشــل إنــشــاء الــبــريــد: {result.get('error')}"),
                reply_markup=get_email_menu()
            )
    
    elif data == "set_username":
        user_waiting_for_username[user_id] = True
        context.user_data['style_action'] = None
        
        await query.edit_message_text(
            decorate_text(
                "✏️ أرســل اســم الــمــســتــخــدم الــمــطــلــوب (أحــرف وأرقــام فــقــط):\n\n"
                "مــثــال: myemail"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 إلــغــاء", callback_data="email_menu", style="danger")
            ]])
        )
    
    elif data == "inbox" or data == "refresh_inbox":
        sid = user.get('sid')
        if not sid:
            await query.edit_message_text(
                decorate_text("❌ لا يــوجــد بــريــد مــؤقــت. قــم بإنــشــاء بــريــد أوّلاً."),
                reply_markup=get_email_menu()
            )
            return
        
        result = await get_email_list(sid)
        if 'error' in result:
            await query.edit_message_text(
                decorate_text(f"❌ فــشــل جــلــب الــرِّســائــل: {result.get('error')}"),
                reply_markup=get_email_menu()
            )
            return
        
        emails = result.get('list', [])
        user['emails'] = emails
        
        keyboard = []
        for i, email in enumerate(emails[:5], 1):
            subject = email.get('mail_subject', 'بــدون مــوضــوع')[:20]
            mail_id = email.get('mail_id')
            keyboard.append([
                InlineKeyboardButton(
                    f"📨 {i}. {subject}",
                    callback_data=f"read_{mail_id}",
                    style="primary"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔄 تــحــديــث", callback_data="refresh_inbox", style="success"),
            InlineKeyboardButton("🔙 رجــوع", callback_data="email_menu", style="primary")
        ])
        
        await query.edit_message_text(
            decorate_text(format_email_list(emails)),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data.startswith("read_"):
        email_id = int(data.split("_")[1])
        sid = user.get('sid')
        
        if not sid:
            await query.edit_message_text(
                decorate_text("❌ لا يــوجــد بــريــد مــؤقــت."),
                reply_markup=get_email_menu()
            )
            return
        
        result = await fetch_email(sid, email_id)
        if 'error' in result:
            await query.edit_message_text(
                decorate_text(f"❌ فــشــل قــراءة الــرِّســالــة: {result.get('error')}"),
                reply_markup=get_email_menu()
            )
            return
        
        await query.edit_message_text(
            decorate_text(format_email_content(result)),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 الــعــودة لــلــوارِد", callback_data="inbox", style="primary")],
                [InlineKeyboardButton("🔙 رجــوع", callback_data="email_menu", style="primary")]
            ]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "copy_email":
        email = user.get('email', 'لا يــوجــد بــريــد')
        await query.edit_message_text(
            decorate_text(
                f"📋 الــبــريــد الإلــكــتــرونــي:\n<code>{email}</code>\n\n"
                "تــم نــســخ الــبــريــد لــلــحــافــظــة (اضــغــط لــلــنــســخ)"
            ),
            reply_markup=get_email_menu(),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "delete_email":
        if user.get('sid'):
            user['sid'] = None
            user['email'] = None
            user['emails'] = []
            await query.edit_message_text(
                decorate_text("🗑️ تــم حــذف الــبــريــد الــحــالــي بــنــجــاح"),
                reply_markup=get_email_menu()
            )
        else:
            await query.edit_message_text(
                decorate_text("❌ لا يــوجــد بــريــد لــحــذفــه"),
                reply_markup=get_email_menu()
            )
    
    # ==================== أزرار الستايلات ====================
    elif data == "style_bold":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'bold'
        
        await query.edit_message_text(
            decorate_text(
                "🔤 أرســل الــنــص الــذي تــريــد تــطــبــيــق ســتــايــل <b>التغليض</b> عــلــيــه:\n\n"
                "أو قــم بــالــرد عــلى أي رِســالــة وســيــتــم تــطــبــيــق الــســتــايــل عــلــيــها"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجــوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_stretch":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'stretch'
        
        await query.edit_message_text(
            decorate_text("📏 اخــتــر مــســتــوى الــتــمــطــيــط:"),
            reply_markup=get_stretch_level_menu()
        )
    
    elif data == "style_quote":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'quote'
        
        await query.edit_message_text(
            decorate_text(
                "❝ أرســل الــنــص الــذي تــريــد تــطــبــيــق ســتــايــل <b>الاقتباس</b> عــلــيــه:\n\n"
                "أو قــم بــالــرد عــلى أي رِســالــة وســيــتــم تــطــبــيــق الــســتــايــل عــلــيــها"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجــوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_italic":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'italic'
        
        await query.edit_message_text(
            decorate_text(
                "✒️ أرســل الــنــص الــذي تــريــد تــطــبــيــق ســتــايــل <b>المائل</b> عــلــيــه:\n\n"
                "أو قــم بــالــرد عــلى أي رِســالــة وســيــتــم تــطــبــيــق الــســتــايــل عــلــيــها"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجــوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data == "style_fancy":
        user_waiting_for_username[user_id] = False
        context.user_data['style_action'] = 'fancy'
        
        await query.edit_message_text(
            decorate_text(
                "✨ أرســل الــنــص الــذي تــريــد تــطــبــيــق ســتــايــل <b>المزخرف العربي</b> عــلــيــه:\n\n"
                "أو قــم بــالــرد عــلى أي رِســالــة وســيــتــم تــطــبــيــق الــســتــايــل عــلــيــها"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجــوع", callback_data="style_menu", style="primary")
            ]]),
            parse_mode=constants.ParseMode.HTML
        )
    
    elif data.startswith("stretch_"):
        level = int(data.split("_")[1])
        user_stretch_level[user_id] = level
        context.user_data['style_action'] = 'stretch'
        
        level_names = {1: "خــفــيــف 🟢", 2: "مــتــوســط 🟡", 3: "قــوي 🔴"}
        await query.edit_message_text(
            decorate_text(
                f"📏 تــم اخــتــيــار الــمــســتــوى: {level_names[level]}\n\n"
                "أرســل الــنــص الــذي تــريــد تــطــبــيــق <b>التمطيط</b> عــلــيــه:\n"
                "أو قــم بــالــرد عــلى أي رِســالــة وســيــتــم تــطــبــيــق الــســتــايــل عــلــيــها"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 تــغــيــيــر الــمــســتــوى", callback_data="style_stretch", style="primary"),
                    InlineKeyboardButton("🔙 رجــوع", callback_data="style_menu", style="primary")
                ]
            ]),
            parse_mode=constants.ParseMode.HTML
        )

# ==================== معالج تعيين اسم المستخدم ====================
async def handle_set_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user_id = update.effective_user.id
    
    if not user_waiting_for_username[user_id]:
        return
    
    username = message.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        await message.reply_text(
            decorate_text("❌ اســم الــمــســتــخــدم يــجــب أن يــحــتــوي عــلى أحــرف وأرقــام فــقــط (a-z, A-Z, 0-9, _)"),
            reply_markup=get_email_menu()
        )
        return
    
    sid = user_data[user_id].get('sid')
    if not sid:
        await message.reply_text(
            decorate_text("❌ لا يــوجــد بــريــد مــؤقــت. قــم بإنــشــاء بــريــد أوّلاً."),
            reply_markup=get_email_menu()
        )
        user_waiting_for_username[user_id] = False
        return
    
    result = await set_email_user(sid, username)
    if 'error' not in result:
        user_data[user_id]['email'] = result.get('email_addr')
        user_data[user_id]['email_user'] = username
        await message.reply_text(
            decorate_text(
                f"✅ تــم تــعــيــيــن اســم الــمــســتــخــدم: {username}\n"
                f"📧 الــبــريــد الــجــديــد: {result.get('email_addr')}"
            ),
            reply_markup=get_email_menu()
        )
    else:
        await message.reply_text(
            decorate_text(f"❌ فــشــل تــعــيــيــن الــاســم: {result.get('error')}"),
            reply_markup=get_email_menu()
        )
    
    user_waiting_for_username[user_id] = False

# ==================== معالج الرسائل للستايلات ====================
async def handle_style_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user_id = update.effective_user.id
    
    if user_waiting_for_username[user_id]:
        return
    
    text_to_style = None
    
    if message.reply_to_message:
        text_to_style = message.reply_to_message.text or message.reply_to_message.caption
        if not text_to_style:
            await message.reply_text(decorate_text("❌ الــرِّســالــة الــمــقــابــلة لا تــحــتــوي عــلى نــص"))
            return
    else:
        text_to_style = message.text
        if not text_to_style:
            await message.reply_text(decorate_text("❌ أرســل نــصــاً لــلــتــنــســيــق"))
            return
    
    style_action = context.user_data.get('style_action')
    if not style_action:
        await message.reply_text(
            decorate_text("❌ يــرجــى اخــتــيــار ســتــايــل أوّلاً مــن الــقــائــمــة"),
            reply_markup=get_main_menu()
        )
        return
    
    styled_text = text_to_style
    style_name = ""
    
    try:
        if style_action == 'bold':
            styled_text = apply_bold(text_to_style)
            style_name = "تــغــلــيــض"
        elif style_action == 'italic':
            styled_text = apply_italic(text_to_style)
            style_name = "مــائــل"
        elif style_action == 'quote':
            styled_text = apply_quote(text_to_style)
            style_name = "اقــتــبــاس"
        elif style_action == 'fancy':
            styled_text = apply_fancy_arabic(text_to_style)
            style_name = "مــزخــرف عــربــي"
        elif style_action == 'stretch':
            level = user_stretch_level.get(user_id, 1)
            styled_text = apply_stretch(text_to_style, level)
            level_names = {1: "خــفــيــف", 2: "مــتــوســط", 3: "قــوي"}
            style_name = f"تــمــطــيــط ({level_names[level]})"
        else:
            await message.reply_text(decorate_text("❌ ســتــايــل غــيــر مــعــروف"))
            return
        
        # تزيين النص الناتج أيضاً
        styled_text = decorate_text(styled_text)
        
        await message.reply_text(
            f"✨ <b>الــســتــايــل: {style_name}</b>\n\n{styled_text}",
            parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجــوع لــلــســتــايــلات", callback_data="style_menu", style="primary")
            ]])
        )
        
        context.user_data['style_action'] = None
        
    except Exception as e:
        await message.reply_text(decorate_text(f"❌ حــدث خــطــأ أثــنــاء تــطــبــيــق الــســتــايــل: {str(e)}"))

# ==================== الدالة الرئيسية ====================
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_set_username
        )
    )
    
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_style_message
        )
    )
    
    print("🚀 البوت يعمل الآن...")
    print(f"📱 توكن البوت: {BOT_TOKEN[:10]}...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
