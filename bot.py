import requests
import json
import time
import re

BOT_TOKEN = "8422372449:AAGZxNXJzli5pQvCJeh_rygqhAhn9dtwoPM"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ===================================================================
#  إعدادات كلود
# ===================================================================
CLAUDE_CONFIG = {
    "org_id": "c64dbe54-2db1-4f65-a289-6b5bccf24347",
    "conv_id": "d7f45caa-a472-4923-a6c3-7a92079331d8",
    "parent_uuid": "019f57ab-9b68-725a-8403-9b7c80911955",
    "cookie": "sessionKeyLC=1783881524010; _cfuvid=_kAOrDYuOYgbAJysgEtOTvKKEUwM8ZroibQyialYWzE-1783881432.6374965-1.0.1.1-2hSW0zY.r3axCtLKKIo48XGICxDkLjftpSrrMe.EbQc; sessionKey=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; routingHint=sk-ant-rh-eyJ0eXAiOiAiSldUIiwgImFsZyI6ICJFUzI1NiIsICJraWQiOiAiN0MxcWFPRnhqdWxaUjRFQnNuNk1UeUZGNWdDV2JHbFpNVDR2RklrRFFpbyJ9.eyJzdWIiOiAiMzczYmQ1NGYtZDE1Zi00YzI4LTliMDQtNjI4NGQxYmE0ZTM2IiwgImlhdCI6IDE3ODM4ODE1MjQsICJpc3MiOiAiY2xhdWRlLWFpLXJvdXRpbmciLCAib25ib2FyZGluZ19jb21wbGV0ZSI6IHRydWUsICJwaG9uZV92ZXJpZmllZCI6IGZhbHNlLCAiYWdlX3ZlcmlmaWVkIjogdHJ1ZSwgIm5hbWUiOiAiXHUwNjQ3XHUwNjQ3XHUwNjQ3In0.ymYA2L6xaU9pfSMGf7JZWePpCbBSYUPa97AAdZHLBY-2d_EwEHVzM14ixFesalrISA1UGx_yz5-Wi-OHrEbltA; __cf_bm=0h0DR111.MiEddRHBbXAsbwiqENkfkN3n6MsTQ60HVw-1783882486.667257-1.0.1.1-.9Frfa_MsAAVnGUAz4t6zJOOS5lYkwqGUaFA29CIKUA8FjQk_RDhVKxDapaoERpLNzgCbXmzvQlapaRdzGMbqyKWJEGh5qq0zSarEpd5A2nIG4LlSIWAvO6ffKmbgLQX"
}

