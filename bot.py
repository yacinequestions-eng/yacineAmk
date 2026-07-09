#!/usr/bin/env python3
# ============================================
# TikSpark Bot v7.1 — Fixed Logic + Advanced Format
# UESM Protocol — Loop Until Target Reached
# ============================================

import logging
import requests
import random
import time
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ====== الإعدادات ======
TOKEN = "8054736760:AAE7TlEcsO4R25LI9e2nAzUr8o9VEzqt84E"
ADMIN_ID = 6936293942

TOKEN_TIKSPARK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2YTRkMWZiOGMyY2ZkMjQxYTFlYmY4ODAiLCJyb2xlIjoiQVVUSCIsInRva2VuVmVyc2lvbiI6MSwiaWF0IjoxNzgzNDkzMDk1LCJleHAiOjE3ODQ3ODkwOTV9.h8_UIDCEIm9TECI_6zZ2qx5tJY2G-fvG1VXLrnUVqZM"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ====== كلاس البوت ======
class TikSparkBot:
    def __init__(self, token):
        self.base_url = "https://api.tikspark.xyz/graphql"
        self.token = token
        self.device_info = '{"d":"62633330356361393666343862636466","n":"4954454c206974656c20413637314c43","o":"14","t":"d","v":"2.2.0","s":"0,0"}'
        self.session = requests.Session()
        self.total_score = 0
        self.success_count = 0
        self.fail_count = 0
        self.running = False

    def generate_headers(self, operation_name, operation_id):
        timestamp = str(int(time.time() * 1000))
        nonce = ''.join(random.choices('0123456789abcdef', k=16))
        csrf = f"{timestamp}:{''.join(random.choices('0123456789abcdef', k=64))}"
        return {
            'User-Agent': "okhttp/4.12.0",
            'Accept': "multipart/mixed; deferSpec=20220824, application/json",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/json",
            'x-apollo-operation-id': operation_id,
            'x-apollo-operation-name': operation_name,
            'x-language': "ar",
            'x-app-name': "com.dev.vidspark",
            'token': self.token,
            'x-csrf-token': csrf,
            'x-device-info': self.device_info,
            'x-app-sig': ''.join(random.choices('0123456789abcdef', k=64)),
            'x-app-ts': timestamp,
            'x-app-nonce': nonce
        }

    def fetch_score(self):
        payload = {
            "operationName": "FetchScore",
            "variables": {},
            "query": "query FetchScore { fetchScore }"
        }
        headers = self.generate_headers(
            "FetchScore",
            "88d30eeca55c0538539ad8217dfefd52b2f47015200cdbb7cb6ea5a765381d69"
        )
        try:
            response = self.session.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('fetchScore', 0)
            return 0
        except:
            return 0

    def fetch_orders(self, page=1):
        payload = {
            "operationName": "FetchOrders",
            "variables": {"page": page},
            "query": "query FetchOrders($page: Int!) { getOrders(page: $page) { _id type videoLink tiktokerUsername avatar score priority } }"
        }
        headers = self.generate_headers(
            "FetchOrders",
            "c2ca4b87e63f30f2cca10e5867d17ea0f1712e96e716a60513f68758b2256185"
        )
        try:
            response = self.session.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                orders = data.get('data', {}).get('getOrders', [])
                return [o for o in orders if o.get('type') != 'followers']
            return []
        except:
            return []

    def action_order(self, order_id):
        attempts = random.randint(50, 100)
        initial_number = random.uniform(50000, 150000)
        time_spent = random.uniform(600000, 1800000)

        payload = {
            "operationName": "ActionOrder",
            "variables": {
                "orderId": order_id,
                "validationData": {
                    "attempts": attempts,
                    "initialNumber": initial_number,
                    "timeSpent": time_spent
                }
            },
            "query": """
            mutation ActionOrder($orderId: ID!, $validationData: ValidationDataInput!) {
                actionOrder(orderId: $orderId, validationData: $validationData) {
                    score
                    taskProgress {
                        count
                        startTime
                        taskProgressLimit
                    }
                }
            }
            """
        }
        headers = self.generate_headers(
            "ActionOrder",
            "ddfbb49865193fd38840a34b92139f1759a71331e374bb1254f8e2352630e8f2"
        )

        try:
            response = self.session.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                action_data = data.get('data', {}).get('actionOrder')
                if action_data and isinstance(action_data, dict):
                    score = action_data.get('score', 0)
                    if score > 0:
                        self.success_count += 1
                        self.total_score += score
                        return score
            self.fail_count += 1
            return 0
        except:
            self.fail_count += 1
            return 0

    # ====== المنطق الجديد: معالجة حتى الوصول للهدف ======
    def run_until_target(self, target_score=1000, max_cycles=50):
        """
        يعالج طلبات متكررة حتى:
        - الوصول للهدف المطلوب (target_score)
        - أو نفاد الطلبات المتاحة
        - أو الوصول لعدد الدورات الأقصى
        """
        if self.running:
            return {"status": "already_running", "score": self.total_score}

        self.running = True
        self.success_count = 0
        self.fail_count = 0
        self.total_score = 0

        try:
            start_score = self.fetch_score()
            current_score = start_score
            total_gained = 0
            total_processed = 0
            cycles = 0

            while total_gained < target_score and cycles < max_cycles:
                cycles += 1

                # جلب الطلبات من جميع الصفحات
                all_orders = []
                for page in range(1, 4):
                    orders = self.fetch_orders(page)
                    if orders:
                        all_orders.extend(orders)
                    time.sleep(0.2)

                if not all_orders:
                    break  # لا توجد طلبات متاحة

                # معالجة كل الطلبات المتاحة
                for order in all_orders:
                    if total_gained >= target_score:
                        break

                    score = self.action_order(order['_id'])
                    total_gained += score
                    total_processed += 1

                    if score > 0:
                        current_score += score

                    time.sleep(0.3)

                # فترة راحة بين الدورات
                time.sleep(1)

            end_score = self.fetch_score()
            self.running = False

            return {
                "status": "success",
                "start_score": start_score,
                "end_score": end_score,
                "target": target_score,
                "gained": total_gained,
                "processed": total_processed,
                "cycles": cycles,
                "success_count": self.success_count,
                "fail_count": self.fail_count,
                "reached_target": total_gained >= target_score
            }

        except Exception as e:
            self.running = False
            return {"status": "error", "error": str(e)}


