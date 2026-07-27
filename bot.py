#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 DARK DECRYPTOR BOT 🔥
@yacinedev - Ultimate Edition
"""

import os
import sys
import json
import base64
import struct
import hashlib
import io
import contextlib
import re
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from Crypto.Cipher import AES, ChaCha20_Poly1305, ChaCha20
from Crypto.Util.Padding import unpad

try:
    from argon2.low_level import hash_secret_raw, Type
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("❌ يرجى تثبيت: pip install python-telegram-bot")
    sys.exit(1)

# ========== إعدادات ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"  # 👈 ضع التوكن هنا
ADMIN_IDS =[6936293942]  # 👈 ضع معرفات المشرفين

# ========== كلاس فك التشفير ==========
class EHIConstants:
    L1_KEY = bytes.fromhex("7e1210f7aab956f7a668bda6e57feddb7f84ad840aef8d27b1b969959be3ab6c")
    L2_KEY_STATIC = bytes.fromhex("b2bc617c32d8b9eb1943a5ffa8051eea")
    EOO_MASTER_KEY = b"null=V5kU5+FFrY\x00"
    BYPASS_IVS = (bytes.fromhex("221d572349555f1d112133236b1f4a3f"), bytes.fromhex("5543494c53443e3f4a6a4539384e776a"), bytes.fromhex("374c2541575e4d531a3c327b75431e5f"))
    STANDARD_IVS = (bytes.fromhex("2c5d1147bbad422b3b334d4d235f1a53"), bytes.fromhex("522b01433a5e8b2fc7549e1ad368e541"), bytes.fromhex("337a1035aaedf3458ca167e92d74b839"))
    STD_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    CUSTOM_ALPHABET = "RkLC2QaVMPYgGJW/A4f7qzDb9e+t6Hr0Zp8OlNyjuxKcTw1o5EIimhBn3UvdSFXs"
    TRANSLATION_TABLE = str.maketrans(CUSTOM_ALPHABET, STD_ALPHABET)

class EHIDecryptor:
    @staticmethod
    def _custom_b64_decode(encoded_str: str) -> bytes:
        clean_str = encoded_str.replace("?", "")
        if rem := len(clean_str) % 4:
            clean_str += "=" * (4 - rem)
        return base64.b64decode(clean_str.translate(EHIConstants.TRANSLATION_TABLE))

    @staticmethod
    def _decrypt_xor_layer(ciphertext_str: str, key: str) -> Optional[str]:
        if not ciphertext_str or not ciphertext_str.strip():
            return ciphertext_str
        with contextlib.suppress(Exception):
            hex_bytes_raw = EHIDecryptor._custom_b64_decode(ciphertext_str[::-1])
            hex_string = hex_bytes_raw.decode('ascii')
            if len(hex_string) % 2 != 0:
                hex_string = f"0{hex_string}"
            raw_bytes = bytes.fromhex(hex_string)
            key_len = len(key)
            decrypted_bytes = bytearray(b ^ ord(key[i % key_len]) for i, b in enumerate(raw_bytes) if (b ^ ord(key[i % key_len])) != 0)
            plaintext = decrypted_bytes.decode('utf-8')
            if plaintext and (sum(1 for c in plaintext if ord(c) < 32 and ord(c) not in (9, 10, 13)) / len(plaintext)) > 0.5:
                return None
            return plaintext
        return None

    @staticmethod
    def _decode_config_message(ciphertext_str: str) -> str:
        if not ciphertext_str or not ciphertext_str.strip():
            return ciphertext_str
        with contextlib.suppress(Exception):
            padded_str = ciphertext_str + "=" * ((4 - len(ciphertext_str) % 4) % 4)
            raw_bytes = base64.b64decode(padded_str)
            utf16_bytes = raw_bytes.decode('utf-8', errors='replace').encode('utf-16-be', errors='surrogatepass')
            num_chars = len(utf16_bytes) // 2
            java_chars = struct.unpack(f'>{num_chars}H', utf16_bytes)
            key_chars = [ord(c) for c in "EHIMSG"]
            key_len = len(key_chars)
            xored_chars = [jc ^ key_chars[i % key_len] for i, jc in enumerate(java_chars)]
            xored_bytes = struct.pack(f'>{num_chars}H', *xored_chars)
            return xored_bytes.decode('utf-16-be', errors='surrogatepass').encode('utf-16', 'surrogatepass').decode('utf-16')
        return ciphertext_str

    @staticmethod
    def _decode_inner_fields(parsed_json: Dict[str, Any], salt_key: str) -> Dict[str, Any]:
        cleaned_json = {}
        vital_keys = {"overwriteServerData"}
        for k, v in parsed_json.items():
            if isinstance(v, str) and v.strip():
                decrypted_val = EHIDecryptor._decode_config_message(v) if k == "configMessage" else EHIDecryptor._decrypt_xor_layer(v, salt_key)
                if decrypted_val is not None:
                    cleaned_json[k] = decrypted_val
                elif k in vital_keys:
                    cleaned_json[k] = v
            else:
                cleaned_json[k] = v
        return cleaned_json

    @staticmethod
    def _xxtea_decrypt(data: bytes, key: bytes) -> bytes:
        if not data:
            return b""
        if rem := len(data) % 4:
            data += b'\x00' * (4 - rem)
        k = struct.unpack('<4I', key.ljust(16, b'\x00')[:16])
        n = len(data) // 4
        v = list(struct.unpack(f'<{n}I', data))
        delta = 0x9e3779b9
        sum_val = ((6 + 52 // n) * delta) & 0xffffffff
        y = v[0]
        while sum_val != 0:
            e = (sum_val >> 2) & 3
            for p in range(n - 1, 0, -1):
                z = v[p - 1]
                mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((sum_val ^ y) + (k[(p & 3) ^ e] ^ z))
                y = v[p] = (v[p] - mx) & 0xffffffff
            z = v[n - 1]
            mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((sum_val ^ y) + (k[(0 & 3) ^ e] ^ z))
            y = v[0] = (v[0] - mx) & 0xffffffff
            sum_val = (sum_val - delta) & 0xffffffff
        decrypted = struct.pack(f'<{n}I', *v)
        length = v[-1]
        return decrypted[:length] if 0 < length <= n * 4 else decrypted.rstrip(b'\x00')

    @staticmethod
    def _parse_ehi_bytes(file_bytes: bytes) -> Optional[bytes]:
        try:
            f = io.BytesIO(file_bytes)
            def r_utf() -> str:
                if len(l_bytes := f.read(2)) < 2:
                    return ""
                return f.read(struct.unpack('>H', l_bytes)[0]).decode('utf-8', errors='ignore')
            r_utf()
            f.read(8)
            r_utf()
            f.read(8)
            if len(p_len_bytes := f.read(4)) < 4:
                return None
            p_len = struct.unpack('>I', p_len_bytes)[0]
            f.read(8)
            return f.read(p_len)
        except struct.error:
            return None

    @staticmethod
    def _generate_master_key(config: Dict[str, Any]) -> bytes:
        payload = "".join(str(p) for p in (
            config.get("configAesKey", ""), config.get("configIdentifier", ""),
            config.get("configSalt", ""), str(config.get("configTimestamp", 0)),
            str(config.get("configExpiryTimestamp", 0)), config.get("lockModes", ""),
            config.get("lockModesHash", ""), config.get("configHwid", ""),
            config.get("configLockMobileOperatorId", "")
        ) if p)
        return hashlib.sha256(payload.encode('utf-8')).digest()

    @classmethod
    def execute(cls, file_bytes: bytes) -> Optional[Dict]:
        if not ARGON2_AVAILABLE:
            return None
        payload = cls._parse_ehi_bytes(file_bytes)
        if not payload:
            return None
        config, matched_iv = None, None
        all_ivs = EHIConstants.BYPASS_IVS + EHIConstants.STANDARD_IVS
        for iv in all_ivs:
            with contextlib.suppress(Exception):
                c1 = AES.new(EHIConstants.L1_KEY, AES.MODE_CBC, iv)
                l1_text = unpad(c1.decrypt(payload), 16).decode('utf-8')
                if (parts := l1_text.split(":")) and len(parts) >= 3:
                    c2 = AES.new(EHIConstants.L2_KEY_STATIC, AES.MODE_CBC, base64.b64decode(parts[0]))
                    garbage = unpad(c2.decrypt(base64.b64decode(parts[2])), 16)
                    final_raw = cls._xxtea_decrypt(garbage, EHIConstants.EOO_MASTER_KEY)
                    if (start := final_raw.find(b'{')) != -1:
                        config = json.loads(final_raw[start:].decode('utf-8', errors='ignore'))
                        matched_iv = iv
                        break
        if not config:
            return None
        target_salt = config.get('configSalt', "EVZJNI")
        if matched_iv in EHIConstants.BYPASS_IVS:
            parsed_final = config
        else:
            target_data = config.get('configData')
            if not target_data or not (aaa_result := cls._decrypt_xor_layer(target_data, target_salt)):
                return None
            raw_payload = base64.b64decode(aaa_result)
            if len(raw_payload) <= 50:
                return None
            try:
                argon_key = hash_secret_raw(
                    secret=cls._generate_master_key(config),
                    salt=raw_payload[0x0a:0x1a],
                    time_cost=int.from_bytes(raw_payload[1:5], "little"),
                    memory_cost=int.from_bytes(raw_payload[5:9], "little"),
                    parallelism=raw_payload[9],
                    hash_len=32,
                    type=Type.ID
                )
                cipher3 = ChaCha20_Poly1305.new(key=argon_key, nonce=raw_payload[0x1a:0x32])
                cipher3.update(raw_payload[:0x1a])
                decrypted_json_bytes = cipher3.decrypt_and_verify(raw_payload[0x32:-16], raw_payload[-16:])
                parsed_final = json.loads(decrypted_json_bytes.decode('utf-8', errors='ignore'))
            except Exception:
                return None
        cleaned_final_json = cls._decode_inner_fields(parsed_final, target_salt)
        for json_field in ("v2rRawJson", "overwriteServerData"):
            if json_field in cleaned_final_json and isinstance(raw_str := cleaned_final_json[json_field], str):
                try:
                    if (start_idx := raw_str.find('{')) != -1 and (end_idx := raw_str.rfind('}')) != -1:
                        parsed_obj = json.loads(raw_str[start_idx:end_idx+1], strict=False)
                        cleaned_final_json[json_field] = json.loads(parsed_obj, strict=False) if isinstance(parsed_obj, str) else parsed_obj
                except Exception:
                    pass
        return cleaned_final_json

class HCConstants:
    CHACHA_KEYS = [
        bytes.fromhex("2be4342943c6f91ff58987f41a1aafd179eeb4e053f5cea55b11d6a7db58bd7d"),
        bytes.fromhex("3380aa278b744ba5b529a7f32fa803e48749280dae378345d9b526cf1dbce372"),
        bytes.fromhex("cea9305c95168b162a335b137c61983b8df54e6375da01136547890f14c5fac3"),
        bytes.fromhex("4beeace0e42bae8f29470cf40cf2dfacd5f4e1f751912bf52e803c8c85792193"),
        bytes.fromhex("f8e5f6ebea90558eb32229da24fd0fb7d813091dafe89bb2954fda33b4c60f63"),
        bytes.fromhex("81342f558a6273bac4548d473f54c4ffc7c41747dee81369acab9c787d41ab9c"),
        bytes.fromhex("45635e6fc70486e2fd10d3c2b4780f02d0b4c5f4aa929fc54f86bb8fa4417944"),
        bytes.fromhex("3d632a251c9820f2baf83e15498d27548fc67921cb437f8ce48505989378adea")
    ]
    RST_KEYS = [b"JN1k3YHc2.6_v235", b"JN1k3YHc_2.7_v71", b"JN1k3YHc2.7.ps69", b"JN1k3YHc2.7.6950", b"Jn1K3yHc2.8.ps08", b"Jn1K3yHc2.9.ps6c", b"Zk:L7>WKaiK*s9>D", b"!<f!&WIlM**R.B0X", b"b4a5opinx2uloec6"]
    JKL_KEY_OLD = bytes([0xd5,0xd4,0xd3,0xd2,0xd1,0xd0,0xcf,0xce,0xcd,0xcc,0xbd,0xbc,0xbb,0xba,0xb9,0xb8,0xb7,0xb6,0xb5,0xb4])
    JKL_KEY_NEW = bytes([8,9,10,11,12,13,14,15,17,17,5,4,3,2,1,0,255,254,253,252])
    TOKEN_MAP = {0:"payload",1:"proxy",2:"lockAllConfig",3:"blockedByRoot",4:"expiryTime",5:"noteEnabled",6:"notes",7:"sshField",8:"mobileDataAndLockProvider",9:"unlockUserAndPass",10:"ovpnConfig",11:"ovpnUserAndPass",12:"sni",13:"unlockUserAndPass2",14:"unknown14",15:"blockedByHwid",16:"cloudconfig",17:"psiphon",18:"name",19:"blockArea",20:"connectionMode",21:"blockedByPassword",22:"unknown22",23:"extraSniffer",24:"psiphon2",25:"v2rayEnabled",26:"v2rayConfig",27:"version",28:"slowdnsEnabled",29:"slowdnsServer",30:"slowdnsPublickey",31:"dnsResolver"}
    BRAILLE_ALPHABET = "â €â â ƒâ ‰â ™â ‘â ‹â ›â “â Šâ šâ …â ‡â â â •â â Ÿâ —â Žâ žâ ¥â §â ºâ ­â ½â µâ ¼â â ¼â ƒâ ¼â ‰â ¼â ™â ¼â ‘â ¼â ‹â ¼â ›â ¼â “â ¼â Šâ ¼â š"
    STATIC_NONCE = b'\xdb' * 8
    RST_XOR_KEY = bytes(range(2, 22))

class HCDecryptor:
    @staticmethod
    def _clean_hex(raw_str: str) -> str:
        if not raw_str:
            return ""
        clean = re.sub(r'[^0-9a-fA-F]', '', raw_str)
        return f"0{clean}" if len(clean) % 2 != 0 else clean

    @staticmethod
    def _is_hex(s: str) -> bool:
        return bool(s and len(s) >= 16 and re.fullmatch(r'^[0-9a-fA-F]+$', s))

    @staticmethod
    def _is_mostly_printable(s: str, strict: bool = False) -> bool:
        if not s:
            return False
        if len(s) < 4:
            return True
        printable_count = sum(1 for c in s if c.isprintable() or c in '\t\n\r')
        return (printable_count / len(s)) > (0.90 if strict else 0.80)

    @staticmethod
    def _extract_z3a(data: str, iv: int) -> str:
        if not data:
            return ""
        new_data = bytearray()
        for m in re.finditer(r'(-?\d+)\.(-?\d+)', data):
            val11, val22 = int(m.group(1)) - iv, int(m.group(2)) - iv
            with contextlib.suppress(Exception):
                if (divisor := 1 << val22) != 0:
                    new_data.append((val11 // divisor) % 256)
        return new_data.decode('utf-8', errors='ignore')

    @staticmethod
    def _decrypt_braille(ciphertext: str) -> str:
        try:
            return bytes((HCConstants.BRAILLE_ALPHABET.index(ciphertext[i]) * 16 + HCConstants.BRAILLE_ALPHABET.index(ciphertext[i+1])) & 255 for i in range(0, len(ciphertext)-1, 2)).decode('utf-8')
        except ValueError:
            return ciphertext

    @classmethod
    def _process_credentials(cls, raw_val: str, is_ssh: bool = False) -> str:
        if not raw_val:
            return raw_val
        if is_ssh and raw_val[0] in HCConstants.BRAILLE_ALPHABET:
            raw_val = cls._decrypt_braille(raw_val)
        pattern = r'^([\w\.-]+):([\d\-]+)@(.+):(.+)$' if is_ssh else r'^([^:]+):(.+)$'
        if match := re.match(pattern, raw_val):
            groups = match.groups()
            u_enc, p_enc = groups[-2:]
            u_dec = cls._extract_z3a(u_enc, len(re.findall(r'(-?\d+)\.(-?\d+)', u_enc)))
            p_dec = cls._extract_z3a(p_enc, len(re.findall(r'(-?\d+)\.(-?\d+)', p_enc)))
            final_user, final_pass = u_dec or u_enc, p_dec or p_enc
            return f"{groups[0]}:{groups[1]}@{final_user}:{final_pass}" if is_ssh else f"{final_user}:{final_pass}"
        return raw_val

    @classmethod
    def _abc_decrypt(cls, raw_input: str, key: bytes, nonce: bytes = HCConstants.STATIC_NONCE) -> str:
        if not raw_input:
            return ""
        with contextlib.suppress(Exception):
            data = bytes.fromhex(cls._clean_hex(raw_input))
            if len(data) > 16:
                cipher = ChaCha20.new(key=key, nonce=nonce)
                cipher.seek(64)
                decrypted = cipher.decrypt(data[:-16])
                return decrypted.decode('utf-8', errors='ignore')
        return ""

    @classmethod
    def _rst_decrypt(cls, encrypted_str: str) -> Optional[str]:
        with contextlib.suppress(Exception):
            b64_string = bytes(b ^ HCConstants.RST_XOR_KEY[i % 20] for i, b in enumerate(encrypted_str.encode('utf-8')))
            aes_ciphertext = base64.b64decode(b64_string)
            for aes_key in HCConstants.RST_KEYS:
                with contextlib.suppress(Exception):
                    decrypted = unpad(AES.new(aes_key, AES.MODE_ECB).decrypt(aes_ciphertext), AES.block_size)
                    dec_str = decrypted.decode('utf-8', errors='ignore')
                    if "[splitConfig]" in dec_str:
                        return dec_str
        return None

    @classmethod
    def _jkl_decrypt(cls, input_str: str, is_new: bool = False) -> str:
        if not input_str:
            return input_str
        active_key = HCConstants.JKL_KEY_NEW if is_new else HCConstants.JKL_KEY_OLD
        with contextlib.suppress(Exception):
            pad = len(input_str) % 4
            padded_str = input_str + "=" * (4 - pad) if pad else input_str
            data = bytearray(base64.b64decode(padded_str, validate=True))
            for i, d in enumerate(data):
                k = active_key[i % 20]
                data[i] = (((d ^ 0xff) & 0xca) | (d & 0x35)) ^ (((k ^ 0xff) & 0xca) | (k & 0x35))
            return base64.b64decode(data.decode('utf-8'), validate=True).decode('utf-8')
        return input_str

    @classmethod
    def _decrypt_field(cls, token: str, dynamic_nonce: bytes) -> str:
        if not token or token in {"true", "false", "lifeTime", "[splitPsiphon][splitPsiphon]"} or token.startswith("<"):
            return token
        candidates = []
        if cls._is_hex(clean_h := cls._clean_hex(token)) and len(clean_h) >= 32:
            with contextlib.suppress(Exception):
                candidates.append(bytes.fromhex(clean_h))
        if len(token) > 16:
            with contextlib.suppress(Exception):
                candidates.append(token.encode('latin-1'))
            with contextlib.suppress(Exception):
                candidates.append(token.encode('utf-8'))
        unique_cands = list(dict.fromkeys(candidates))
        for data_bytes in (c for c in unique_cands if len(c) > 16):
            ciphertext = data_bytes[:-16]
            for chacha_key in HCConstants.CHACHA_KEYS:
                with contextlib.suppress(Exception):
                    cipher = ChaCha20.new(key=chacha_key, nonce=dynamic_nonce)
                    cipher.seek(64)
                    dec_str = cipher.decrypt(ciphertext).decode('utf-8', errors='ignore')
                    for is_new in (True, False):
                        if (out := cls._jkl_decrypt(dec_str, is_new)) and out != dec_str and cls._is_mostly_printable(out):
                            return out
                    if cls._is_mostly_printable(dec_str, strict=True) and any(x in dec_str for x in ("HTTP", "@", ":", "{")) or dec_str.isalnum():
                        return dec_str
        for is_new in (True, False):
            if (out := cls._jkl_decrypt(token, is_new)) != token and cls._is_mostly_printable(out):
                return out
        return token

    @staticmethod
    def _extract_initial_payload(file_bytes: bytes, hex_key: str) -> Optional[str]:
        with contextlib.suppress(Exception):
            key_bytes = bytes.fromhex(hex_key)
            k_len = len(key_bytes)
            try:
                encrypted_data = file_bytes.decode('utf-8', errors='ignore').encode('latin-1', errors='ignore')
            except Exception:
                encrypted_data = file_bytes
            return bytes(b ^ key_bytes[i % k_len] for i, b in enumerate(encrypted_data)).decode('utf-8')
        return None

    @classmethod
    def execute(cls, file_bytes: bytes) -> Optional[Dict]:
        if not file_bytes or not (hex_payload := cls._extract_initial_payload(file_bytes, "e382e4b8adc386f09f9293")):
            return None
        with contextlib.suppress(Exception):
            if not (outer := cls._abc_decrypt(hex_payload, HCConstants.CHACHA_KEYS[5])) or not outer.startswith("{"):
                return None
            json_obj = json.loads(outer)
            if not isinstance(json_obj, dict):
                return None
            cfg_obj = json_obj.get("cfg", {})
            is_new_format = isinstance(cfg_obj, dict) and "content" in cfg_obj
            meta_values, protections = {}, {}
            if is_new_format:
                for k, name in {'b': 'hwid', 'f': 'area'}.items():
                    if val := str(json_obj.get(k) or cfg_obj.get(k) or ""):
                        meta_values[name] = protections[name] = val
                target_cipher, split_delim = cfg_obj.get('content'), "[splitConfig]"
            else:
                obj_a = json_obj.get('a') if isinstance(json_obj.get('a'), dict) else {}
                for k, name in {'bb': 'hwid', 'e': 'password', 'fe': 'area', 'ed': 'provider'}.items():
                    if val := (json_obj.get(k) if k == 'e' else obj_a.get(k)):
                        if dec_val := cls._abc_decrypt(str(val), HCConstants.CHACHA_KEYS[7]):
                            meta_values[name] = protections[name] = dec_val
                target_cipher, split_delim = json_obj.get('xy') or obj_a.get('xy'), json_obj.get('uv') or obj_a.get('uv')
            if not target_cipher or not split_delim:
                return None
            to_hex = lambda s: s.encode().hex() if s else ""
            h, p, pr, a = meta_values.get('hwid'), meta_values.get('password'), meta_values.get('provider'), meta_values.get('area')
            derived_hex = (to_hex(h) * 2) if h and not any((p, pr, a)) else (to_hex(p) + to_hex(h) + to_hex(pr) + to_hex(a))
            dynamic_nonce = bytearray(HCConstants.STATIC_NONCE)
            if derived_hex:
                with contextlib.suppress(Exception):
                    for i, b in enumerate(bytes.fromhex(derived_hex)[:8]):
                        dynamic_nonce[i] = b
            xy_dec = None
            if is_new_format:
                xy_dec = cls._rst_decrypt(str(target_cipher))
                if not xy_dec:
                    for key in HCConstants.CHACHA_KEYS:
                        if (temp := cls._abc_decrypt(str(target_cipher), key)) and split_delim in temp:
                            xy_dec = temp
                            break
            else:
                xy_dec = cls._abc_decrypt(str(target_cipher), HCConstants.CHACHA_KEYS[1])
            if not xy_dec:
                return None
            config_data = {}
            for i, token in enumerate(xy_dec.split(str(split_delim))):
                if i in {22, 24}:
                    continue
                label = HCConstants.TOKEN_MAP.get(i, f"field_{i}")
                final_out = token
                if is_new_format:
                    final_out = cls._decrypt_field(token, dynamic_nonce)
                else:
                    if cls._is_hex(token):
                        final_out = cls._abc_decrypt(token, HCConstants.CHACHA_KEYS[7], dynamic_nonce)
                    final_out = cls._jkl_decrypt(final_out, is_new=False)
                if i == 7:
                    final_out = cls._process_credentials(final_out, is_ssh=True)
                elif i == 11:
                    final_out = cls._process_credentials(final_out, is_ssh=False)
                if final_out:
                    if isinstance(final_out, str):
                        final_out = final_out.replace("88a05e8772eac3e5703e0cd26c6e6f23de72fb09f7ee5a43283d1681f19d", "")
                        with contextlib.suppress(Exception):
                            if final_out.startswith(("{", "[")):
                                final_out = json.loads(final_out)
                    if not (isinstance(final_out, str) and cls._is_hex(final_out)):
                        config_data[label] = final_out
            return {"Protections": protections, "Config": config_data}
        return None

class DTConstants:
    KEY_256 = b"$B&E)H@McQfThWmZq4t7w!z%C*F-JaNd"
    KEY_192 = b"F)J@NcRfUjXn2r4u7x!A%D*G"
    IV = bytes.fromhex("232e39185523184a5723586242200e05")

class DTDecryptor:
    @staticmethod
    def _base64_decode_safe(data: str) -> bytes:
        clean_data = data.replace("-", "+").replace("_", "/")
        if pad := len(clean_data) % 4:
            clean_data += "=" * (4 - pad)
        return base64.b64decode(clean_data)

    @staticmethod
    def _aes_cfb_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
        return AES.new(key, AES.MODE_CFB, iv=iv, segment_size=128).decrypt(data)

    @staticmethod
    def _is_utf8_printable(value: bytes) -> bool:
        if not value:
            return False
        try:
            return bool(re.fullmatch(r"[^\x00-\x08\x0B\x0C\x0E-\x1F\x7F]*", value.decode("utf-8")))
        except UnicodeDecodeError:
            return False

    @classmethod
    def _try_parse_json_string(cls, value: str) -> Union[Dict, List, str]:
        stripped = value.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            with contextlib.suppress(Exception):
                fixed_json = re.sub(r'(:\s*)(\$[A-Za-z0-9_]+)', r'\1"\2"', stripped)
                return cls._normalize_for_json(json.loads(fixed_json))
        return value

    @classmethod
    def _normalize_for_json(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: cls._normalize_for_json(v) for k, v in value.items() if k != "Password"}
        if isinstance(value, list):
            return [cls._normalize_for_json(v) for v in value]
        if isinstance(value, bytes):
            return cls._try_parse_json_string(value.decode("utf-8")) if cls._is_utf8_printable(value) else list(value)
        if isinstance(value, str):
            return cls._try_parse_json_string(value)
        return value

    @classmethod
    def _clean_encrypted(cls, value: Any, key: bytes, iv: bytes) -> Any:
        if isinstance(value, dict):
            cleaned = {}
            for k, v in value.items():
                if isinstance(k, str) and k.startswith("Encrypted") and v and isinstance(v, (bytes, bytearray)):
                    try:
                        cleaned[k] = cls._aes_cfb_decrypt(bytes(v), key, iv)
                    except Exception:
                        cleaned[k] = v
                else:
                    cleaned[k] = cls._clean_encrypted(v, key, iv)
            return cleaned
        if isinstance(value, list):
            return [cls._clean_encrypted(v, key, iv) for v in value]
        return value

    @classmethod
    def execute(cls, file_bytes: bytes) -> Optional[Dict]:
        if not MSGPACK_AVAILABLE:
            return None
        with contextlib.suppress(Exception):
            raw_input = file_bytes.decode('utf-8', errors='ignore').strip()
            if not raw_input:
                return None
            if "://" in raw_input:
                raw_input = raw_input.split("://", 1)[1]
            outer = json.loads(cls._base64_decode_safe(raw_input).decode("utf-8"))
            if "encryptedLockedConfig" not in outer:
                return None
            encrypted_locked_config = cls._base64_decode_safe(outer["encryptedLockedConfig"])
            decrypted_outer = cls._aes_cfb_decrypt(encrypted_locked_config, DTConstants.KEY_256, DTConstants.IV)
            unpacked_outer = msgpack.unpackb(decrypted_outer, raw=False, strict_map_key=False)
            if "EncryptedLockedConfig" in unpacked_outer:
                decrypted_inner = cls._aes_cfb_decrypt(unpacked_outer["EncryptedLockedConfig"], DTConstants.KEY_192, DTConstants.IV)
                unpacked_inner = msgpack.unpackb(decrypted_inner, raw=False, strict_map_key=False)
                unpacked_outer["EncryptedLockedConfig"] = cls._clean_encrypted(unpacked_inner, DTConstants.KEY_192, DTConstants.IV)
            outer["encryptedLockedConfig"] = unpacked_outer
            return cls._normalize_for_json(outer)
        return None

# ==================== دوال البوت ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح لك.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔓 فك تشفير EHI", callback_data="decrypt_ehi")],
        [InlineKeyboardButton("🔓 فك تشفير HC", callback_data="decrypt_hc")],
        [InlineKeyboardButton("🔓 فك تشفير DARK", callback_data="decrypt_dark")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔥 **DARK DECRYPTOR BOT** 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 بوت فك تشفير ملفات:\n"
        "🔹 EHI (HTTP Injector)\n"
        "🔹 HC (HTTP Custom)\n"
        "🔹 DARK (Dark Tunnel)\n\n"
        "📤 أرسل الملف أو اختر النوع:",
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
    
    if action == "decrypt_ehi":
        context.user_data['decrypt_type'] = 'ehi'
        await query.edit_message_text(
            "📤 **فك تشفير EHI**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "أرسل ملف `.ehi` لفك تشفيره."
        )
    elif action == "decrypt_hc":
        context.user_data['decrypt_type'] = 'hc'
        await query.edit_message_text(
            "📤 **فك تشفير HC**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "أرسل ملف `.hc` لفك تشفيره."
        )
    elif action == "decrypt_dark":
        context.user_data['decrypt_type'] = 'dark'
        await query.edit_message_text(
            "📤 **فك تشفير DARK**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "أرسل ملف `.dark` لفك تشفيره."
        )
    elif action == "stats":
        await show_stats(update, context)
    elif action == "help":
        await show_help(update, context)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stats = context.user_data.get('stats', {'total': 0, 'success': 0, 'failed': 0})
    
    message = (
        "📊 **الإحصائيات**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 المجموع: {stats.get('total', 0)}\n"
        f"✅ الناجحة: {stats.get('success', 0)}\n"
        f"❌ الفاشلة: {stats.get('failed', 0)}\n"
        f"📈 نسبة النجاح: {int((stats['success']/stats['total'])*100) if stats['total'] > 0 else 0}%"
    )
    await query.edit_message_text(message)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    message = (
        "ℹ️ **المساعدة**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **الأوامر:**\n"
        "/start - عرض القائمة\n"
        "/stats - عرض الإحصائيات\n"
        "/help - هذه المساعدة\n\n"
        "📤 **الملفات المدعومة:**\n"
        "🔹 .ehi - HTTP Injector\n"
        "🔹 .hc - HTTP Custom\n"
        "🔹 .dark - Dark Tunnel\n\n"
        "🔹 اختر النوع من الأزرار ثم أرسل الملف."
    )
    await query.edit_message_text(message)

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح لك.")
        return
    
    file_type = context.user_data.get('decrypt_type')
    if not file_type:
        await update.message.reply_text(
            "❌ يرجى اختيار نوع الملف أولاً من الأزرار."
        )
        return
    
    document = update.message.document
    if not document:
        await update.message.reply_text("❌ يرجى إرسال ملف.")
        return
    
    # تحميل الملف
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    
    await update.message.reply_text("⏳ **جاري فك التشفير...**")
    
    # فك التشفير
    result = None
    if file_type == 'ehi':
        result = EHIDecryptor.execute(bytes(file_bytes))
    elif file_type == 'hc':
        result = HCDecryptor.execute(bytes(file_bytes))
    elif file_type == 'dark':
        result = DTDecryptor.execute(bytes(file_bytes))
    
    # تحديث الإحصائيات
    stats = context.user_data.get('stats', {'total': 0, 'success': 0, 'failed': 0})
    stats['total'] += 1
    
    if result:
        stats['success'] += 1
        context.user_data['stats'] = stats
        
        # تنسيق النتيجة
        result_text = json.dumps(result, indent=2, ensure_ascii=False)[:4000]
        
        await update.message.reply_text(
            f"✅ **فك التشفير ناجح!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 **النتيجة:**\n```json\n{result_text}\n```",
            parse_mode='Markdown'
        )
    else:
        stats['failed'] += 1
        context.user_data['stats'] = stats
        await update.message.reply_text("❌ **فشل فك التشفير!**\nيرجى التأكد من صحة الملف.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ أمر غير معروف.\n"
        "استخدم /start للبدء."
    )

# ========== تشغيل البوت ==========
def main():
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ يرجى إدخال توكن البوت في المتغير TOKEN")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("help", show_help))
    
    app.add_handler(CallbackQueryHandler(handle_buttons, pattern="^(decrypt_ehi|decrypt_hc|decrypt_dark|stats|help)$"))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