# ===================================================================
#  تنقية النص من HTML غير مدعوم
# ===================================================================
def clean_html(text):
    text = re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<html[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</html>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<head[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</head>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<body[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</body>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# ===================================================================
#  دوال كلود
# ===================================================================
def send_to_claude(prompt, conv_id, parent_uuid):
    url = f"https://claude.ai/api/organizations/{CLAUDE_CONFIG['org_id']}/chat_conversations/{conv_id}/completion"
    
    headers = {
        "Host": "claude.ai",
        "Accept": "text/event-stream",
        "User-Agent": "Claude com.anthropic.claude/1.260702.10 (Android 34)",
        "anthropic-client-platform": "android",
        "anthropic-client-app": "com.anthropic.claude",
        "anthropic-client-version": "1.260702.10",
        "anthropic-client-os-version": "34",
        "accept-language": "ar-DZ, fr-FR;q=0.9",
        "Cookie": CLAUDE_CONFIG["cookie"],
        "Content-Type": "application/json; charset=UTF8",
        "Accept-Encoding": "identity",
        "Priority": "u=1, i"
    }
    
    payload = {
        "prompt": prompt,
        "timezone": "Africa/Algiers",
        "model": "claude-sonnet-5",
        "attachments": [],
        "files": [],
        "rendering_mode": "messages",
        "input_mode": "text",
        "tools": [
            {"name": "repl", "type": "repl_v0"},
            {"name": "web_search", "type": "web_search_v0"},
            {"name": "user_time_v0", "title": "Check current time", "description": "Retrieves current time", "input_schema": {"type": "object", "properties": {}, "required": []}},
        ],
        "parent_message_uuid": parent_uuid,
        "effort": "medium",
        "thinking_mode": "auto"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=90)
        
        if response.status_code == 200:
            full_response = ""
            new_parent_uuid = parent_uuid
            
            for line in response.iter_lines():
                if line:
                    try:
                        decoded = line.decode('utf-8', errors='ignore')
                        
                        if 'message_start' in decoded:
                            try:
                                json_str = decoded[6:].strip()
                                if json_str:
                                    json_data = json.loads(json_str)
                                    if 'message' in json_data:
                                        new_parent_uuid = json_data['message'].get('uuid', parent_uuid)
                            except:
                                pass
                        
                        if decoded.startswith('data: '):
                            try:
                                json_str = decoded[6:].strip()
                                if json_str and json_str != '[DONE]':
                                    json_data = json.loads(json_str)
                                    if json_data.get('type') == 'content_block_delta':
                                        delta = json_data.get('delta', {})
                                        if delta.get('type') == 'text_delta':
                                            full_response += delta.get('text', '')
                            except:
                                pass
                    except:
                        pass
            
            full_response = clean_html(full_response)
            return full_response, new_parent_uuid
        else:
            return None, parent_uuid
    except Exception as e:
        print(f"❌ خطأ كلود: {str(e)}")
        return None, parent_uuid

# ===================================================================
#  إرسال رسالة مع اقتباس وتغليض HTML
# ===================================================================
def send_message(chat_id, text, buttons=None, parse_mode="HTML"):
    if '<!DOCTYPE' in text or '<html' in text.lower():
        parse_mode = None
    
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    if buttons:
        payload["reply_markup"] = json.dumps(buttons)
    
    try:
        response = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=30)
        result = response.json()
        if not result.get("ok"):
            if parse_mode:
                payload.pop("parse_mode", None)
                response = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=30)
                return response.json()
        return result
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return None

# ===================================================================
#  🔥 زر DEV واحد أحمر (danger)
# ===================================================================
def get_buttons():
    return {
        "inline_keyboard": [
            [
                {"text": "𝗬𝗔𝗖𝗜𝗡𝗘 𝗗𝗭", "callback_data": "dev", "style": "danger"}
            ]
        ]
    }

# ===================================================================
#  اختبار التوكن
# ===================================================================
def test_bot():
    try:
        response = requests.get(f"{TELEGRAM_API}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print(f"✅ البوت شغال: @{data['result']['username']}")
                return True
        return False
    except:
        return False

def clear_webhook():
    try:
        requests.get(f"{TELEGRAM_API}/deleteWebhook", timeout=10)
        print("✅ تم حذف الـ Webhook")
        return True
    except:
        return False

# ===================================================================
#  المتغيرات والمعالجة
# ===================================================================
user_conversations = {}
user_histories = {}

def create_claude_conversation():
    return CLAUDE_CONFIG["conv_id"], CLAUDE_CONFIG["parent_uuid"]

# ===================================================================
#  🔥 رد عند الضغط على زر DEV
# ===================================================================
def handle_callback(chat_id, callback_id, data, user_id):
    requests.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json={"callback_query_id": callback_id},
        timeout=10
    )
    
    if data == "dev":
        send_message(
            chat_id,
            """<blockquote>
<u><b>🔥 YACINE_X6 DEV</b></u>

<u><b>👑 أنت الأسطورة يا سيدي ياسين ديف</b></u>
<u><b>💀 البوت تحت أمرك</b></u>
<u><b>⚡ القوة لك وحدك</b></u>

✿ ⌘ ⌬ ✪
</blockquote>""",
            get_buttons()
        )

# ===================================================================
#  التشغيل الرئيسي
# ===================================================================
def main():
    print("="*60)
    print("✦ DARK HUNTER X CLAUDE ✦")
    print("⌘ بواسطة: YACINE DEV ⚡")
    print("🔥 زر DEV أحمر + اقتباس + تغليض")
    print("="*60)
    
    if not test_bot():
        return
    
    clear_webhook()
    
    print("🔥 جاري الاستماع للرسائل...")
    print("📌 اضغط Ctrl+C للإيقاف")
    print("="*60)
    
    last_id = 0
    
    while True:
        try:
            params = {
                "offset": last_id + 1,
                "timeout": 30,
                "allowed_updates": ["message", "callback_query"]
            }
            
            response = requests.get(
                f"{TELEGRAM_API}/getUpdates",
                params=params,
                timeout=35
            )
            
            if response.status_code != 200:
                print(f"⚠️ خطأ: {response.status_code}")
                time.sleep(5)
                continue
            
            updates = response.json()
            
            if not updates.get("ok"):
                print(f"⚠️ خطأ: {updates}")
                time.sleep(5)
                continue
            
            for update in updates.get("result", []):
                last_id = update.get("update_id", 0)
                
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    user_id = msg["from"]["id"]
                    text = msg.get("text", "")
                    username = msg["from"].get("username", "مجهول")
                    
                    print(f"📩 رسالة من @{username}: {text[:50]}")
                    
                    if str(user_id) not in user_conversations:
                        conv_id, parent_uuid = create_claude_conversation()
                        user_conversations[str(user_id)] = {
                            "conv_id": conv_id,
                            "parent_uuid": parent_uuid
                        }
                        user_histories[str(user_id)] = []
                    
                    if text == "/start":
                        send_message(
                            chat_id,
                            """<blockquote>
<u><b>مـــــرحبـــــا بـــــك</b></u>  
<u><b>إنـــــي كـــــلـــــود أســـــاعـــــدك فـــــي أي شـــــيء</b></u>  

<u><b>قـــــوتـــــي لا حـــــدود لـــــهـــــا</b></u>  
<u><b>صـــــنـــــع بـــــأمـــــر ياسين ديف</b></u>  

<u><b>اســـــألـــــنـــــي أي شـــــيء</b></u>  

━━━━━━━━━━━━━━━━━━━━━━━━━━
<u><b>الـــــأوامـــــر:</b></u>

<u>/start</u>  <b>بـــــدء الـــــبـــــوت</b>
<u>/help</u>   <b>الـــــمـــــســـــاعـــــدة</b>
<u>/new</u>    <b>مـــــحـــــادثـــــة جـــــديـــــدة</b>
<u>/stats</u>  <b>الـــــإحـــــصـــــائـــــيـــــات</b>
<u>/dev</u>    <b>مـــــعـــــلـــــومـــــات الـــــمـــــطـــــور</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>اســـــألـــــنـــــي أي شـــــيء</b>
</blockquote>""",
                            get_buttons()
                        )
                    
                    elif text == "/help":
                        send_message(
                            chat_id,
                            """<blockquote>
<u><b>المساعدة</b></u>

<u>/start</u> - <b>بدء البوت</b>
<u>/help</u> - <b>هذه الرسالة</b>
<u>/new</u> - <b>محادثة جديدة</b>
<u>/stats</u> - <b>الإحصائيات</b>
<u>/dev</u> - <b>معلومات المطور</b>
</blockquote>""",
                            get_buttons()
                        )
                    
                    elif text == "/new":
                        conv_id, parent_uuid = create_claude_conversation()
                        user_conversations[str(user_id)] = {
                            "conv_id": conv_id,
                            "parent_uuid": parent_uuid
                        }
                        user_histories[str(user_id)] = []
                        send_message(
                            chat_id,
                            """<blockquote>
✅ <u><b>تم بدء محادثة جديدة</b></u>
</blockquote>""",
                            get_buttons()
                        )
                    
                    elif text == "/stats":
                        history = user_histories.get(str(user_id), [])
                        send_message(
                            chat_id,
                            f"""<blockquote>
<u><b>الإحصائيات</b></u>

📊 <b>عدد الرسائل:</b> <u>{len(history)}</u>
📅 <b>اليوم:</b> <u>{time.strftime("%Y-%m-%d")}</u>
</blockquote>""",
                            get_buttons()
                        )
                    
                    elif text == "/dev":
                        send_message(
                            chat_id,
                            """<blockquote>
<u><b>🔥 YACINE_X6 DEV</b></u>

<u><b> 𝗬𝗔𝗖𝗜𝗡𝗘 𝗗𝗭</b></u>
<u><b>💀 ياسين عمك ديرها مليح في راسك </b></u>
</blockquote>""",
                            get_buttons()
                        )
                    
                    else:
                        conv = user_conversations[str(user_id)]
                        
                        requests.post(
                            f"{TELEGRAM_API}/sendChatAction",
                            json={"chat_id": chat_id, "action": "typing"},
                            timeout=10
                        )
                        
                        response, new_uuid = send_to_claude(
                            text,
                            conv["conv_id"],
                            conv["parent_uuid"]
                        )
                        
                        if response:
                            conv["parent_uuid"] = new_uuid
                            user_conversations[str(user_id)] = conv
                            
                            history = user_histories.get(str(user_id), [])
                            history.append({"user": text, "assistant": response[:200]})
                            user_histories[str(user_id)] = history[-10:]
                            
                            send_message(
                                chat_id,
                                f"""🤖 <b>كلود:</b>

{response}""",
                                get_buttons()
                            )
                        else:
                            send_message(
                                chat_id,
                                """❌ <b>فشل الاتصال بكلود</b>
✿ حاول مرة أخرى""",
                                get_buttons()
                            )
                
                elif "callback_query" in update:
                    cb = update["callback_query"]
                    chat_id = cb["message"]["chat"]["id"]
                    cb_id = cb["id"]
                    data = cb["data"]
                    user_id = cb["from"]["id"]
                    
                    print(f"🔄 كولباك: {data}")
                    handle_callback(chat_id, cb_id, data, user_id)
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n👋 تم الإيقاف")
            break
        except Exception as e:
            print(f"❌ خطأ: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 تم الإيقاف")
