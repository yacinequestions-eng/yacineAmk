# ============================================================
#  ✿ ⌘ ⌬ ✪  بوت DARK HUNTER – الإصدار النهائي  ✿ ⌘ ⌬ ✪
#  [تم إدخال بيانات API الخاصة بك]
# ============================================================

import asyncio
import sqlite3
import re
import time
import os
import logging
import json
import csv
import shutil
import sys
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired

# ================== الإعدادات (بياناتك) ==================
API_ID = 33133213
API_HASH = "3a651b67145433de258b2112c72e8d86"
BOT_TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"

# ================== إعدادات التسجيل ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ✿ %(levelname)s - ⌘ %(message)s',
    handlers=[logging.FileHandler("dark_hunter.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ================== إنشاء العميل ==================
app = Client(
    "dark_hunter_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=20,
    parse_mode="Markdown"
)

# ================== قاعدة البيانات ==================
DB_PATH = "dark_files.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE,
            title TEXT,
            added_at INTEGER,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            file_name TEXT,
            file_id TEXT,
            file_size INTEGER,
            mime_type TEXT,
            message_id INTEGER,
            date INTEGER,
            downloaded INTEGER DEFAULT 0,
            FOREIGN KEY(channel_id) REFERENCES channels(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("⌬ تم تهيئة قاعدة البيانات بنجاح")

init_db()

# ================== دوال مساعدة ==================
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def add_channel(link, title):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO channels (link, title, added_at, status) VALUES (?, ?, ?, ?)",
                  (link, title, int(time.time()), 'active'))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def add_file(channel_id, file_name, file_id, file_size, mime_type, message_id, date):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO files (channel_id, file_name, file_id, file_size, mime_type, message_id, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (channel_id, file_name, file_id, file_size, mime_type, message_id, date))
    conn.commit()
    conn.close()

def get_channels():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, link, title FROM channels WHERE status = 'active'")
    result = c.fetchall()
    conn.close()
    return result

def get_all_files():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT f.id, f.file_name, f.file_id, f.file_size, f.date, c.title FROM files f JOIN channels c ON f.channel_id = c.id ORDER BY f.date DESC")
    result = c.fetchall()
    conn.close()
    return result

def count_files():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM files")
    result = c.fetchone()[0]
    conn.close()
    return result

def count_channels():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM channels WHERE status = 'active'")
    result = c.fetchone()[0]
    conn.close()
    return result

def update_channel_status(channel_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE channels SET status = ? WHERE id = ?", (status, channel_id))
    conn.commit()
    conn.close()

def remove_channel(channel_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()

def format_time(timestamp):
    if not timestamp:
        return "✿ غير معروف"
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "✿ غير معروف"

def format_size(size):
    if not size:
        return "غير معروف"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def is_valid_channel_link(link):
    patterns = [
        r'^https?://t\.me/[a-zA-Z0-9_]+$',
        r'^https?://t\.me/joinchat/[a-zA-Z0-9_-]+$',
        r'^https?://t\.me/\+[a-zA-Z0-9_-]+$',
    ]
    for pattern in patterns:
        if re.match(pattern, link):
            return True
    return False

# ================== دالة البحث ==================
async def search_dark_files_in_channel(channel_id, channel_link, limit=500):
    logger.info(f"⌬ بدأ البحث في القناة: {channel_link}")
    found_count = 0
    
    try:
        try:
            await app.join_chat(channel_link)
            logger.info(f"✅ تم الانضمام إلى {channel_link}")
        except Exception as e:
            logger.warning(f"⚠️ فشل الانضمام إلى {channel_link}: {e}")
            update_channel_status(channel_id, 'error')
            return 0
        
        try:
            async for message in app.get_chat_history(channel_link, limit=limit):
                if message.document:
                    file_name = message.document.file_name or ""
                    if file_name.lower().endswith('.dark'):
                        file_id = message.document.file_id
                        file_size = message.document.file_size
                        mime_type = message.document.mime_type or "unknown"
                        msg_id = message.id
                        date = message.date.timestamp() if message.date else int(time.time())
                        
                        add_file(channel_id, file_name, file_id, file_size, mime_type, msg_id, date)
                        found_count += 1
                        logger.info(f"✪ تم العثور على ملف: {file_name}")
                        
        except FloodWait as e:
            logger.warning(f"⏳ تم حظر الطلب لمدة {e.value} ثانية")
            await asyncio.sleep(e.value)
            return await search_dark_files_in_channel(channel_id, channel_link, limit)
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الرسائل: {e}")
            update_channel_status(channel_id, 'error')
            return found_count
            
        update_channel_status(channel_id, 'done')
        logger.info(f"⌘ تم الانتهاء من البحث في {channel_link} - وجد {found_count} ملف")
        return found_count
        
    except Exception as e:
        logger.error(f"✿ خطأ في البحث: {e}")
        update_channel_status(channel_id, 'error')
        return found_count

async def search_all_channels(limit=500):
    channels = get_channels()
    if not channels:
        return 0
    
    total_files = 0
    for ch_id, link, title in channels:
        try:
            count = await search_dark_files_in_channel(ch_id, link, limit)
            total_files += count
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"✿ خطأ في القناة {link}: {e}")
    
    return total_files

# ================== الكيبوردات ==================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("🔍 بحث فوري", callback_data="search_now")],
        [InlineKeyboardButton("📋 قائمة القنوات", callback_data="list_channels")],
        [InlineKeyboardButton("📄 عرض الملفات", callback_data="list_files")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh")],
        [InlineKeyboardButton("❓ مساعدة", callback_data="help")],
    ])

def back_to_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
    ])

