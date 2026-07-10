#!/usr/bin/env python3
# ============================================
# GARENA MANAGER BOT v9.0
# Developer : @yacine_X6
# Channel   : @UESM_Team
# ============================================

import logging
import os
import sys
import json
import time
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import requests
import urllib3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, ContextTypes, filters

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8422372449:AAGZxNXJzli5pQvCJeh_rygqhAhn9dtwoPM"
ADMIN_ID = 6936293942

GA_HEADERS = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
GA_BASE = "https://100067.connect.garena.com"
GA_APPID = "100067"

PLATFORMS = {1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter/Line", 11: "X", 13: "Apple ID", 28: "Line", 35: "TikTok"}

STATE_MENU, STATE_BIND_EMAIL, STATE_BIND_OTP, STATE_BIND_SEC, STATE_UNBIND_CHOICE, STATE_UNBIND_OTP, STATE_UNBIND_SEC, STATE_CHANGE_CHOICE, STATE_CHANGE_OLD_OTP, STATE_CHANGE_OLD_SEC, STATE_CHANGE_NEW_EMAIL, STATE_CHANGE_NEW_OTP, STATE_REVOKE_CONFIRM = range(13)

_user_sessions: Dict[int, Dict[str, Any]] = {}
_operation_log: List[Dict[str, Any]] = []

def _sec_to_str(s: int) -> str:
    d, s = divmod(s, 86400); h, s = divmod(s, 3600); m, s = divmod(s, 60)
    return " ".join([f"{d}d" for _ in [1] if d] + [f"{h}h" for _ in [1] if h] + [f"{m}m" for _ in [1] if m] + [f"{s}s" for _ in [1] if s]) or "0s"

def _log_op(uid: int, action: str, status: str, details: str = ""):
    _operation_log.append({"timestamp": datetime.now().isoformat(), "user_id": uid, "action": action, "status": status, "details": details})
    if len(_operation_log) > 1000: _operation_log.pop(0)

class GarenaAPI:
    def __init__(self): self.session = requests.Session(); self.session.headers.update(GA_HEADERS)
    def _g(self, e: str, p: dict) -> requests.Response: return self.session.get(f"{GA_BASE}{e}", params=p, timeout=15, verify=False)
    def _p(self, e: str, d: dict) -> requests.Response: return self.session.post(f"{GA_BASE}{e}", data=d, timeout=15, verify=False)
    def player(self, t: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            r = requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={t}", headers={"User-Agent": GA_HEADERS["User-Agent"]}, allow_redirects=True, timeout=15)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
            return q.get("account_id", ["Unknown"])[0], q.get("nickname", ["Unknown"])[0], q.get("region", ["Unknown"])[0]
        except: return None, None, None
    def bind_info(self, t: str) -> Optional[dict]:
        try: r = self._g("/game/account_security/bind:get_bind_info", {"xMaSrY": GA_APPID, "access_token": t}); return r.json() if r.status_code == 200 else None
        except: return None
    def send_otp(self, e: str, t: str) -> requests.Response:
        return self._p("/game/account_security/bind:send_otp", {"email": e, "locale": "en_PK", "region": "PK", "xMaSrY": GA_APPID, "access_token": t})
    def verify_otp(self, e: str, o: str, t: str) -> Optional[str]:
        try:
            r = self._p("/game/account_security/bind:verify_otp", {"email": e, "xMaSrY": GA_APPID, "access_token": t, "code": o, "otp": o, "type": "1"})
            return r.json().get("verifier_token")
        except: return None
    def verify_identity(self, e: str, t: str, o: str = None, s: str = None) -> Optional[str]:
        try:
            d = {"email": e, "xMaSrY": GA_APPID, "access_token": t}
            if o: d["otp"] = o
            elif s: d["secondary_password"] = hashlib.sha256(s.encode()).hexdigest()
            r = self._p("/game/account_security/bind:verify_identity", d); return r.json().get("identity_token")
        except: return None
    def create_bind(self, e: str, t: str, v: str, s: str) -> requests.Response:
        return self._p("/game/account_security/bind:create_bind_request", {"email": e, "xMaSrY": GA_APPID, "access_token": t, "verifier_token": v, "secondary_password": s})
    def create_unbind(self, t: str, i: str) -> requests.Response:
        return self._p("/game/account_security/bind:create_unbind_request", {"xMaSrY": GA_APPID, "access_token": t, "identity_token": i})
    def create_rebind(self, i: str, e: str, t: str, v: str) -> requests.Response:
        return self._p("/game/account_security/bind:create_rebind_request", {"identity_token": i, "email": e, "xMaSrY": GA_APPID, "verifier_token": v, "access_token": t})
    def cancel(self, t: str) -> requests.Response:
        return self._p("/game/account_security/bind:cancel_request", {"xMaSrY": GA_APPID, "access_token": t})
    def revoke(self, t: str) -> requests.Response:
        return self.session.get(f"{GA_BASE}/oauth/logout?access_token={t}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8", headers=GA_HEADERS, timeout=15)
    def platforms(self, t: str) -> Optional[dict]:
        try: r = self._g("/bind/app/platform/info/get", {"access_token": t}); return r.json() if r.status_code == 200 else None
        except: return None

_gapi = GarenaAPI()

# ====== FORMAT FUNCTIONS ======

def _fmt_start(username: str) -> str:
    return (
        "<blockquote>"
        "<b>مـــــرحبا بــــك يــا @{}</b>\n\n"
        "<b>بــوت إدارة حــسابات Garena</b>\n\n"
        "<b>الأوامر المتاحة:</b>\n"
        "<b>/start</b> عرض الواجهة\n"
        "<b>/info</b> معلومات اللاعب\n"
        "<b>/bind</b> ربط بريد إلكتروني\n"
        "<b>/unbind</b> فك ربط البريد\n"
        "<b>/change</b> تغيير البريد\n"
        "<b>/cancel</b> إلغاء الطلب\n"
        "<b>/revoke</b> إلغاء التوكن\n"
        "<b>/platforms</b> المنصات المرتبطة\n"
        "<b>/status</b> حالة البوت\n\n"
        "<b>ديــفـلـوبـر: @yacine_X6</b>"
        "</blockquote>"
    ).format(username)

def _fmt_info(uid: str, nick: str, region: str, email: str, pending: str, cd: int) -> str:
    return (
        "<blockquote>"
        f"<b>مــعـلـومـات الـلاعـب</b>\n\n"
        f"<b>UID:</b> {uid}\n"
        f"<b>Nickname:</b> {nick}\n"
        f"<b>Region:</b> {region}\n"
        f"<b>Email:</b> {email or 'None'}\n"
        f"<b>Pending:</b> {pending or 'None'}\n"
        f"<b>Countdown:</b> {_sec_to_str(cd) if cd else 'N/A'}"
        "</blockquote>"
    )

def _fmt_platforms(bound: List[int], available: List[int]) -> str:
    b = ", ".join([PLATFORMS.get(p, f"Unknown({p})") for p in bound]) or "None"
    a = ", ".join([PLATFORMS.get(p, f"Unknown({p})") for p in available]) or "None"
    return (
        "<blockquote>"
        f"<b>الـمـنـصـات الـمـربـوطـة</b>\n\n"
        f"<b>Bound:</b> {b}\n"
        f"<b>Available:</b> {a}"
        "</blockquote>"
    )

def _fmt_status() -> str:
    return (
        "<blockquote>"
        f"<b>حــالة الـبـوت</b>\n\n"
        f"<b>Version:</b> 9.0\n"
        f"<b>Operations:</b> {len(_operation_log)}\n"
        f"<b>Active Sessions:</b> {len(_user_sessions)}\n"
        f"<b>Status:</b> Online"
        "</blockquote>"
    )

# ====== KEYBOARDS ======

def _kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Info", callback_data="cmd_info"), InlineKeyboardButton("Bind", callback_data="cmd_bind")],
        [InlineKeyboardButton("Unbind", callback_data="cmd_unbind"), InlineKeyboardButton("Change", callback_data="cmd_change")],
        [InlineKeyboardButton("Cancel", callback_data="cmd_cancel"), InlineKeyboardButton("Revoke", callback_data="cmd_revoke")],
        [InlineKeyboardButton("Platforms", callback_data="cmd_platforms"), InlineKeyboardButton("Status", callback_data="cmd_status")]
    ])

