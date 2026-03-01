import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import threading
import time
import random
import string
import json
import hmac
import hashlib
import base64
import os
import codecs
import urllib3
import subprocess
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

# ==========================================
# 𝐅𝐋𝐀𝐒𝐊 𝐈𝐌𝐏𝐎𝐑𝐓𝐒
# ==========================================
from flask import Flask, jsonify, request, send_file, render_template_string
import threading
import psutil
from datetime import datetime, timedelta
import sqlite3
import csv
from io import StringIO, BytesIO

# ==========================================
# 𝐂𝐎𝐍𝐅𝐈𝐆𝐔𝐑𝐀𝐓𝐈𝐎𝐍
# ==========================================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_TOKEN = '8114132308:AAFn5sVwq5MR7tyWQadp1zNC_FcQxLgbQ2c' 
OWNER_ID = 123456789  # Replace with your Telegram ID

bot = telebot.TeleBot(API_TOKEN)

# 𝐏𝐫𝐨𝐱𝐲 𝐂𝐨𝐧𝐟𝐢𝐠 - Disable proxies on Render since Tor won't work
IS_RENDER = os.environ.get('RENDER', False) or 'RENDER' in os.environ

if IS_RENDER:
    PROXIES = {}
    print("🚀 Running on Render - Tor disabled")
else:
    PROXIES = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

user_data = {}
user_settings = {}
active_generations = {}
bot_stats = {
    'total_generations': 0,
    'total_accounts': 0,
    'total_real': 0,
    'total_fake': 0,
    'start_time': datetime.now()
}

# ==========================================
# 𝐃𝐀𝐒𝐇𝐁𝐎𝐀𝐑𝐃 𝐂𝐎𝐍𝐅𝐈𝐆
# ==========================================
DASHBOARD_PORT = int(os.environ.get('PORT', 5000))
DASHBOARD_HOST = '0.0.0.0'  # Critical for Render

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS generation_stats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME,
                  user_id INTEGER,
                  username TEXT,
                  first_name TEXT,
                  count INTEGER,
                  real_accounts INTEGER,
                  fake_accounts INTEGER,
                  region TEXT,
                  speed REAL,
                  duration REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bot_users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  last_seen DATETIME,
                  join_date DATETIME,
                  total_generations INTEGER DEFAULT 0,
                  total_accounts_generated INTEGER DEFAULT 0,
                  total_real_accounts INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS verified_accounts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME,
                  uid TEXT,
                  password TEXT,
                  nickname TEXT,
                  region TEXT,
                  user_id INTEGER,
                  username TEXT,
                  open_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 𝐎𝐑𝐈𝐆𝐈𝐍𝐀𝐋 𝐁𝐔𝐓𝐓𝐎𝐍 𝐓𝐄𝐗𝐓 (𝐘𝐎𝐔𝐑 𝐅𝐎𝐍𝐓 𝐒𝐓𝐘𝐋𝐄)
# ==========================================

BUTTONS = {
    'generate': '⚡ 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄',
    'history': '📊 𝐇𝐈𝐒𝐓𝐎𝐑𝐘',
    'profile': '👤 𝐏𝐑𝐎𝐅𝐈𝐋𝐄',
    'settings': '⚙️ 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒',
    'help': '❓ 𝐇𝐄𝐋𝐏',
    'owner': '👑 𝐎𝐖𝐍𝐄𝐑',
    'status': '📈 𝐒𝐓𝐀𝐓𝐔𝐒',
    'restart': '🔄 𝐑𝐄𝐒𝐓𝐀𝐑𝐓',
    'set_region': '🌍 𝐑𝐄𝐆𝐈𝐎𝐍',
    'set_speed': '⚡ 𝐒𝐏𝐄𝐄𝐃',
    'set_prefix': '🔑 𝐏𝐑𝐄𝐅𝐈𝐗',
    'back_main': '🔙 𝐁𝐀𝐂𝐊',
    'region_ind': '🇮🇳 𝐈𝐍𝐃𝐈𝐀',
    'region_bd': '🇧🇩 𝐁𝐀𝐍𝐆𝐋𝐀𝐃𝐄𝐒𝐇',
    'region_sg': '🇸🇬 𝐒𝐈𝐍𝐆𝐀𝐏𝐎𝐑𝐄',
    'region_eu': '🇪🇺 𝐄𝐔𝐑𝐎𝐏𝐄',
    'region_ru': '🇷🇺 𝐑𝐔𝐒𝐒𝐈𝐀',
    'region_br': '🇧🇷 𝐁𝐑𝐀𝐙𝐈𝐋',
    'region_us': '🇺🇸 𝐔𝐒𝐀',
    'region_uk': '🇬🇧 𝐔𝐊',
    'speed_ultra': '🚀 𝐔𝐋𝐓𝐑𝐀',
    'speed_fast': '⚡ 𝐅𝐀𝐒𝐓',
    'speed_medium': '⏱️ 𝐌𝐄𝐃𝐈𝐔𝐌',
    'speed_slow': '🐢 𝐒𝐋𝐎𝐖',
    'speed_safe': '🛡️ 𝐒𝐀𝐅𝐄',
    'confirm_yes': '✅ 𝐘𝐄𝐒',
    'confirm_no': '❌ 𝐍𝐎',
    'cancel': '❌ 𝐂𝐀𝐍𝐂𝐄𝐋'
}

# ==========================================
# 𝐊𝐄𝐘𝐁𝐎𝐀𝐑𝐃 𝐌𝐀𝐏𝐏𝐈𝐍𝐆
# ==========================================

def create_main_keyboard(is_owner=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton(BUTTONS['generate']), KeyboardButton(BUTTONS['history']))
    markup.row(KeyboardButton(BUTTONS['profile']), KeyboardButton(BUTTONS['settings']))
    markup.row(KeyboardButton(BUTTONS['help']), KeyboardButton(BUTTONS['status']))
    if is_owner:
        markup.row(KeyboardButton(BUTTONS['owner']), KeyboardButton(BUTTONS['restart']))
    else:
        markup.row(KeyboardButton(BUTTONS['restart']))
    return markup

