#!/usr/bin/env python3
# ============================================
# TikSpark Bot v7.0 — Mo.dark Redesign
# UESM Protocol — Design Match from Image
# ============================================

import logging
import requests
import random
import time
import re
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
            return 0
        except:
            return 0

    def run_cycle(self, max_orders=3):
        if self.running:
            return {"status": "already_running", "score": self.total_score}

        self.running = True
        self.success_count = 0
        self.fail_count = 0

        try:
            start_score = self.fetch_score()
            all_orders = []
            for page in range(1, 4):
                orders = self.fetch_orders(page)
                if orders:
                    all_orders.extend(orders)
                time.sleep(0.2)

            if not all_orders:
                self.running = False
                return {"status": "no_orders", "score": start_score}

            selected = random.sample(
                all_orders, min(max_orders, len(all_orders))
            )
            gained = 0

            for order in selected:
                score = self.action_order(order['_id'])
                gained += score
                time.sleep(0.3)

            end_score = self.fetch_score()
            self.running = False
            return {
                "status": "success",
                "start_score": start_score,
                "end_score": end_score,
                "gained": gained,
                "processed": len(selected),
                "success_count": self.success_count,
                "fail_count": self.fail_count
            }
        except Exception as e:
            self.running = False
            return {"status": "error", "error": str(e)}


# ====== نسخة التصميم من الصورة ======
bot_instance = TikSparkBot(TOKEN_TIKSPARK)


def format_start_message(username):
    """تنسيق رسالة /start مطابقة للصورة"""
    return (
        f"[+] مـرحـبـا بــك يــا « @{username} »\n"
        f"\n"
        f"<u>بوت جلب النقاط من TikSpark</u>\n"
        f"\n"
        f"{{•}} الأوامر:\n"
        f"<u>/start</u> → عرض هذه الرسالة\n"
        f"<u>/points</u> → جلب نقاطك\n"
        f"<u>/collect 1000</u> → جلب 1000 نقطة\n"
        f"<u>/collect 2000</u> → جلب 2000 نقطة\n"
        f"<u>/status</u> → حالة البوت\n"
        f"\n"
        f"Dev by: @yacine_X6 🕸"
    )


def format_collect_success(result):
    """تنسيق رسالة جمع النقاط الناجح"""
    return (
        f"[+] تـم جـلـب الـنـقـاط\n"
        f"\n"
        f"<u>النقاط السابقة:</u> {result['start_score']}\n"
        f"<u>النقاط الحالية:</u> {result['end_score']}\n"
        f"<u>الزيادة:</u> +{result['gained']} نقطة\n"
        f"<u>تم معالجة:</u> {result['processed']} طلب\n"
        f"<u>نجاح:</u> {result['success_count']}\n"
        f"<u>فشل:</u> {result['fail_count']}\n"
        f"\n"
        f"Dev by: @yacine_X6 🕸"
    )


def format_points(score):
    """تنسيق رسالة النقاط"""
    return (
        f"[+] نـقـاطـك الـحـالـيـة\n"
        f"\n"
        f"<u>النقاط:</u> {score}\n"
        f"\n"
        f"Dev by: @yacine_X6 🕸"
    )


def format_status(score):
    """تنسيق رسالة الحالة"""
    status = "يعمل" if bot_instance.running else "متوقف"
    return (
        f"[+] حـالـة الـبـوت\n"
        f"\n"
        f"<u>الحالة:</u> {status}\n"
        f"<u>النقاط:</u> {score}\n"
        f"<u>نجاح:</u> {bot_instance.success_count}\n"
        f"<u>فشل:</u> {bot_instance.fail_count}\n"
        f"\n"
        f"Dev by: @yacine_X6 🕸"
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
        await msg.edit_text(
            "[+] خـطـأ\n\nفشل جلب النقاط\n\nDev by: @yacine_X6 🕸",
            parse_mode="HTML"
        )


async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "[+] هـذا الأمـر للـمـطـور فـقـط\n\nDev by: @yacine_X6 🕸",
            parse_mode="HTML"
        )
        return

    if bot_instance.running:
        await update.message.reply_text(
            "[+] الـبـوت يـعـمل حـالـيـاً\n\nDev by: @yacine_X6 🕸",
            parse_mode="HTML"
        )
        return

    # استخراج العدد
    try:
        parts = update.message.text.split()
        if len(parts) > 1:
            max_orders = int(parts[1]) // 100
            if max_orders < 1:
                max_orders = 1
            if max_orders > 20:
                max_orders = 20
        else:
            max_orders = 3
    except:
        max_orders = 3

    msg = await update.message.reply_text("⏳ جاري جلب النقاط...")

    result = bot_instance.run_cycle(max_orders=max_orders)

    if result["status"] == "success":
        text = format_collect_success(result)
    elif result["status"] == "no_orders":
        text = (
            f"[+] لا تـوجـد طـلـبـات\n\n"
            f"نقاطك الحالية: {result['score']}\n\n"
            f"Dev by: @yacine_X6 🕸"
        )
    elif result["status"] == "already_running":
        text = (
            f"[+] الـبـوت يـعـمل\n\n"
            f"انتظر حتى ينتهي\n\n"
            f"Dev by: @yacine_X6 🕸"
        )
    else:
        text = (
            f"[+] خـطـأ\n\n"
            f"{result.get('error', 'غير معروف')}\n\n"
            f"Dev by: @yacine_X6 🕸"
        )

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

    print("🕸 TikSpark Bot Started")
    print("👑 Dev: @yacine_X6")
    app.run_polling()


if __name__ == "__main__":
    main()