# ================== الأوامر الرئيسية ==================
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user = message.from_user
    welcome_text = f"""
✿ ⌘ ⌬ ✪ *بوت DARK HUNTER* ✪ ⌬ ⌘ ✿

╭━━━〔 ✿ Y A C I N E   T X ✿ 〕━━━╮
┃
┃  ⌬ *بوت استخراج ملفات .dark*
┃  
┃  ✪ البوت الأقوى لاستخراج الملفات
┃  التي تنتهي بـ `.dark` من القنوات.
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  ✿ *المطور:* `Y A C I N E   T X`
┃  ⌘ *الإصدار:* `v5.0.0`
┃  ⌬ *الحالة:* `نشط 🟢`
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  📌 *الأوامر المتاحة:*
┃
┃  /start  ✿ الصفحة الرئيسية
┃  /addchannel  ⌘ إضافة قناة
┃  /searchdark  ⌬ بحث فوري
┃  /listchannels  ✪ عرض القنوات
┃  /listfiles  ✿ عرض الملفات
┃  /stats  ⌘ الإحصائيات
┃  /removechannel  ⌬ حذف قناة
┃  /export  ✪ تصدير النتائج
┃  /help  ✿ المساعدة
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  🎯 *مثال:*
┃
┃  /addchannel https://t.me/example
┃  /searchdark
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  👨‍💻 *المطور:* `Y A C I N E   T X`
┃  ⌬ جميع الحقوق محفوظة ©
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
    await message.reply(welcome_text, reply_markup=main_menu_keyboard())

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    help_text = """
✿ ⌘ ⌬ ✪ *دليل البوت* ✪ ⌬ ⌘ ✿

╭━━━〔 ✿ Y A C I N E   T X ✿ 〕━━━╮
┃
┃  ⌬ *الأوامر المتاحة:*
┃
┃  /start  ✿ الصفحة الرئيسية
┃  /addchannel <رابط>  ⌘ إضافة قناة
┃  /searchdark  ⌬ بحث فوري عن .dark
┃  /listchannels  ✪ عرض القنوات المضافة
┃  /listfiles  ✿ عرض الملفات المستخرجة
┃  /stats  ⌘ الإحصائيات
┃  /removechannel <id>  ⌬ حذف قناة
┃  /export  ✪ تصدير النتائج
┃  /help  ✿ عرض هذه القائمة
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  📌 *نصائح:*
┃
┃  ✿ تأكد من أن البوت لديه صلاحية الدخول.
┃  ⌘ يمكن إضافة قنوات عامة وخاصة.
┃  ⌬ البحث يستخرج فقط الملفات التي تنتهي بـ `.dark`
┃  ✪ النتائج تُحفظ في قاعدة البيانات.
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  👨‍💻 *المطور:* `Y A C I N E   T X`
┃  ⌬ جميع الحقوق محفوظة ©
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
    await message.reply(help_text, reply_markup=back_to_main_keyboard())