def create_settings_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton(BUTTONS['set_region']), KeyboardButton(BUTTONS['set_speed']))
    markup.row(KeyboardButton(BUTTONS['set_prefix']), KeyboardButton(BUTTONS['back_main']))
    return markup

def create_region_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton(BUTTONS['region_ind']), KeyboardButton(BUTTONS['region_bd']))
    markup.row(KeyboardButton(BUTTONS['region_sg']), KeyboardButton(BUTTONS['region_eu']))
    markup.row(KeyboardButton(BUTTONS['region_ru']), KeyboardButton(BUTTONS['region_br']))
    markup.row(KeyboardButton(BUTTONS['region_us']), KeyboardButton(BUTTONS['region_uk']))
    markup.row(KeyboardButton(BUTTONS['back_main']))
    return markup

def create_speed_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton(BUTTONS['speed_ultra']), KeyboardButton(BUTTONS['speed_fast']))
    markup.row(KeyboardButton(BUTTONS['speed_medium']), KeyboardButton(BUTTONS['speed_slow']))
    markup.row(KeyboardButton(BUTTONS['speed_safe']))
    markup.row(KeyboardButton(BUTTONS['back_main']))
    return markup

def create_confirm_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton(BUTTONS['confirm_yes']), KeyboardButton(BUTTONS['confirm_no']))
    markup.row(KeyboardButton(BUTTONS['cancel']))
    return markup

def create_inline_region_buttons():
    markup = InlineKeyboardMarkup(row_width=3)
    regions = [
        ('🇮🇳 IND', 'reg_ind'), ('🇧🇩 BD', 'reg_bd'), ('🇸🇬 SG', 'reg_sg'),
        ('🇪🇺 EU', 'reg_eu'), ('🇷🇺 RU', 'reg_ru'), ('🇧🇷 BR', 'reg_br'),
        ('🇺🇸 USA', 'reg_us'), ('🇬🇧 UK', 'reg_uk'), ('🇯🇵 JP', 'reg_jp')
    ]
    buttons = [InlineKeyboardButton(text, callback_data=data) for text, data in regions]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_main"))
    return markup

# ==========================================
# 𝐓𝐎𝐑 𝐒𝐄𝐑𝐕𝐈𝐂𝐄 (𝐃𝐈𝐒𝐀𝐁𝐋𝐄𝐃 𝐎𝐍 𝐑𝐄𝐍𝐃𝐄𝐑)
# ==========================================

def start_tor_service():
    if IS_RENDER:
        print("⏭️ Skipping Tor on Render")
        return True
        
    try:
        result = subprocess.run(['pgrep', 'tor'], capture_output=True)
        if result.returncode == 0:
            print("✅ Tor is already running")
            return True
        print("🔄 Starting Tor service...")
        subprocess.Popen(['tor', '--quiet'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL)
        time.sleep(5)
        return True
    except Exception as e:
        print(f"❌ Tor error: {e}")
        return False

# ==========================================
# 𝐂𝐑𝐘𝐏𝐓𝐎 𝐅𝐔𝐍𝐂𝐓𝐈𝐎𝐍𝐒 (𝐘𝐎𝐔𝐑 𝐎𝐑𝐈𝐆𝐈𝐍𝐀𝐋)
# ==========================================

def EnC_Vr(N):
    if N < 0: return b''
    H = []
    while True:
        BesTo = N & 0x7F 
        N >>= 7
        if N: BesTo |= 0x80
        H.append(BesTo)
        if not N: break
    return bytes(H)

def CrEaTe_VarianT(field_number, value):
    field_header = (field_number << 3) | 0
    return EnC_Vr(field_header) + EnC_Vr(value)

def CrEaTe_LenGTh(field_number, value):
    field_header = (field_number << 3) | 2
    encoded_value = value.encode() if isinstance(value, str) else value
    return EnC_Vr(field_header) + EnC_Vr(len(encoded_value)) + encoded_value

def CrEaTe_ProTo(fields):
    packet = bytearray()    
    for field, value in fields.items():
        if isinstance(value, dict):
            nested_packet = CrEaTe_ProTo(value)
            packet.extend(CrEaTe_LenGTh(field, nested_packet))
        elif isinstance(value, int):
            packet.extend(CrEaTe_VarianT(field, value))           
        elif isinstance(value, str) or isinstance(value, bytes):
            packet.extend(CrEaTe_LenGTh(field, value))           
    return packet

def E_AEs(Pc):
    Z = bytes.fromhex(Pc)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    K = AES.new(key, AES.MODE_CBC, iv)
    return K.encrypt(pad(Z, AES.block_size))

def generate_exponent_number():
    exponent_digits = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    number = random.randint(1, 99999)
    number_str = f"{number:05d}"
    return ''.join(exponent_digits[digit] for digit in number_str)

def generate_random_name(base_name):
    return f"{base_name[:7]}{generate_exponent_number()}"

def generate_custom_password(prefix):
    characters = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(characters) for _ in range(5))
    return f"{prefix}_EXU_{random_part}"

def encode_string(original):
    keystream = [0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30]
    encoded = ""
    for i in range(len(original)):
        orig_byte = ord(original[i])
        key_byte = keystream[i % len(keystream)]
        result_byte = orig_byte ^ key_byte
        encoded += chr(result_byte)
    return {"open_id": original, "field_14": encoded}

def to_unicode_escaped(s):
    result = []
    for c in s:
        if 32 <= ord(c) <= 126:
            result.append(c)
        else:
            result.append(r'\u{:04x}'.format(ord(c)))
    return ''.join(result)

# 𝐀𝐏𝐈 𝐂𝐎𝐍𝐅𝐈𝐆 (𝐘𝐎𝐔𝐑 𝐎𝐑𝐈𝐆𝐈𝐍𝐀𝐋)
MAIN_HEX_KEY = "32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533"
API_POOL = [{"id": "100067", "key": bytes.fromhex(MAIN_HEX_KEY)} for _ in range(8)]

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if not IS_RENDER:
        session.proxies.update(PROXIES)
    session.verify = False
    return session