def _kb_confirm(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm", callback_data=f"confirm_{action}"), InlineKeyboardButton("Cancel", callback_data="cancel")]
    ])

def _kb_unbind() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("OTP", callback_data="unbind_otp"), InlineKeyboardButton("Security Code", callback_data="unbind_sec")],
        [InlineKeyboardButton("Back", callback_data="back")]
    ])

def _kb_change() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("OTP", callback_data="change_otp"), InlineKeyboardButton("Security Code", callback_data="change_sec")],
        [InlineKeyboardButton("Back", callback_data="back")]
    ])

# ====== COMMAND HANDLERS ======

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(_fmt_start(user.username or user.first_name or "User"), parse_mode="HTML", reply_markup=_kb_main())

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in _user_sessions or "token" not in _user_sessions[uid]:
        await update.message.reply_text("<blockquote><b>لـم يـتـم تـسـجـيـل الـدخـول</b>\n\n<b>اسـتـخـدم /bind أو أي أمـر آخـر لإدخـال الـتـوكـن</b></blockquote>", parse_mode="HTML")
        return
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري جـلـب الـمـعـلـومـات...</b></blockquote>", parse_mode="HTML")
    uid2, nick, region = _gapi.player(t)
    bd = _gapi.bind_info(t)
    if uid2 is None:
        await msg.edit_text("<blockquote><b>فـشـل الـتـصـديـق</b>\n\n<b>الـتـوكـن غـيـر صـالـح أو مـنـتـهي</b></blockquote>", parse_mode="HTML")
        _log_op(uid, "info", "failed", "invalid token")
        return
    e, p, c = (bd.get("email", "") if bd else ""), (bd.get("email_to_be", "") if bd else ""), (bd.get("request_exec_countdown", 0) if bd else 0)
    await msg.edit_text(_fmt_info(uid2, nick, region, e, p, c), parse_mode="HTML")
    _log_op(uid, "info", "success", f"uid={uid2}")

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>لا تـوجـد جـلـسـة نـشـطـة</b></blockquote>", parse_mode="HTML")
        return
    t = _user_sessions[uid].get("token", "")
    if not t:
        await update.message.reply_text("<blockquote><b>لا تـوجـد طـلـبـات</b></blockquote>", parse_mode="HTML")
        return
    msg = await update.message.reply_text("<blockquote><b>جـاري إلـغـاء الـطـلـب...</b></blockquote>", parse_mode="HTML")
    r = _gapi.cancel(t)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text("<blockquote><b>تـم إلـغـاء الـطـلـب</b>\n\n<b>الـحـالـة:</b> Success</blockquote>", parse_mode="HTML")
        _log_op(uid, "cancel", "success", "")
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل إلـغـاء الـطـلـب</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        _log_op(uid, "cancel", "failed", d.get("error", ""))