@app.on_message(filters.command("addchannel") & filters.private)
async def add_channel_command(client, message):
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            await message.reply("❌ *استخدم:* `/addchannel <رابط القناة>`\nمثال: `/addchannel https://t.me/example`")
            return
        
        link = parts[1].strip()
        
        if not is_valid_channel_link(link):
            await message.reply("❌ *رابط غير صحيح!* يرجى إدخال رابط قناة صحيح.")
            return
        
        try:
            chat = await app.join_chat(link)
            title = chat.title or "بدون عنوان"
            
            channel_id = add_channel(link, title)
            if channel_id:
                await message.reply(f"✅ *تم إضافة القناة بنجاح!*\n📌 *العنوان:* `{title}`\n🆔 *المعرف:* `{channel_id}`")
            else:
                await message.reply("⚠️ *القناة موجودة مسبقاً.*")
        except UserNotParticipant:
            await message.reply("❌ *لا يمكن الانضمام للقناة!* قد تكون القناة خاصة أو محظورة.")
        except ChatAdminRequired:
            await message.reply("❌ *البوت يحتاج صلاحيات إضافية.*")
        except Exception as e:
            await message.reply(f"❌ *خطأ:* `{str(e)}`")
            
    except Exception as e:
        await message.reply(f"❌ *خطأ:* `{str(e)}`")

@app.on_message(filters.command("searchdark") & filters.private)
async def search_command(client, message):
    channels = get_channels()
    if not channels:
        await message.reply("❌ *لا توجد قنوات مضافة!*\nاستخدم `/addchannel` لإضافة قناة.")
        return
    
    msg = await message.reply("⏳ *جاري البحث عن ملفات `.dark` في جميع القنوات...*\n⏱️ قد يستغرق هذا بعض الوقت.")
    
    try:
        total = await search_all_channels(limit=500)
        await msg.edit_text(f"✅ *اكتمل البحث!*\n📂 *تم العثور على* `{total}` *ملف.*\nاستخدم `/listfiles` لعرضها.")
    except Exception as e:
        await msg.edit_text(f"❌ *خطأ أثناء البحث:* `{str(e)}`")

@app.on_message(filters.command("listchannels") & filters.private)
async def list_channels_command(client, message):
    channels = get_channels()
    if not channels:
        await message.reply("❌ *لا توجد قنوات مضافة.*")
        return
    
    text = "📋 *قائمة القنوات المضافة:*\n\n"
    for ch_id, link, title in channels:
        text += f"🆔 `{ch_id}` ─ ✿ `{title}`\n📍 {link}\n\n"
    
    await message.reply(text)