# ==========================================
# 𝐃𝐀𝐓𝐀𝐁𝐀𝐒𝐄 𝐅𝐔𝐍𝐂𝐓𝐈𝐎𝐍𝐒
# ==========================================

def save_generation_stats(user_id, username, first_name, count, real_count, fake_count, region, speed, duration):
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''INSERT INTO generation_stats 
                 (timestamp, user_id, username, first_name, count, real_accounts, fake_accounts, region, speed, duration)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (datetime.now(), user_id, username, first_name, count, real_count, fake_count, region, speed, duration))
    conn.commit()
    conn.close()

def update_user_stats(user_id, username, first_name, real_count):
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM bot_users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    
    if user:
        c.execute('''UPDATE bot_users 
                     SET last_seen = ?, total_generations = total_generations + 1,
                         total_accounts_generated = total_accounts_generated + ?,
                         total_real_accounts = total_real_accounts + ?
                     WHERE user_id = ?''',
                  (datetime.now(), real_count, real_count, user_id))
    else:
        c.execute('''INSERT INTO bot_users 
                     (user_id, username, first_name, last_seen, join_date, total_generations, total_accounts_generated, total_real_accounts)
                     VALUES (?, ?, ?, ?, ?, 1, ?, ?)''',
                  (user_id, username, first_name, datetime.now(), datetime.now(), real_count, real_count))
    
    conn.commit()
    conn.close()

def save_verified_account(uid, password, nickname, region, user_id, username, open_id):
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''INSERT INTO verified_accounts 
                 (timestamp, uid, password, nickname, region, user_id, username, open_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (datetime.now(), uid, password, nickname, region, user_id, username, open_id))
    conn.commit()
    conn.close()

def get_dashboard_stats():
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM generation_stats')
    total_gens = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(real_accounts) FROM generation_stats')
    total_real = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(fake_accounts) FROM generation_stats')
    total_fake = c.fetchone()[0] or 0
    
    c.execute('SELECT COUNT(DISTINCT user_id) FROM bot_users')
    total_users = c.fetchone()[0] or 0
    
    today = datetime.now().date()
    c.execute('SELECT SUM(real_accounts) FROM generation_stats WHERE DATE(timestamp) = ?', (today,))
    today_real = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_generations': total_gens,
        'total_real': total_real,
        'total_fake': total_fake,
        'total_users': total_users,
        'today_real': today_real
    }

# ==========================================
# 𝐅𝐋𝐀𝐒𝐊 𝐑𝐎𝐔𝐓𝐄𝐒 (𝐅𝐈𝐗𝐄𝐃 𝐅𝐎𝐑 𝐑𝐄𝐍𝐃𝐄𝐑)
# ==========================================