async def cmd_revoke_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in _user_sessions or "token" not in _user_sessions[uid]:
        await update.message.reply_text("<blockquote><b>لـم يـتـم تـسـجـيـل الـدخـول</b>\n\n<b>اسـتـخـدم /bind أو أي أمـر آخـر لإدخـال الـتـوكـن</b></blockquote>", parse_mode="HTML")
        return
    t = _user_sessions[uid]["token"]
    uid2, nick, region = _gapi.player(t)
    if uid2 is None:
        await update.message.reply_text("<blockquote><b>تـوكـن غـيـر صـالـح</b></blockquote>", parse_mode="HTML")
        return
    await update.message.reply_text(f"<blockquote><b>تـأكـيـد إلـغـاء الـتـوكـن</b>\n\n<b>UID:</b> {uid2}\n<b>Nick:</b> {nick}\n\n<b>هـل أنـت مـتـأكـد؟</b></blockquote>", parse_mode="HTML", reply_markup=_kb_confirm("revoke"))

async def cmd_revoke_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in _user_sessions:
        await q.edit_message_text("<blockquote><b>انـتـهـت الـجـلـسـة</b></blockquote>", parse_mode="HTML")
        return
    t = _user_sessions[uid].get("token", "")
    if q.data == "confirm_revoke":
        msg = await q.edit_message_text("<blockquote><b>جـاري إلـغـاء الـتـوكـن...</b></blockquote>", parse_mode="HTML")
        r = _gapi.revoke(t)
        if r.status_code == 200 and "error" not in r.text:
            await msg.edit_text("<blockquote><b>تـم إلـغـاء الـتـوكـن</b>\n\n<b>الـحـالـة:</b> Success</blockquote>", parse_mode="HTML")
            _log_op(uid, "revoke", "success", "")
            _user_sessions.pop(uid, None)
        else:
            await msg.edit_text(f"<blockquote><b>فـشـل إلـغـاء الـتـوكـن</b>\n\n<b>الـخطـأ:</b> {r.status_code}</blockquote>", parse_mode="HTML")
            _log_op(uid, "revoke", "failed", str(r.status_code))
    else:
        await q.edit_message_text("<blockquote><b>تـم الإلـغـاء</b></blockquote>", parse_mode="HTML")

