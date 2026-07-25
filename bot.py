#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import json
import logging
import requests
import threading
from datetime import datetime
from typing import Dict, Optional, List

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("❌ يرجى تثبيت: pip install python-telegram-bot")
    sys.exit(1)

# ========== إعدادات ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== التوكن مدمج في الكود ==========
TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"  # 👈 ضع توكنك هنا

ADMIN_IDS = []  # ضع معرفات المشرفين هنا

# ========== إعدادات Instagram ==========
INSTAGRAM_URL = 'https://www.instagram.com/api/v1/web/accounts/login/ajax/'

INSTAGRAM_HEADERS = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.instagram.com',
    'referer': 'https://www.instagram.com/accounts/login/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 12; M2102J20SG) AppleWebKit/537.36 Chrome/112.0.0.0 Mobile Safari/537.36',
    'x-csrftoken': 'Cq2Bu3f9ZmKpE7wslVty91QptYjPegpQ',
    'x-ig-app-id': '1217981644879628',
    'x-requested-with': 'XMLHttpRequest'
}

# ========== دوال Instagram ==========
def generate_username() -> str:
    prefix = random.choice(['+91', '+92', '+971', '+966', '+1', '+44'])
    number = ''.join(random.choice('0123456789') for _ in range(10))
    return f"{prefix}{number}"

def generate_password() -> str:
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(random.randint(8, 12)))

def create_instagram_account():
    username = generate_username()
    password = generate_password()
    
    data = {
        'username': username,
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}'
    }
    
    try:
        response = requests.post(INSTAGRAM_URL, headers=INSTAGRAM_HEADERS, data=data, timeout=30)
        result = response.json()
        
        if result.get('userId'):
            return {'success': True, 'username': username, 'password': password, 'user_id': result['userId']}
        else:
            return {'success': False, 'username': username, 'password': password, 'error': result.get('message', 'Unknown error')}
    except Exception as e:
        return {'success': False, 'username': username, 'password': password, 'error': str(e)}

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح لك.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🚀 بدء التوليد", callback_data="start_gen")],
        [InlineKeyboardButton("⏹️ إيقاف", callback_data="stop_gen")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📋 النتائج", callback_data="results")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 **InstaBot**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 بوت إنشاء حسابات Instagram\n\n"
        "🔹 استخدم الأزرار للتحكم:",
        reply_markup=reply_markup
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ غير مصرح لك.")
        return
    
    action = query.data
    
    if action == "start_gen":
        await start_generation(update, context)
    elif action == "stop_gen":
        await stop_generation(update, context)
    elif action == "stats":
        await show_stats(update, context)
    elif action == "results":
        await show_results(update, context)

async def start_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if context.user_data.get('is_running', False):
        await query.edit_message_text("⚠️ التوليد قيد التشغيل بالفعل!")
        return
    
    keyboard = [
        [InlineKeyboardButton("10", callback_data="gen_10")],
        [InlineKeyboardButton("50", callback_data="gen_50")],
        [InlineKeyboardButton("100", callback_data="gen_100")],
        [InlineKeyboardButton("500", callback_data="gen_500")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📌 **اختر عدد الحسابات:**",
        reply_markup=reply_markup
    )

async def handle_gen_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    count = int(query.data.split('_')[1])
    context.user_data['is_running'] = True
    context.user_data['results'] = []
    
    await query.edit_message_text(
        f"🚀 **بدء التوليد...**\n"
        f"📊 العدد: {count}\n"
        f"⏳ جاري العمل..."
    )
    
    threading.Thread(target=run_generation, args=(update, context, count), daemon=True).start()

def run_generation(update, context, count):
    results = []
    done = 0
    errors = 0
    
    for i in range(count):
        if not context.user_data.get('is_running', False):
            break
        
        result = create_instagram_account()
        
        if result['success']:
            done += 1
            results.append(result)
            send_account(update, context, result)
        else:
            errors += 1
        
        time.sleep(random.uniform(0.5, 1.5))
        
        if (i + 1) % 10 == 0:
            update_progress(update, context, i + 1, count, done, errors)
    
    context.user_data['is_running'] = False
    context.user_data['results'] = results
    
    send_final_report(update, context, done, errors, count)

def send_account(update, context, result):
    try:
        message = (
            "✅ **حساب جديد**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 `{result['username']}`\n"
            f"🔑 `{result['password']}`\n"
            f"🆔 {result.get('user_id', 'N/A')}"
        )
        
        asyncio.run_coroutine_threadsafe(
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode='Markdown'
            ),
            asyncio.get_event_loop()
        )
    except Exception as e:
        logger.error(f"خطأ في الإرسال: {e}")

def update_progress(update, context, current, total, done, errors):
    try:
        progress = int((current / total) * 100)
        message = (
            f"⏳ **جاري التوليد...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 {progress}% ({current}/{total})\n"
            f"✅ الناجحة: {done}\n"
            f"❌ الفاشلة: {errors}"
        )
        
        asyncio.run_coroutine_threadsafe(
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.callback_query.message.message_id,
                text=message
            ),
            asyncio.get_event_loop()
        )
    except Exception as e:
        logger.error(f"خطأ في التحديث: {e}")

def send_final_report(update, context, done, errors, total):
    try:
        success_rate = int((done/total)*100) if total > 0 else 0
        message = (
            "📊 **التقرير النهائي**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 المجموع: {total}\n"
            f"✅ الناجحة: {done}\n"
            f"❌ الفاشلة: {errors}\n"
            f"📈 نسبة النجاح: {success_rate}%\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ انتهى التوليد!"
        )
        
        asyncio.run_coroutine_threadsafe(
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.callback_query.message.message_id,
                text=message
            ),
            asyncio.get_event_loop()
        )
    except Exception as e:
        logger.error(f"خطأ في التقرير: {e}")

async def stop_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if not context.user_data.get('is_running', False):
        await query.edit_message_text("⚠️ لا يوجد توليد قيد التشغيل.")
        return
    
    context.user_data['is_running'] = False
    await query.edit_message_text("⏹️ **تم إيقاف التوليد.**")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    results = context.user_data.get('results', [])
    total = len(results)
    success = sum(1 for r in results if r.get('success', False))
    failed = total - success
    
    message = (
        "📊 **الإحصائيات**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 المجموع: {total}\n"
        f"✅ الناجحة: {success}\n"
        f"❌ الفاشلة: {failed}\n"
        f"📈 نسبة النجاح: {int((success/total)*100) if total > 0 else 0}%\n"
        f"⏳ قيد التشغيل: {'نعم' if context.user_data.get('is_running', False) else 'لا'}"
    )
    
    await query.edit_message_text(message)

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    results = context.user_data.get('results', [])
    if not results:
        await query.edit_message_text("❌ لا توجد نتائج محفوظة.")
        return
    
    success = [r for r in results if r.get('success', False)]
    if not success:
        await query.edit_message_text("❌ لا توجد حسابات ناجحة.")
        return
    
    text = "📋 **آخر الحسابات الناجحة**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for r in success[-10:]:
        text += f"👤 `{r['username']}` | 🔑 `{r['password']}`\n"
    
    await query.edit_message_text(text, parse_mode='Markdown')

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await start(update, context)

# ========== تشغيل البوت ==========
def main():
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ يرجى إدخال توكن البوت في المتغير TOKEN")
        print("📝 عدل السطر: TOKEN = 'YOUR_BOT_TOKEN_HERE'")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons, pattern="^(start_gen|stop_gen|stats|results)$"))
    app.add_handler(CallbackQueryHandler(handle_gen_count, pattern="^gen_\\d+$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    main()