@app.on_message(filters.command("listfiles") & filters.private)
async def list_files_command(client, message):
    files = get_all_files()
    if not files:
        await message.reply("❌ *لا توجد ملفات مستخرجة بعد.*\nاستخدم `/searchdark` للبحث.")
        return
    
    text = "📂 *الملفات المستخرجة (.dark):*\n\n"
    for f_id, f_name, f_id_str, f_size, f_date, channel_title in files[:50]:
        text += f"📄 `{f_name}`\n"
        text += f"   ✿ الحجم: `{format_size(f_size)}`\n"
        text += f"   ⌘ القناة: `{channel_title}`\n"
        text += f"   ⌬ التاريخ: `{format_time(f_date)}`\n\n"
    
    total = len(files)
    if total > 50:
        text += f"\n📌 *عرض 50 من {total} ملف.* استخدم `/export` لتصدير الكل."
    
    await message.reply(text)

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message):
    total_files = count_files()
    total_channels = count_channels()
    
    stats_text = f"""
✿ ⌘ ⌬ ✪ *الإحصائيات* ✪ ⌬ ⌘ ✿

╭━━━〔 ✿ Y A C I N E   T X ✿ 〕━━━╮
┃
┃  ⌬ *إحصائيات البوت*
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  ✿ *القنوات المضافة:* `{total_channels}`
┃  ⌘ *الملفات المستخرجة:* `{total_files}`
┃  ⌬ *آخر تحديث:* `{format_time(int(time.time()))}`
┃  ✪ *الحالة:* `نشط 🟢`
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  👨‍💻 *المطور:* `Y A C I N E   T X`
┃  ⌬ جميع الحقوق محفوظة ©
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
    await message.reply(stats_text)

@app.on_message(filters.command("export") & filters.private)
async def export_command(client, message):
    files = get_all_files()
    if not files:
        await message.reply("❌ *لا توجد ملفات لتصديرها.*")
        return
    
    filename = f"dark_files_export_{int(time.time())}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("✿ ⌘ ⌬ ✪ قائمة ملفات .dark المستخرجة ✪ ⌬ ⌘ ✿\n\n")
        f.write(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"📂 إجمالي الملفات: {len(files)}\n\n")
        f.write("=" * 60 + "\n\n")
        
        for f_id, f_name, f_id_str, f_size, f_date, channel_title in files:
            f.write(f"📄 اسم الملف: {f_name}\n")
            f.write(f"📦 الحجم: {format_size(f_size)}\n")
            f.write(f"📌 القناة: {channel_title}\n")
            f.write(f"📅 التاريخ: {format_time(f_date)}\n")
            f.write(f"🆔 File ID: {f_id_str}\n")
            f.write("-" * 40 + "\n")
    
    await message.reply_document(document=filename, caption="📂 *ملف تصدير النتائج*")
    os.remove(filename)

@app.on_message(filters.command("removechannel") & filters.private)
async def remove_channel_command(client, message):
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            await message.reply("❌ *استخدم:* `/removechannel <id>`\nاستخدم `/listchannels` لعرض المعرفات.")
            return
        
        channel_id = int(parts[1].strip())
        remove_channel(channel_id)
        await message.reply(f"✅ *تم حذف القناة رقم* `{channel_id}`")
    except ValueError:
        await message.reply("❌ *المعرف يجب أن يكون رقماً.*")
    except Exception as e:
        await message.reply(f"❌ *خطأ:* `{str(e)}`")

# ================== معالجة الـ Callbacks ==================
@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "main_menu":
        await callback_query.message.edit_text(
            "✿ ⌘ ⌬ ✪ *القائمة الرئيسية* ✪ ⌬ ⌘ ✿\n\nاختر الخدمة التي تريدها:",
            reply_markup=main_menu_keyboard()
        )
        await callback_query.answer()
    
    elif data == "add_channel":
        await callback_query.message.edit_text(
            "📌 *أرسل رابط القناة*\n\nمثال: `/addchannel https://t.me/example`",
            reply_markup=back_to_main_keyboard()
        )
        await callback_query.answer()
    
    elif data == "search_now":
        await callback_query.message.edit_text(
            "⏳ *جاري البحث عن ملفات `.dark`...*\n⏱️ قد يستغرق هذا بعض الوقت.",
            reply_markup=back_to_main_keyboard()
        )
        await callback_query.answer()
        
        channels = get_channels()
        if not channels:
            await callback_query.message.reply("❌ *لا توجد قنوات مضافة!*")
            return
        
        try:
            total = await search_all_channels(limit=500)
            await callback_query.message.reply(
                f"✅ *اكتمل البحث!*\n📂 *تم العثور على* `{total}` *ملف.*"
            )
        except Exception as e:
            await callback_query.message.reply(f"❌ *خطأ:* `{str(e)}`")
    
    elif data == "list_channels":
        channels = get_channels()
        if not channels:
            await callback_query.message.edit_text(
                "❌ *لا توجد قنوات مضافة.*",
                reply_markup=back_to_main_keyboard()
            )
            await callback_query.answer()
            return
        
        text = "📋 *قائمة القنوات المضافة:*\n\n"
        for ch_id, link, title in channels:
            text += f"🆔 `{ch_id}` ─ ✿ `{title}`\n📍 {link}\n\n"
        
        await callback_query.message.edit_text(text, reply_markup=back_to_main_keyboard())
        await callback_query.answer()
    
    elif data == "list_files":
        files = get_all_files()
        if not files:
            await callback_query.message.edit_text(
                "❌ *لا توجد ملفات مستخرجة بعد.*",
                reply_markup=back_to_main_keyboard()
            )
            await callback_query.answer()
            return
        
        text = "📂 *الملفات المستخرجة (.dark):*\n\n"
        for f_id, f_name, f_id_str, f_size, f_date, channel_title in files[:30]:
            text += f"📄 `{f_name}`\n"
            text += f"   ✿ الحجم: `{format_size(f_size)}`\n"
            text += f"   ⌘ القناة: `{channel_title}`\n\n"
        
        total = len(files)
        if total > 30:
            text += f"\n📌 *عرض 30 من {total} ملف.*"
        
        await callback_query.message.edit_text(text, reply_markup=back_to_main_keyboard())
        await callback_query.answer()
    
    elif data == "stats":
        total_files = count_files()
        total_channels = count_channels()
        
        stats_text = f"""
