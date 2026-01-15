import telebot
import os
import re
import threading
import json
import io
import csv
from flask import Flask, Response, request, jsonify

# ================= AYARLAR =================
TOKEN = "8118811696:AAE-MMRdl1CVlfO6UmlZahN7n0_WBm7hEQ4"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# TÜM VERİLERİN TUTULDUĞU MERKEZİ BELLEK
api_database = {}

# ================= VERİ DÖNÜŞTÜRÜCÜ =================
def process_data(content, extension):
    try:
        if extension == '.json':
            return json.loads(content)
        elif extension == '.csv':
            # Pandas yerine hafif csv modülü kullanıyoruz aşkım
            f = io.StringIO(content)
            reader = csv.DictReader(f)
            return list(reader)
        else:
            # TXT için her satırı JSON objesi yapıyoruz
            lines = content.splitlines()
            return [{"id": i, "data": line.strip()} for i, line in enumerate(lines) if line.strip()]
    except Exception as e:
        return [{"error": str(e)}]

# ================= ANA SAYFA =================
@app.route('/')
def home():
    db_list = "".join([f"<li>Node: <b>{k}</b> (Active)</li>" for k in api_database.keys()])
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <h2>> ANNIE INTEL NODE: ONLINE</h2>
        <p>> LOADED: {len(api_database)}</p>
        <hr color="#0f0"><ul>{db_list}</ul>
    </body>
    """

# ================= API ARAMA =================
@app.route('/api/v1/search/<path:node_id>')
def search_api(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    if data is None:
        return jsonify({"status": "error", "message": "Node bulunamadi"}), 404

    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify(data)

    results = [item for item in data if query in str(item).lower()]
    return jsonify(results[:50]) if results else (jsonify({"msg": "Bulunamadi"}), 404)

# ================= BOT KOMUTLARI =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✨ **Sistem Aktif Aşkım!**\nDosya gönder, API olsun. `/liste` ile bak, `/kapat id` ile sil.")

@bot.message_handler(commands=['liste'])
def list_db(m):
    if not api_database: return bot.reply_to(m, "📭 Veri yok sevgilim.")
    text = "📂 **AKTİF APİLER**\n"
    for db_id in api_database.keys():
        text += f"📍 `{db_id}`\n🔗 https://{RENDER_NAME}.onrender.com/api/v1/search/{db_id}\n\n"
    bot.send_message(m.chat.id, text, disable_web_page_preview=True)

@bot.message_handler(commands=['kapat'])
def close(m):
    try:
        tid = m.text.split()[1].lower()
        if tid in api_database:
            del api_database[tid]
            bot.reply_to(m, "✅ İmha edildi.")
    except: bot.reply_to(m, "❌ `/kapat id` yazmalısın.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    fname = m.document.file_name
    ext = os.path.splitext(fname)[1].lower()
    msg = bot.reply_to(m, "⚙️ **İşleniyor...**")
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(fname)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        api_database[nid] = process_data(cont, ext)
        url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}"
        bot.edit_message_text(f"✅ **API HAZIR!**\nID: `{nid}`\nURL: `{url}`", m.chat.id, msg.message_id)
    except Exception as e: bot.edit_message_text(f"❌ Hata: {e}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