@app.route('/')
def dashboard():
    stats = get_dashboard_stats()
    uptime = datetime.now() - bot_stats['start_time']
    uptime_str = str(uptime).split('.')[0]
    
    # Get Render URL if available
    render_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
    
    return f"""
    <html>
    <head>
        <title>EXU CODER Dashboard</title>
        <style>
            body {{ font-family: Arial; background: #1a1a1a; color: #fff; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
            .card {{ background: #2d2d2d; padding: 20px; border-radius: 10px; border-left: 4px solid #00ff00; }}
            .value {{ font-size: 2em; font-weight: bold; color: #00ff00; }}
            .label {{ color: #888; }}
            .info {{ background: #333; padding: 10px; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔥 EXU CODER Dashboard</h1>
            <div class="info">
                <p>🌐 Running on: Render</p>
                <p>🔗 URL: {render_url}</p>
                <p>🔄 Tor: {'Disabled on Render' if IS_RENDER else 'Active'}</p>
            </div>
            <div class="stats">
                <div class="card">
                    <div class="value">{stats['total_users']}</div>
                    <div class="label">Total Users</div>
                </div>
                <div class="card">
                    <div class="value">{stats['total_generations']}</div>
                    <div class="label">Total Generations</div>
                </div>
                <div class="card">
                    <div class="value">{stats['total_real']}</div>
                    <div class="label">Real Accounts</div>
                </div>
                <div class="card">
                    <div class="value">{stats['total_fake']}</div>
                    <div class="label">Fake Accounts</div>
                </div>
                <div class="card">
                    <div class="value">{stats['today_real']}</div>
                    <div class="label">Today's Real</div>
                </div>
                <div class="card">
                    <div class="value">{uptime_str}</div>
                    <div class="label">Uptime</div>
                </div>
                <div class="card">
                    <div class="value">{len(active_generations)}</div>
                    <div class="label">Active Generations</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/api/stats')
def api_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/accounts')
def api_accounts():
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''SELECT timestamp, uid, password, nickname, region, username 
                 FROM verified_accounts ORDER BY timestamp DESC LIMIT 50''')
    accounts = c.fetchall()
    conn.close()
    
    accounts_list = []
    for acc in accounts:
        accounts_list.append({
            'timestamp': acc[0],
            'uid': acc[1],
            'password': acc[2],
            'nickname': acc[3],
            'region': acc[4],
            'username': acc[5]
        })
    
    return jsonify(accounts_list)

@app.route('/api/users')
def api_users():
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''SELECT user_id, username, first_name, last_seen, join_date,
                 total_generations, total_accounts_generated, total_real_accounts
                 FROM bot_users ORDER BY total_real_accounts DESC''')
    users = c.fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        users_list.append({
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'last_seen': user[3],
            'join_date': user[4],
            'total_generations': user[5],
            'total_accounts': user[6],
            'total_real': user[7]
        })
    
    return jsonify(users_list)

@app.route('/api/generations')
def api_generations():
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''SELECT timestamp, username, first_name, count, real_accounts, fake_accounts, region, duration
                 FROM generation_stats ORDER BY timestamp DESC LIMIT 100''')
    gens = c.fetchall()
    conn.close()
    
    gens_list = []
    for gen in gens:
        gens_list.append({
            'timestamp': gen[0],
            'username': gen[1],
            'first_name': gen[2],
            'count': gen[3],
            'real': gen[4],
            'fake': gen[5],
            'region': gen[6],
            'duration': round(gen[7], 2) if gen[7] else 0
        })
    
    return jsonify(gens_list)

@app.route('/api/active')
def api_active():
    active_list = []
    for chat_id, gen_info in active_generations.items():
        active_list.append({
            'chat_id': chat_id,
            'progress': gen_info.get('progress', 0),
            'real': gen_info.get('real', 0),
            'fake': gen_info.get('fake', 0),
            'region': gen_info.get('region', 'N/A'),
            'start_time': str(gen_info.get('start_time', ''))
        })
    return jsonify(active_list)

@app.route('/export/accounts')
def export_accounts():
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''SELECT timestamp, uid, password, nickname, region, username 
                 FROM verified_accounts ORDER BY timestamp DESC''')
    accounts = c.fetchall()
    conn.close()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Timestamp', 'UID', 'Password', 'Nickname', 'Region', 'Generated By'])
    for acc in accounts:
        cw.writerow(acc)
    
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='verified_accounts.csv')

# ==========================================
# 𝐅𝐔𝐍𝐂𝐓𝐈𝐎𝐍 𝐓𝐎 𝐑𝐔𝐍 𝐅𝐋𝐀𝐒𝐊 (𝐅𝐈𝐗𝐄𝐃 𝐅𝐎𝐑 𝐑𝐄𝐍𝐃𝐄𝐑)
# ==========================================
def run_flask():
    """Starts the Flask web server, binding to the correct host/port for Render."""
    print(f"🌐 Starting Flask dashboard on {DASHBOARD_HOST}:{DASHBOARD_PORT}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False, threaded=True)

# ==========================================
# 𝐀𝐂𝐂𝐎𝐔𝐍𝐓 𝐕𝐄𝐑𝐈𝐅𝐈𝐂𝐀𝐓𝐈𝐎𝐍
# ==========================================

def verify_guest_account(uid, password, session):
    try:
        app_id = "100067"
        url = f"https://{app_id}.connect.garena.com/oauth/guest/token/grant"
        body = {
            "uid": uid, 
            "password": password, 
            "response_type": "token",
            "client_type": "2", 
            "client_id": app_id
        }
        
        headers = {
            "User-Agent": "GarenaMSDK/4.0.19P8(ASUS_Z01QD;Android 12;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        resp = session.post(url, data=body, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if 'access_token' in data:
                return {
                    'uid': uid,
                    'password': password,
                    'is_real': True,
                    'access_token': data.get('access_token'),
                    'open_id': data.get('open_id')
                }
        return None
    except:
        return None

# ==========================================
# 𝐀𝐂𝐂𝐎𝐔𝐍𝐓 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐈𝐎𝐍
# ==========================================

def logic_create_acc(region, account_name, password_prefix, session):
    try:
        current_api = random.choice(API_POOL)
        app_id = current_api["id"]
        secret_key = current_api["key"]
        password = generate_custom_password(password_prefix)
        data = f"password={password}&client_type=2&source=2&app_id={app_id}"
        message = data.encode('utf-8')
        signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
        
        headers = {
            "User-Agent": "GarenaMSDK/4.0.19P8(ASUS_Z01QD ;Android 12;en;US;)",
            "Authorization": "Signature " + signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        url = f"https://{app_id}.connect.garena.com/oauth/guest/register"
        resp = session.post(url, headers=headers, data=data, timeout=10)
        
        if 'uid' in resp.json():
            uid = resp.json()['uid']
            return logic_token(uid, password, region, account_name, password_prefix, current_api, session)
        return None
    except:
        return None

def logic_token(uid, password, region, account_name, password_prefix, api_config, session):
    try:
        app_id = api_config["id"]
        secret_key = api_config["key"]
        url = f"https://{app_id}.connect.garena.com/oauth/guest/token/grant"
        body = {
            "uid": uid, "password": password, "response_type": "token",
            "client_type": "2", "client_secret": secret_key, "client_id": app_id
        }
        resp = session.post(url, data=body, timeout=10)
        if 'access_token' in resp.json():
            data = resp.json()
            enc = encode_string(data['open_id'])
            field = to_unicode_escaped(enc['field_14'])
            field = codecs.decode(field, 'unicode_escape').encode('latin1')
            
            return logic_major_register(data['access_token'], data['open_id'], field, uid, password, region, account_name, session)
        return None
    except:
        return None

def logic_major_register(access_token, open_id, field, uid, password, region, account_name, session):
    try:
        url = "https://loginbp.ggblueshark.com/MajorRegister"
        name = generate_random_name(account_name)
        headers = {
            "ReleaseVersion": "OB52",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
            "X-GA": "v1 1"
        }
        
        payload = {1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1, 13: 1, 14: field, 15: "en", 16: 1, 17: 1}
        payload_bytes = CrEaTe_ProTo(payload)
        encrypted = E_AEs(payload_bytes.hex())
        
        resp = session.post(url, headers=headers, data=encrypted, timeout=10)
        
        if resp.status_code == 200:
            return {
                "uid": uid, 
                "password": password, 
                "name": name, 
                "region": region,
                "access_token": access_token,
                "open_id": open_id
            }
        return None
    except:
        return None

# ==========================================
# 𝐖𝐎𝐑𝐊𝐄𝐑 𝐏𝐑𝐎𝐂𝐄𝐒𝐒
# ==========================================

def worker_process(chat_id, total, name_prefix, pass_prefix, region, message_id):
    try:
        session = get_session()
        user = bot.get_chat(chat_id)
        
        active_generations[chat_id] = {
            'progress': 0,
            'real': 0,
            'fake': 0,
            'region': region,
            'start_time': datetime.now()
        }
        
        if not IS_RENDER:
            try:
                session.get("https://check.torproject.org", timeout=5)
            except:
                bot.edit_message_text("❌ **𝐓𝐎𝐑 𝐄𝐑𝐑𝐎𝐑**\n𝐓𝐨𝐫 𝐢𝐬 𝐧𝐨𝐭 𝐫𝐮𝐧𝐧𝐢𝐧𝐠!", 
                                    chat_id, message_id, parse_mode='Markdown')
                if chat_id in active_generations:
                    del active_generations[chat_id]
                return

        real_accounts = 0
        fake_accounts = 0
        verified_accounts = []
        start_time = time.time()
        speed = user_settings.get(chat_id, {}).get('speed', 0.2)
        
        for i in range(1, total + 1):
            if chat_id in active_generations:
                active_generations[chat_id]['progress'] = int((i/total)*100)
                active_generations[chat_id]['real'] = real_accounts
                active_generations[chat_id]['fake'] = fake_accounts
            
            acc = logic_create_acc(region, name_prefix, pass_prefix, session)
            
            if acc:
                verification = verify_guest_account(acc['uid'], acc['password'], session)
                
                if verification and verification.get('is_real'):
                    real_accounts += 1
                    verified_accounts.append({
                        'uid': acc['uid'],
                        'password': acc['password'],
                        'nickname': acc['name'],
                        'region': region,
                        'open_id': verification.get('open_id', 'N/A')
                    })
                    
                    save_verified_account(
                        acc['uid'], acc['password'], acc['name'], region,
                        user.id, user.username, verification.get('open_id', 'N/A')
                    )
                    
                    if chat_id not in user_settings:
                        user_settings[chat_id] = {}
                    if 'history' not in user_settings[chat_id]:
                        user_settings[chat_id]['history'] = []
                    user_settings[chat_id]['history'].append(f"✅ {region}: {acc['uid']}")
                else:
                    fake_accounts += 1
            else:
                fake_accounts += 1
            
            if i % 10 == 0 or i == total:
                percent = (i / total) * 100
                bar = '█' * int(percent / 10) + '░' * (10 - int(percent / 10))
                elapsed = int(time.time() - start_time)
                current_speed = round(i / elapsed, 2) if elapsed > 0 else 0
                
                msg = (
                    f"⚡ **𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐈𝐍𝐆...**\n\n"
                    f"📊 **𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬:** `{bar}` {int(percent)}%\n"
                    f"✅ **𝐑𝐞𝐚𝐥:** `{real_accounts}`\n"
                    f"❌ **𝐅𝐚𝐤𝐞:** `{fake_accounts}`\n"
                    f"🚀 **𝐒𝐩𝐞𝐞𝐝:** `{current_speed} 𝐚𝐜𝐜/𝐬`\n"
                    f"⏱️ **𝐓𝐢𝐦𝐞:** `{elapsed}𝐬`"
                )
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg, parse_mode='Markdown')
                except:
                    pass
            
            time.sleep(speed)
        
        duration = time.time() - start_time
        bot_stats['total_generations'] += 1
        bot_stats['total_accounts'] += total
        bot_stats['total_real'] += real_accounts
        bot_stats['total_fake'] += fake_accounts
        
        save_generation_stats(
            user.id, user.username, user.first_name,
            total, real_accounts, fake_accounts, region, speed, duration
        )
        
        update_user_stats(user.id, user.username, user.first_name, real_accounts)
        
        if chat_id in active_generations:
            del active_generations[chat_id]
        
        if real_accounts > 0:
            summary = (
                f"✅ **𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐈𝐎𝐍 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃!**\n\n"
                f"📊 **𝐒𝐮𝐦𝐦𝐚𝐫𝐲:**\n"
                f"   • **𝐓𝐨𝐭𝐚𝐥:** {total}\n"
                f"   • **✅ 𝐑𝐞𝐚𝐥:** {real_accounts}\n"
                f"   • **❌ 𝐅𝐚𝐤𝐞:** {fake_accounts}\n"
                f"   • **🌍 𝐑𝐞𝐠𝐢𝐨𝐧:** {region}\n"
                f"   • **⏱️ 𝐓𝐢𝐦𝐞:** {int(duration)}s\n"
            )
            
            if total >= 100:
                filename = f"EXU_ACCOUNTS_{region}_{random.randint(1000,9999)}.json"
                
                json_data = {
                    "generation_info": {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "total_requested": total,
                        "real_accounts": real_accounts,
                        "fake_accounts": fake_accounts,
                        "region": region,
                        "generated_by": user.username or user.first_name,
                        "user_id": user.id
                    },
                    "accounts": verified_accounts
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                with open(filename, 'rb') as f:
                    bot.send_document(
                        chat_id, 
                        f, 
                        caption=summary + f"\n📁 **𝐅𝐢𝐥𝐞:** {filename}\n📦 **𝐅𝐨𝐫𝐦𝐚𝐭:** JSON",
                        parse_mode='Markdown'
                    )
                
                os.remove(filename)
                bot.delete_message(chat_id, message_id)
            
            else:
                result_text = summary + "\n📋 **𝐕𝐞𝐫𝐢𝐟𝐢𝐞𝐝 𝐀𝐜𝐜𝐨𝐮𝐧𝐭𝐬:**\n\n"
                
                for idx, acc in enumerate(verified_accounts, 1):
                    result_text += f"**𝐀𝐜𝐜𝐨𝐮𝐧𝐭 #{idx}**\n"
                    result_text += f"   ├─ **𝐔𝐈𝐃:** `{acc['uid']}`\n"
                    result_text += f"   ├─ **𝐏𝐚𝐬𝐬:** `{acc['password']}`\n"
                    result_text += f"   ├─ **𝐍𝐢𝐜𝐤:** {acc['nickname']}\n"
                    result_text += f"   └─ **𝐒𝐭𝐚𝐭𝐮𝐬:** ✅ 𝐑𝐄𝐀𝐋\n\n"
                
                if len(result_text) > 4000:
                    parts = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
                    for part in parts:
                        bot.send_message(chat_id, part, parse_mode='Markdown')
                else:
                    bot.send_message(chat_id, result_text, parse_mode='Markdown')
                
                bot.delete_message(chat_id, message_id)
        else:
            bot.edit_message_text(
                f"❌ **𝐅𝐀𝐈𝐋𝐄𝐃!**\n\n"
                f"📊 **𝐑𝐞𝐬𝐮𝐥𝐭𝐬:**\n"
                f"   • **𝐓𝐨𝐭𝐚𝐥:** {total}\n"
                f"   • **✅ 𝐑𝐞𝐚𝐥:** 0\n"
                f"   • **❌ 𝐅𝐚𝐤𝐞:** {fake_accounts}\n\n"
                f"💡 **𝐓𝐢𝐩:** Try different region or slower speed", 
                chat_id, message_id, parse_mode='Markdown'
            )
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ **𝐄𝐫𝐫𝐨𝐫:** {str(e)}", parse_mode='Markdown')
        if chat_id in active_generations:
            del active_generations[chat_id]

# ==========================================
# 𝐁𝐎𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    is_owner = (user_id == OWNER_ID)
    
    render_msg = " (Render Cloud)" if IS_RENDER else ""
    
    welcome_text = (
        f"🔥 **𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐁𝐎𝐓{render_msg}** 🔥\n\n"
        f"👋 **𝐖𝐞𝐥𝐜𝐨𝐦𝐞 {message.from_user.first_name}!**\n"
        f"🆔 **𝐈𝐃:** `{user_id}`\n"
        f"⚡ **𝐒𝐭𝐚𝐭𝐮𝐬:** 𝐎𝐧𝐥𝐢𝐧𝐞\n"
        f"🛡️ **𝐏𝐫𝐨𝐭𝐞𝐜𝐭𝐢𝐨𝐧:** {'𝐓𝐎𝐑 𝐃𝐢𝐬𝐚𝐛𝐥𝐞𝐝 (𝐑𝐞𝐧𝐝𝐞𝐫)' if IS_RENDER else '𝐓𝐎𝐑 𝐀𝐜𝐭𝐢𝐯𝐞'}\n\n"
        f"👇 **𝐔𝐬𝐞 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐛𝐞𝐥𝐨𝐰:**"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=create_main_keyboard(is_owner)
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_owner = (user_id == OWNER_ID)
    
    if text == BUTTONS['generate']:
        msg = bot.send_message(chat_id, "🔢 **𝐇𝐨𝐰 𝐦𝐚𝐧𝐲 𝐚𝐜𝐜𝐨𝐮𝐧𝐭𝐬?**\n(𝐄𝐧𝐭𝐞𝐫 𝐧𝐮𝐦𝐛𝐞𝐫 1-1000)", parse_mode='Markdown')
        bot.register_next_step_handler(msg, step_count)
        
    elif text == BUTTONS['history']:
        history = user_settings.get(user_id, {}).get('history', [])
        if history:
            history_text = "📊 **𝐘𝐨𝐮𝐫 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧 𝐇𝐢𝐬𝐭𝐨𝐫𝐲:**\n\n"
            for h in history[-10:]:
                history_text += f"• {h}\n"
        else:
            history_text = "📊 **𝐍𝐨 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧 𝐡𝐢𝐬𝐭𝐨𝐫𝐲 𝐲𝐞𝐭.**"
        bot.send_message(chat_id, history_text, parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
        
    elif text == BUTTONS['profile']:
        user = message.from_user
        profile_text = (
            f"👤 **𝐔𝐬𝐞𝐫 𝐏𝐫𝐨𝐟𝐢𝐥𝐞**\n\n"
            f"**𝐍𝐚𝐦𝐞:** {user.first_name}\n"
            f"**𝐈𝐃:** `{user.id}`\n"
            f"**𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞:** @{user.username if user.username else 'None'}\n"
            f"**𝐋𝐚𝐧𝐠:** {user.language_code}"
        )
        bot.send_message(chat_id, profile_text, parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
        
    elif text == BUTTONS['settings']:
        bot.send_message(chat_id, "⚙️ **𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬 𝐌𝐞𝐧𝐮**", parse_mode='Markdown', reply_markup=create_settings_keyboard())
        
    elif text == BUTTONS['help']:
        help_text = (
            "❓ **𝐇𝐞𝐥𝐩 𝐌𝐞𝐧𝐮**\n\n"
            "**𝐇𝐨𝐰 𝐭𝐨 𝐮𝐬𝐞:**\n"
            "1. 𝐂𝐥𝐢𝐜𝐤 '𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄'\n"
            "2. 𝐄𝐧𝐭𝐞𝐫 𝐧𝐮𝐦𝐛𝐞𝐫 𝐨𝐟 𝐚𝐜𝐜𝐨𝐮𝐧𝐭𝐬 (1-1000)\n"
            "3. 𝐄𝐧𝐭𝐞𝐫 𝐧𝐚𝐦𝐞 𝐩𝐫𝐞𝐟𝐢𝐱\n"
            "4. 𝐄𝐧𝐭𝐞𝐫 𝐩𝐚𝐬𝐬𝐰𝐨𝐫𝐝 𝐩𝐫𝐞𝐟𝐢𝐱\n"
            "5. 𝐒𝐞𝐥𝐞𝐜𝐭 𝐫𝐞𝐠𝐢𝐨𝐧\n\n"
            "📁 **𝐅𝐨𝐫 100+ 𝐚𝐜𝐜𝐨𝐮𝐧𝐭𝐬:** JSON file will be sent\n"
            "📝 **𝐅𝐨𝐫 < 100 𝐚𝐜𝐜𝐨𝐮𝐧𝐭𝐬:** Text message with details\n\n"
            "✅ **𝐑𝐞𝐚𝐥 𝐀𝐜𝐜𝐨𝐮𝐧𝐭𝐬:** Verified with token\n"
            "❌ **𝐅𝐚𝐤𝐞 𝐀𝐜𝐜𝐨𝐮𝐧𝐭𝐬:** Filtered out\n\n"
            "📞 **𝐂𝐨𝐧𝐭𝐚𝐜𝐭:** @EXUcoder"
        )
        bot.send_message(chat_id, help_text, parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
        
    elif text == BUTTONS['status']:
        stats = get_dashboard_stats()
        status_text = (
            "📈 **𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐮𝐬**\n\n"
            f"✅ **𝐁𝐨𝐭:** 𝐑𝐮𝐧𝐧𝐢𝐧𝐠\n"
            f"🔄 **𝐓𝐨𝐫:** {'𝐃𝐢𝐬𝐚𝐛𝐥𝐞𝐝 (𝐑𝐞𝐧𝐝𝐞𝐫)' if IS_RENDER else '𝐀𝐜𝐭𝐢𝐯𝐞'}\n"
            f"✅ **𝐕𝐞𝐫𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧:** 𝐀𝐜𝐭𝐢𝐯𝐞\n"
            f"👥 **𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬:** {stats['total_users']}\n"
            f"📊 **𝐓𝐨𝐭𝐚𝐥 𝐆𝐞𝐧𝐬:** {stats['total_generations']}\n"
            f"✅ **𝐓𝐨𝐭𝐚𝐥 𝐑𝐞𝐚𝐥:** {stats['total_real']}\n"
            f"📈 **𝐓𝐨𝐝𝐚𝐲 𝐑𝐞𝐚𝐥:** {stats['today_real']}"
        )
        bot.send_message(chat_id, status_text, parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
        
    elif text == BUTTONS['restart']:
        msg = bot.send_message(chat_id, "🔄 **𝐑𝐞𝐬𝐭𝐚𝐫𝐭 𝐛𝐨𝐭?**", parse_mode='Markdown', reply_markup=create_confirm_keyboard())
        bot.register_next_step_handler(msg, process_restart)
        
    elif text == BUTTONS['owner'] and is_owner:
        render_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
        owner_text = f"👑 **𝐎𝐰𝐧𝐞𝐫 𝐏𝐚𝐧𝐞𝐥**\n\n**𝐁𝐨𝐭 𝐢𝐬 𝐫𝐮𝐧𝐧𝐢𝐧𝐠 𝐬𝐦𝐨𝐨𝐭𝐡𝐥𝐲!**\n\n🌐 **𝐃𝐚𝐬𝐡𝐛𝐨𝐚𝐫𝐝:** {render_url}"
        bot.send_message(chat_id, owner_text, parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
    
    elif text == BUTTONS['set_region']:
        bot.send_message(chat_id, "🌍 **𝐒𝐞𝐥𝐞𝐜𝐭 𝐑𝐞𝐠𝐢𝐨𝐧:**", parse_mode='Markdown', reply_markup=create_region_keyboard())
        
    elif text == BUTTONS['set_speed']:
        bot.send_message(chat_id, "⚡ **𝐒𝐞𝐥𝐞𝐜𝐭 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧 𝐒𝐩𝐞𝐞𝐝:**", parse_mode='Markdown', reply_markup=create_speed_keyboard())
        
    elif text == BUTTONS['set_prefix']:
        msg = bot.send_message(chat_id, "🔑 **𝐄𝐧𝐭𝐞𝐫 𝐧𝐞𝐰 𝐩𝐚𝐬𝐬𝐰𝐨𝐫𝐝 𝐩𝐫𝐞𝐟𝐢𝐱:**", parse_mode='Markdown')
        bot.register_next_step_handler(msg, set_password_prefix)
        
    elif text == BUTTONS['back_main']:
        bot.send_message(chat_id, "🏠 **𝐌𝐚𝐢𝐧 𝐌𝐞𝐧𝐮**", parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
    
    elif text in [BUTTONS['region_ind'], BUTTONS['region_bd'], BUTTONS['region_sg'], 
                  BUTTONS['region_eu'], BUTTONS['region_ru'], BUTTONS['region_br'],
                  BUTTONS['region_us'], BUTTONS['region_uk']]:
        region_map = {
            BUTTONS['region_ind']: 'IND', BUTTONS['region_bd']: 'BD', BUTTONS['region_sg']: 'SG',
            BUTTONS['region_eu']: 'EU', BUTTONS['region_ru']: 'RU', BUTTONS['region_br']: 'BR',
            BUTTONS['region_us']: 'USA', BUTTONS['region_uk']: 'UK'
        }
        selected_region = region_map.get(text, 'IND')
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['region'] = selected_region
        bot.send_message(chat_id, f"✅ **𝐑𝐞𝐠𝐢𝐨𝐧 𝐬𝐞𝐭 𝐭𝐨 {selected_region}!**", parse_mode='Markdown', reply_markup=create_settings_keyboard())
    
    elif text in [BUTTONS['speed_ultra'], BUTTONS['speed_fast'], BUTTONS['speed_medium'],
                  BUTTONS['speed_slow'], BUTTONS['speed_safe']]:
        speed_map = {
            BUTTONS['speed_ultra']: 0.1, BUTTONS['speed_fast']: 0.2,
            BUTTONS['speed_medium']: 0.5, BUTTONS['speed_slow']: 1.0,
            BUTTONS['speed_safe']: 2.0
        }
        selected_speed = speed_map.get(text, 0.2)
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['speed'] = selected_speed
        speed_name = text.split(' ')[1]
        bot.send_message(chat_id, f"✅ **𝐒𝐩𝐞𝐞𝐝 𝐬𝐞𝐭 𝐭𝐨 {speed_name}!**", parse_mode='Markdown', reply_markup=create_settings_keyboard())
    
    elif text == BUTTONS['confirm_yes']:
        bot.send_message(chat_id, "✅ **𝐀𝐜𝐭𝐢𝐨𝐧 𝐜𝐨𝐧𝐟𝐢𝐫𝐦𝐞𝐝!**", parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))
        
    elif text == BUTTONS['confirm_no'] or text == BUTTONS['cancel']:
        bot.send_message(chat_id, "❌ **𝐀𝐜𝐭𝐢𝐨𝐧 𝐜𝐚𝐧𝐜𝐞𝐥𝐞𝐝!**", parse_mode='Markdown', reply_markup=create_main_keyboard(is_owner))

def process_restart(message):
    if message.text == BUTTONS['confirm_yes']:
        bot.send_message(message.chat.id, "🔄 **𝐑𝐞𝐬𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐛𝐨𝐭...**", parse_mode='Markdown')
        time.sleep(1)
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, "❌ **𝐑𝐞𝐬𝐭𝐚𝐫𝐭 𝐜𝐚𝐧𝐜𝐞𝐥𝐞𝐝**", parse_mode='Markdown', 
                        reply_markup=create_main_keyboard(message.from_user.id == OWNER_ID))

def set_password_prefix(message):
    user_id = message.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]['password_prefix'] = message.text
    bot.send_message(message.chat.id, f"✅ **𝐏𝐚𝐬𝐬𝐰𝐨𝐫𝐝 𝐩𝐫𝐞𝐟𝐢𝐱 𝐬𝐞𝐭 𝐭𝐨:** `{message.text}`", 
                    parse_mode='Markdown', reply_markup=create_settings_keyboard())

def step_count(message):
    try:
        count = int(message.text)
        if count <= 0 or count > 1000:
            bot.send_message(message.chat.id, "❌ **𝐏𝐥𝐞𝐚𝐬𝐞 𝐞𝐧𝐭𝐞𝐫 𝐚 𝐧𝐮𝐦𝐛𝐞𝐫 𝐛𝐞𝐭𝐰𝐞𝐞𝐧 1-1000**", parse_mode='Markdown')
            return
        user_data[message.chat.id] = {'count': count}
        msg = bot.send_message(message.chat.id, "👤 **𝐄𝐧𝐭𝐞𝐫 𝐧𝐚𝐦𝐞 𝐩𝐫𝐞𝐟𝐢𝐱:**\n(𝐞.𝐠. EXU)", parse_mode='Markdown')
        bot.register_next_step_handler(msg, step_name)
    except ValueError:
        bot.send_message(message.chat.id, "❌ **𝐏𝐥𝐞𝐚𝐬𝐞 𝐞𝐧𝐭𝐞𝐫 𝐚 𝐯𝐚𝐥𝐢𝐝 𝐧𝐮𝐦𝐛𝐞𝐫**", parse_mode='Markdown')

def step_name(message):
    user_data[message.chat.id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "🔑 **𝐄𝐧𝐭𝐞𝐫 𝐩𝐚𝐬𝐬𝐰𝐨𝐫𝐝 𝐩𝐫𝐞𝐟𝐢𝐱:**\n(𝐞.𝐠. EXUPASS)", parse_mode='Markdown')
    bot.register_next_step_handler(msg, step_pass)

def step_pass(message):
    user_data[message.chat.id]['pass'] = message.text
    bot.send_message(message.chat.id, "🌍 **𝐒𝐞𝐥𝐞𝐜𝐭 𝐫𝐞𝐠𝐢𝐨𝐧:**", 
                    parse_mode='Markdown', reply_markup=create_inline_region_buttons())

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data.startswith('reg_'):
        region_map = {
            'reg_ind': 'IND', 'reg_bd': 'BD', 'reg_sg': 'SG',
            'reg_eu': 'EU', 'reg_ru': 'RU', 'reg_br': 'BR',
            'reg_us': 'USA', 'reg_uk': 'UK', 'reg_jp': 'JP'
        }
        region = region_map.get(data, 'IND')
        
        if chat_id in user_data:
            count = user_data[chat_id]['count']
            name = user_data[chat_id]['name']
            pasw = user_data[chat_id]['pass']
            
            bot.answer_callback_query(call.id, f"✅ Region {region} selected!")
            bot.edit_message_text(f"⚡ **𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐠𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧...**\n\n🌍 **𝐑𝐞𝐠𝐢𝐨𝐧:** {region}\n🎯 **𝐓𝐚𝐫𝐠𝐞𝐭:** {count}\n📁 **𝐎𝐮𝐭𝐩𝐮𝐭:** {'JSON file' if count >= 100 else 'Text message'}", 
                                 chat_id, call.message.message_id, parse_mode='Markdown')
            
            status_msg = bot.send_message(chat_id, "⏳ **𝐈𝐧𝐢𝐭𝐢𝐚𝐥𝐢𝐳𝐢𝐧𝐠...**", parse_mode='Markdown')
            threading.Thread(target=worker_process, args=(chat_id, count, name, pasw, region, status_msg.message_id)).start()
            
            del user_data[chat_id]
        else:
            bot.answer_callback_query(call.id, "❌ Session expired! Please start again.")
            
    elif data == 'back_main':
        bot.answer_callback_query(call.id)
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "🏠 **𝐌𝐚𝐢𝐧 𝐌𝐞𝐧𝐮**", 
                        reply_markup=create_main_keyboard(call.from_user.id == OWNER_ID))

# ==========================================
# 𝐌𝐀𝐈𝐍 𝐒𝐓𝐀𝐑𝐓𝐔𝐏
# ==========================================

if __name__ == "__main__":
    print("🤖 EXU CODER BOT STARTING...")
    print("🔄 Starting Tor service...")
    
    if IS_RENDER:
        print("✅ Running on Render - Tor disabled")
        print("🚀 Bot is live! Press Ctrl+C to stop.")
        print("✅ Account verification is ACTIVE")
        render_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
        print(f"🌐 Web Dashboard: {render_url}")
        print("📁 Large batches (100+ accounts) will be sent as JSON files")
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        try:
            bot.infinity_polling(skip_pending=True)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif start_tor_service():
        print("✅ Tor is running")
        print("🚀 Bot is live! Press Ctrl+C to stop.")
        print("✅ Account verification is ACTIVE")
        print(f"🌐 Web Dashboard: http://localhost:{DASHBOARD_PORT}")
        print("📁 Large batches (100+ accounts) will be sent as JSON files")
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        try:
            bot.infinity_polling(skip_pending=True)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Failed to start Tor. Starting without Tor...")
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        try:
            bot.infinity_polling(skip_pending=True)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