async def cmd_platforms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in _user_sessions or "token" not in _user_sessions[uid]:
        await update.message.reply_text("<blockquote><b>لـم يـتـم تـسـجـيـل الـدخـول</b>\n\n<b>اسـتـخـدم /bind أو أي أمـر آخـر لإدخـال الـتـوكـن</b></blockquote>", parse_mode="HTML")
        return
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري جـلـب الـمـنـصـات...</b></blockquote>", parse_mode="HTML")
    d = _gapi.platforms(t)
    if d is None:
        await msg.edit_text("<blockquote><b>فـشـل جـلـب الـمـنـصـات</b></blockquote>", parse_mode="HTML")
        return
    await msg.edit_text(_fmt_platforms(d.get("bounded_accounts", []), d.get("available_platforms", [])), parse_mode="HTML")
    _log_op(uid, "platforms", "success", f"bound={len(d.get('bounded_accounts', []))}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(_fmt_status(), parse_mode="HTML")

# ====== BIND CONVERSATION ======

async def conv_bind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        await q.edit_message_text("<blockquote><b>ربــط بـريـد إلـكـتـرونـي</b>\n\n<b>أرسـل الـتـوكـن الـخـاص بـك:</b></blockquote>", parse_mode="HTML")
    else:
        await update.message.reply_text("<blockquote><b>ربــط بـريـد إلـكـتـرونـي</b>\n\n<b>أرسـل الـتـوكـن الـخـاص بـك:</b></blockquote>", parse_mode="HTML")
    return STATE_BIND_EMAIL

async def conv_bind_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    t = update.message.text.strip()
    uid2, nick, region = _gapi.player(t)
    if uid2 is None:
        await update.message.reply_text("<blockquote><b>تـوكـن غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid] = {"token": t, "uid": uid2, "nick": nick}
    await update.message.reply_text(f"<blockquote><b>تـم الـتـصـديـق</b>\n\n<b>UID:</b> {uid2}\n<b>Nick:</b> {nick}\n<b>Region:</b> {region}\n\n<b>أرسـل الـبـريـد الإلـكـتـرونـي للـربـط:</b></blockquote>", parse_mode="HTML")
    return STATE_BIND_OTP

async def conv_bind_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    e = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /bind</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid]["email"] = e
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري إرسـال OTP...</b></blockquote>", parse_mode="HTML")
    r = _gapi.send_otp(e, t)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text(f"<blockquote><b>تـم إرسـال OTP</b>\n\n<b>الـبـريـد:</b> {e}\n\n<b>أرسـل رقـم OTP:</b></blockquote>", parse_mode="HTML")
        return STATE_BIND_SEC
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل إرسـال OTP</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        return ConversationHandler.END

async def conv_bind_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    o = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /bind</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    e = _user_sessions[uid].get("email", "")
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري الـتـحـقـق مـن OTP...</b></blockquote>", parse_mode="HTML")
    v = _gapi.verify_otp(e, o, t)
    if not v:
        await msg.edit_text("<blockquote><b>OTP غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid]["verifier"] = v
    await msg.edit_text(f"<blockquote><b>تـم الـتـحـقـق مـن OTP</b>\n\n<b>الـبـريـد:</b> {e}\n\n<b>أدخـل كـود الأمـان (6 أرقـام):</b></blockquote>", parse_mode="HTML")
    return STATE_BIND_SEC

async def conv_bind_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    s = update.message.text.strip()
    if len(s) != 6 or not s.isdigit():
        await update.message.reply_text("<blockquote><b>كـود غـيـر صـالـح</b>\n\n<b>يـجـب أن يـكـون 6 أرقـام</b></blockquote>", parse_mode="HTML")
        return STATE_BIND_SEC
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /bind</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    e = _user_sessions[uid].get("email", "")
    t = _user_sessions[uid]["token"]
    v = _user_sessions[uid].get("verifier", "")
    msg = await update.message.reply_text("<blockquote><b>جـاري إنـشـاء طـلـب الـربـط...</b></blockquote>", parse_mode="HTML")
    r = _gapi.create_bind(e, t, v, s)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text(f"<blockquote><b>تـم ربـط الـبـريـد</b>\n\n<b>الـبـريـد:</b> {e}\n<b>الـحـالـة:</b> Success</blockquote>", parse_mode="HTML")
        _log_op(uid, "bind", "success", f"email={e}")
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل ربـط الـبـريـد</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        _log_op(uid, "bind", "failed", d.get("error", ""))
    return ConversationHandler.END

# ====== UNBIND CONVERSATION ======

async def conv_unbind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        await q.edit_message_text("<blockquote><b>فــك ربــط الـبـريـد</b>\n\n<b>اخـتـر طـريـقـة الـتـحـقـق:</b></blockquote>", parse_mode="HTML", reply_markup=_kb_unbind())
    else:
        await update.message.reply_text("<blockquote><b>فــك ربــط الـبـريـد</b>\n\n<b>أرسـل الـتـوكـن الـخـاص بـك:</b></blockquote>", parse_mode="HTML")
    return STATE_UNBIND_CHOICE

async def conv_unbind_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    t = update.message.text.strip()
    uid2, nick, region = _gapi.player(t)
    if uid2 is None:
        await update.message.reply_text("<blockquote><b>تـوكـن غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid] = {"token": t, "uid": uid2, "nick": nick}
    await update.message.reply_text(f"<blockquote><b>تـم الـتـصـديـق</b>\n\n<b>UID:</b> {uid2}\n<b>Nick:</b> {nick}\n\n<b>اخـتـر طـريـقـة الـتـحـقـق:</b></blockquote>", parse_mode="HTML", reply_markup=_kb_unbind())
    return STATE_UNBIND_OTP

async def conv_unbind_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in _user_sessions:
        await q.edit_message_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /unbind</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    choice = q.data
    t = _user_sessions[uid]["token"]
    bd = _gapi.bind_info(t)
    e = bd.get("email", "") if bd else ""
    if not e:
        await q.edit_message_text("<blockquote><b>لا يـوجـد بـريـد مـربـوط</b>\n\n<b>الـحـسـاب لـيـس لـديـه بـريـد إلـكـتـرونـي مـربـوط</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid]["email"] = e
    if choice == "unbind_otp":
        msg = await q.edit_message_text("<blockquote><b>جـاري إرسـال OTP...</b></blockquote>", parse_mode="HTML")
        r = _gapi.send_otp(e, t)
        d = r.json() if r.status_code == 200 else {}
        if d.get("result") == 0:
            await msg.edit_text(f"<blockquote><b>تـم إرسـال OTP</b>\n\n<b>الـبـريـد:</b> {e}\n\n<b>أرسـل رقـم OTP:</b></blockquote>", parse_mode="HTML")
            return STATE_UNBIND_OTP
        else:
            await msg.edit_text(f"<blockquote><b>فـشـل إرسـال OTP</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
            return ConversationHandler.END
    elif choice == "unbind_sec":
        await q.edit_message_text(f"<blockquote><b>أدخـل كـود الأمـان</b>\n\n<b>الـبـريـد:</b> {e}\n\n<b>أدخـل كـود الأمـان (6 أرقـام):</b></blockquote>", parse_mode="HTML")
        return STATE_UNBIND_SEC
    return ConversationHandler.END

async def conv_unbind_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    o = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /unbind</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    e = _user_sessions[uid].get("email", "")
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري الـتـحـقـق...</b></blockquote>", parse_mode="HTML")
    i = _gapi.verify_identity(e, t, otp=o)
    if not i:
        await msg.edit_text("<blockquote><b>OTP غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    await msg.edit_text("<blockquote><b>جـاري فـك الـربـط...</b></blockquote>", parse_mode="HTML")
    r = _gapi.create_unbind(t, i)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text(f"<blockquote><b>تـم فـك ربـط الـبـريـد</b>\n\n<b>الـبـريـد:</b> {e}\n<b>الـحـالـة:</b> Success</blockquote>", parse_mode="HTML")
        _log_op(uid, "unbind", "success", f"email={e}")
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل فـك ربـط الـبـريـد</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        _log_op(uid, "unbind", "failed", d.get("error", ""))
    return ConversationHandler.END

async def conv_unbind_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    s = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /unbind</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    e = _user_sessions[uid].get("email", "")
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري الـتـحـقـق...</b></blockquote>", parse_mode="HTML")
    i = _gapi.verify_identity(e, t, sec=s)
    if not i:
        await msg.edit_text("<blockquote><b>كـود الأمـان غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    await msg.edit_text("<blockquote><b>جـاري فـك الـربـط...</b></blockquote>", parse_mode="HTML")
    r = _gapi.create_unbind(t, i)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text(f"<blockquote><b>تـم فـك ربـط الـبـريـد</b>\n\n<b>الـبـريـد:</b> {e}\n<b>الـحـالـة:</b> Success</blockquote>", parse_mode="HTML")
        _log_op(uid, "unbind", "success", f"email={e}")
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل فـك ربـط الـبـريـد</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        _log_op(uid, "unbind", "failed", d.get("error", ""))
    return ConversationHandler.END

# ====== CHANGE CONVERSATION ======

async def conv_change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        await q.edit_message_text("<blockquote><b>تــغـيـيـر الـبـريـد</b>\n\n<b>أرسـل الـتـوكـن الـخـاص بـك:</b></blockquote>", parse_mode="HTML")
    else:
        await update.message.reply_text("<blockquote><b>تــغـيـيـر الـبـريـد</b>\n\n<b>أرسـل الـتـوكـن الـخـاص بـك:</b></blockquote>", parse_mode="HTML")
    return STATE_CHANGE_CHOICE

async def conv_change_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    t = update.message.text.strip()
    uid2, nick, region = _gapi.player(t)
    if uid2 is None:
        await update.message.reply_text("<blockquote><b>تـوكـن غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid] = {"token": t, "uid": uid2, "nick": nick}
    await update.message.reply_text(f"<blockquote><b>تـم الـتـصـديـق</b>\n\n<b>UID:</b> {uid2}\n<b>Nick:</b> {nick}\n\n<b>اخـتـر طـريـقـة الـتـحـقـق:</b></blockquote>", parse_mode="HTML", reply_markup=_kb_change())
    return STATE_CHANGE_OLD_OTP

async def conv_change_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in _user_sessions:
        await q.edit_message_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /change</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    choice = q.data
    t = _user_sessions[uid]["token"]
    bd = _gapi.bind_info(t)
    e = bd.get("email", "") if bd else ""
    if not e:
        await q.edit_message_text("<blockquote><b>لا يـوجـد بـريـد مـربـوط</b>\n\n<b>الـحـسـاب لـيـس لـديـه بـريـد إلـكـتـرونـي مـربـوط</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid]["old_email"] = e
    if choice == "change_otp":
        msg = await q.edit_message_text("<blockquote><b>جـاري إرسـال OTP...</b></blockquote>", parse_mode="HTML")
        r = _gapi.send_otp(e, t)
        d = r.json() if r.status_code == 200 else {}
        if d.get("result") == 0:
            await msg.edit_text(f"<blockquote><b>تـم إرسـال OTP</b>\n\n<b>الـبـريـد الـقـديـم:</b> {e}\n\n<b>أرسـل رقـم OTP:</b></blockquote>", parse_mode="HTML")
            return STATE_CHANGE_OLD_OTP
        else:
            await msg.edit_text(f"<blockquote><b>فـشـل إرسـال OTP</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
            return ConversationHandler.END
    elif choice == "change_sec":
        await q.edit_message_text(f"<blockquote><b>أدخـل كـود الأمـان</b>\n\n<b>الـبـريـد الـقـديـم:</b> {e}\n\n<b>أدخـل كـود الأمـان (6 أرقـام):</b></blockquote>", parse_mode="HTML")
        return STATE_CHANGE_OLD_SEC
    return ConversationHandler.END

async def conv_change_old_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    o = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /change</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    e = _user_sessions[uid].get("old_email", "")
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري الـتـحـقـق...</b></blockquote>", parse_mode="HTML")
    i = _gapi.verify_identity(e, t, otp=o)
    if not i:
        await msg.edit_text("<blockquote><b>OTP غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid]["identity"] = i
    await msg.edit_text(f"<blockquote><b>تـم الـتـحـقـق</b>\n\n<b>أرسـل الـبـريـد الإلـكـتـرونـي الـجـديـد:</b></blockquote>", parse_mode="HTML")
    return STATE_CHANGE_NEW_EMAIL

async def conv_change_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ne = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /change</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    _user_sessions[uid]["email"] = ne
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري إرسـال OTP إلـى الـبـريـد الـجـديـد...</b></blockquote>", parse_mode="HTML")
    r = _gapi.send_otp(ne, t)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text(f"<blockquote><b>تـم إرسـال OTP</b>\n\n<b>الـبـريـد الـجـديـد:</b> {ne}\n\n<b>أرسـل رقـم OTP:</b></blockquote>", parse_mode="HTML")
        return STATE_CHANGE_NEW_OTP
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل إرسـال OTP</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        return ConversationHandler.END

async def conv_change_new_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    o = update.message.text.strip()
    if uid not in _user_sessions:
        await update.message.reply_text("<blockquote><b>انـتـهـت الـجـلـسـة</b>\n\n<b>ابـدأ مـن جـديـد بـ /change</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    ne = _user_sessions[uid].get("email", "")
    t = _user_sessions[uid]["token"]
    msg = await update.message.reply_text("<blockquote><b>جـاري الـتـحـقـق مـن OTP...</b></blockquote>", parse_mode="HTML")
    v = _gapi.verify_otp(ne, o, t)
    if not v:
        await msg.edit_text("<blockquote><b>OTP غـيـر صـالـح</b>\n\n<b>الـرجـاء إعـادة الـمـحـاولـة</b></blockquote>", parse_mode="HTML")
        return ConversationHandler.END
    i = _user_sessions[uid].get("identity", "")
    await msg.edit_text("<blockquote><b>جـاري تـغـيـيـر الـبـريـد...</b></blockquote>", parse_mode="HTML")
    r = _gapi.create_rebind(i, ne, t, v)
    d = r.json() if r.status_code == 200 else {}
    if d.get("result") == 0:
        await msg.edit_text(f"<blockquote><b>تـم تـغـيـيـر الـبـريـد</b>\n\n<b>الـبـريـد الـجـديـد:</b> {ne}\n<b>الـحـالـة:</b> Success</blockquote>", parse_mode="HTML")
        _log_op(uid, "change", "success", f"new_email={ne}")
    else:
        await msg.edit_text(f"<blockquote><b>فـشـل تـغـيـيـر الـبـريـد</b>\n\n<b>الـخطـأ:</b> {d.get('error', 'Unknown')}</blockquote>", parse_mode="HTML")
        _log_op(uid, "change", "failed", d.get("error", ""))
    return ConversationHandler.END

# ====== CALLBACK HANDLER ======

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "back":
        await query.edit_message_text(_fmt_start(query.from_user.username or "User"), parse_mode="HTML", reply_markup=_kb_main())
        return
    
    if data == "cancel":
        await query.edit_message_text("<blockquote><b>تـم الإلـغـاء</b></blockquote>", parse_mode="HTML", reply_markup=_kb_main())
        return
    
    if data == "cmd_info":
        await cmd_info(update, context)
    elif data == "cmd_bind":
        await conv_bind_start(update, context)
    elif data == "cmd_unbind":
        await conv_unbind_start(update, context)
    elif data == "cmd_change":
        await conv_change_start(update, context)
    elif data == "cmd_cancel":
        await cmd_cancel(update, context)
    elif data == "cmd_revoke":
        await cmd_revoke_start(update, context)
    elif data == "cmd_platforms":
        await cmd_platforms(update, context)
    elif data == "cmd_status":
        await cmd_status(update, context)
    elif data == "confirm_revoke":
        await cmd_revoke_confirm(update, context)
    elif data in ["unbind_otp", "unbind_sec"]:
        await conv_unbind_choice(update, context)
    elif data in ["change_otp", "change_sec"]:
        await conv_change_choice(update, context)

# ====== MAIN ======

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("revoke", cmd_revoke_start))
    app.add_handler(CommandHandler("platforms", cmd_platforms))
    app.add_handler(CommandHandler("status", cmd_status))
    
    # Callback handler (الأزرار)
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # Bind conversation
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("bind", conv_bind_start), CallbackQueryHandler(conv_bind_start, pattern="^cmd_bind$")],
        states={
            STATE_BIND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_bind_token)],
            STATE_BIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_bind_email)],
            STATE_BIND_SEC: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_bind_otp)]
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)]
    ))
    
    # Unbind conversation
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("unbind", conv_unbind_start), CallbackQueryHandler(conv_unbind_start, pattern="^cmd_unbind$")],
        states={
            STATE_UNBIND_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_unbind_token)],
            STATE_UNBIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_unbind_otp)],
            STATE_UNBIND_SEC: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_unbind_sec)]
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)]
    ))
    
    # Change conversation
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("change", conv_change_start), CallbackQueryHandler(conv_change_start, pattern="^cmd_change$")],
        states={
            STATE_CHANGE_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_change_token)],
            STATE_CHANGE_OLD_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_change_old_otp)],
            STATE_CHANGE_OLD_SEC: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_change_old_otp)],
            STATE_CHANGE_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_change_new_email)],
            STATE_CHANGE_NEW_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_change_new_otp)]
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)]
    ))
    
    print("\n" + "="*50)
    print("GARENA MANAGER BOT v9.0")
    print("Developer: @yacine_X6")
    print("Channel: @UESM_Team")
    print("="*50 + "\n")
    app.run_polling()

if __name__ == "__main__":
    main()