# ====== نسخة التصميم المتقدم ======
bot_instance = TikSparkBot(TOKEN_TIKSPARK)


def format_start_message(username):
    """تنسيق رسالة /start"""
    return (
        f"<b>[+] مـرحـبـا بــك يــا « @{username} »</b>\n"
        f"\n"
        f"<u><b>بوت جلب النقاط من TikSpark</b></u>\n"
        f"\n"
        f"<b>{{•}} الأوامر:</b>\n"
        f"<u><b>/start</b></u> → عرض هذه الرسالة\n"
        f"<u><b>/points</b></u> → جلب نقاطك\n"
        f"<u><b>/collect 1000</b></u> → جلب 1000 نقطة\n"
        f"<u><b>/collect 2000</b></u> → جلب 2000 نقطة\n"
        f"<u><b>/status</b></u> → حالة البوت\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


def format_collect_success(result):
    """تنسيق رسالة جمع النقاط الناجح — مطابق للصورة"""
    target_status = "✅ تم الوصول" if result['reached_target'] else "⚠️ لم يكتمل"
    
    return (
        f"<b>[+] تـم جـلـب الـنـقـاط</b>\n"
        f"\n"
        f"<u><b>النقاط السابقة:</b></u> <b>{result['start_score']}</b>\n"
        f"<u><b>النقاط الحالية:</b></u> <b>{result['end_score']}</b>\n"
        f"<u><b>الزيادة:</b></u> <b>+{result['gained']}</b> نقطة\n"
        f"<u><b>الهدف:</b></u> <b>{result['target']}</b> نقطة\n"
        f"<u><b>الحالة:</b></u> <b>{target_status}</b>\n"
        f"<u><b>تم معالجة:</b></u> <b>{result['processed']}</b> طلب\n"
        f"<u><b>دورات:</b></u> <b>{result['cycles']}</b>\n"
        f"<u><b>نجاح:</b></u> <b>{result['success_count']}</b>\n"
        f"<u><b>فشل:</b></u> <b>{result['fail_count']}</b>\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


def format_points(score):
    """تنسيق رسالة النقاط"""
    return (
        f"<b>[+] نـقـاطـك الـحـالـيـة</b>\n"
        f"\n"
        f"<u><b>النقاط:</b></u> <b>{score}</b>\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


def format_status(score):
    """تنسيق رسالة الحالة"""
    status = "🟢 يعمل" if bot_instance.running else "🔴 متوقف"
    return (
        f"<b>[+] حـالـة الـبـوت</b>\n"
        f"\n"
        f"<u><b>الحالة:</b></u> <b>{status}</b>\n"
        f"<u><b>النقاط:</b></u> <b>{score}</b>\n"
        f"<u><b>نجاح:</b></u> <b>{bot_instance.success_count}</b>\n"
        f"<u><b>فشل:</b></u> <b>{bot_instance.fail_count}</b>\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


def format_no_orders(score):
    """تنسيق: لا توجد طلبات"""
    return (
        f"<b>[+] لا تـوجـد طـلـبـات</b>\n"
        f"\n"
        f"<u><b>نقاطك الحالية:</b></u> <b>{score}</b>\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


def format_error(error_msg):
    """تنسيق: خطأ"""
    return (
        f"<b>[+] خـطـأ</b>\n"
        f"\n"
        f"<u><b>التفاصيل:</b></u> <b>{error_msg}</b>\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


def format_already_running():
    """تنسيق: البوت يعمل"""
    return (
        f"<b>[+] الـبـوت يـعـمل</b>\n"
        f"\n"
        f"<u><b>الحالة:</b></u> <b>يعمل حالياً، انتظر حتى ينتهي</b>\n"
        f"\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
    )


# ====== handlers تليجرام ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or user.first_name or "مستخدم"
    text = format_start_message(username)
    await update.message.reply_text(text, parse_mode="HTML")


async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ جاري جلب النقاط...")
    score = bot_instance.fetch_score()
    if score is not None:
        text = format_points(score)
        await msg.edit_text(text, parse_mode="HTML")
    else:
        text = format_error("فشل جلب النقاط")
        await msg.edit_text(text, parse_mode="HTML")


async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        text = (
            f"<b>[+] هـذا الأمـر للـمـطـور فـقـط</b>\n"
            f"\n"
            f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    if bot_instance.running:
        text = format_already_running()
        await update.message.reply_text(text, parse_mode="HTML")
        return

    # استخراج الهدف
    try:
        parts = update.message.text.split()
        if len(parts) > 1:
            target = int(parts[1])
            if target < 100:
                target = 100
            if target > 10000:
                target = 10000
        else:
            target = 1000
    except:
        target = 1000

    msg = await update.message.reply_text(
        f"<b>[+] جـاري الـعـمـل</b>\n\n"
        f"<u><b>الهدف:</b></u> <b>{target}</b> نقطة\n"
        f"<u><b>الحالة:</b></u> <b>جاري المعالجة...</b>\n\n"
        f"<blockquote>Dev by: @yacine_X6 🕸</blockquote>",
        parse_mode="HTML"
    )

    # المنطق الجديد: معالجة حتى الوصول للهدف
    result = bot_instance.run_until_target(target_score=target, max_cycles=50)

    if result["status"] == "success":
        text = format_collect_success(result)
    elif result["status"] == "no_orders":
        text = format_no_orders(result.get('score', 0))
    elif result["status"] == "already_running":
        text = format_already_running()
    else:
        text = format_error(result.get('error', 'غير معروف'))

    await msg.edit_text(text, parse_mode="HTML")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = bot_instance.fetch_score()
    text = format_status(score)
    await update.message.reply_text(text, parse_mode="HTML")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("points", points))
    app.add_handler(CommandHandler("collect", collect))
    app.add_handler(CommandHandler("status", status_cmd))

    print("🕸 TikSpark Bot v7.1 Started")
    print("👑 Dev: @yacine_X6")
    app.run_polling()


if __name__ == "__main__":
    main()