✿ ⌘ ⌬ ✪ *الإحصائيات* ✪ ⌬ ⌘ ✿

╭━━━〔 ✿ Y A C I N E   T X ✿ 〕━━━╮
┃
┃  ⌬ *إحصائيات البوت*
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  ✿ *القنوات المضافة:* `{total_channels}`
┃  ⌘ *الملفات المستخرجة:* `{total_files}`
┃  ⌬ *آخر تحديث:* `{format_time(int(time.time()))}`
┃  ✪ *الحالة:* `نشط 🟢`
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  👨‍💻 *المطور:* `Y A C I N E   T X`
┃  ⌬ جميع الحقوق محفوظة ©
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
        await callback_query.message.edit_text(stats_text, reply_markup=back_to_main_keyboard())
        await callback_query.answer()
    
    elif data == "refresh":
        await callback_query.message.edit_text(
            "🔄 *جاري تحديث البيانات...*",
            reply_markup=back_to_main_keyboard()
        )
        await callback_query.answer()
        
        total_files = count_files()
        total_channels = count_channels()
        
        await callback_query.message.reply(
            f"✅ *تم التحديث!*\n📂 {total_files} ملف\n📌 {total_channels} قناة"
        )
    
    elif data == "help":
        help_text = """
✿ ⌘ ⌬ ✪ *دليل البوت* ✪ ⌬ ⌘ ✿

╭━━━〔 ✿ Y A C I N E   T X ✿ 〕━━━╮
┃
┃  ⌬ *الأوامر المتاحة:*
┃
┃  /start  ✿ الصفحة الرئيسية
┃  /addchannel <رابط>  ⌘ إضافة قناة
┃  /searchdark  ⌬ بحث فوري
┃  /listchannels  ✪ عرض القنوات
┃  /listfiles  ✿ عرض الملفات
┃  /stats  ⌘ الإحصائيات
┃  /removechannel <id>  ⌬ حذف قناة
┃  /export  ✪ تصدير النتائج
┃  /help  ✿ المساعدة
┃
┃  ━━━━━━━━━━━━━━━━━━━━
┃
┃  👨‍💻 *المطور:* `Y A C I N E   T X`
┃  ⌬ جميع الحقوق محفوظة ©
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
        await callback_query.message.edit_text(help_text, reply_markup=back_to_main_keyboard())
        await callback_query.answer()
    
    else:
        await callback_query.answer("⚠️ أمر غير معروف")

# ================== معالجة الرسائل النصية ==================
@app.on_message(filters.text & filters.private & ~filters.command)
async def handle_text(client, message):
    text = message.text.strip()
    if is_valid_channel_link(text):
        try:
            chat = await app.join_chat(text)
            title = chat.title or "بدون عنوان"
            channel_id = add_channel(text, title)
            if channel_id:
                await message.reply(f"✅ *تم إضافة القناة بنجاح!*\n📌 *العنوان:* `{title}`")
            else:
                await message.reply("⚠️ *القناة موجودة مسبقاً.*")
        except Exception as e:
            await message.reply(f"❌ *خطأ:* `{str(e)}`")
    else:
        await message.reply(
            "✿ ⌘ ⌬ ✪ *أرسل رابط قناة صحيح*\nأو استخدم الأوامر المتاحة.\n\n📌 `/help` لعرض المساعدة.",
            reply_markup=back_to_main_keyboard()
        )

# ================== تشغيل البوت ==================
if __name__ == "__main__":
    print("=" * 60)
    print("✿ ⌘ ⌬ ✪  بوت DARK HUNTER  ✪ ⌬ ⌘ ✿")
    print("👨‍💻 المطور: Y A C I N E   T X")
    print("⌬ الإصدار: v5.0.0")
    print("✪ يعمل الآن...")
    print("=" * 60)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("✿ تم إيقاف البوت.")
    except Exception as e:
        print(f"✿ خطأ: {e}")
