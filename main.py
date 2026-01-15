import telebot
import os
import re
import threading
import json
import io
import pandas as pd
from flask import Flask, Response, request, jsonify

# ================= AYARLAR =================
TOKEN = "8173921081:AAFX7vtywKCMEupTwOI5qewDgYqaQ6yRQlM"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# TÜM VERİLERİN TUTULDUĞU MERKEZİ BELLEK
api_database = {}

# ================= EVRENSEL TEMİZLİK VE İNDEKSLEME =================
def process_any_file(content, extension):
    try:
        if extension == '.json':
            data = json.loads(content)
            text_content = json.dumps(data, indent=2, ensure_ascii=False)
        elif extension == '.csv':
            df = pd.read_csv(io.StringIO(content))
            text_content = df.to_string(index=False)
        else:
            text_content = content
        
        lines = text_content.splitlines()
        # Veriyi temizle ve listeye çevir (Gereksiz karakterleri ayıklar)
        return [re.sub(r'[^\w\s\d:|\-.,@]', '', line).strip() for line in lines if line.strip()]
    except:
        return content.splitlines()

# ================= HAYALET ANA SAYFA =================
@app.route('/')
def home():
    # Render incelemesi için masum ama senin için bilgi dolu sayfa
    db_list = "".join([f"<li>Node: {k} (Active)</li>" for k in api_database.keys()])
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <h2>> MULTI-INTEL NODE: ONLINE</h2>
        <p>> LOADED_DATABASES: {len(api_database)}</p>
        <ul>{db_list}</ul>
        <hr>
        <p style="color:#333;">Secure connection established. No logs stored.</p>
    </body>
    """

# ================= EVRENSEL AKILLI ARAMA API'Sİ =================
@app.route('/api/v1/search/<path:filename>')
def universal_search(filename):
    query = request.args.get('q', '').strip()
    if not query:
        return Response("HATA: Sorgu parametresi bos (?q=...)", mimetype='text/plain'), 400
    
    data_list = api_database.get(filename.lower())
    if not data_list:
        return Response("HATA: Veri bulunamadi veya sunucu resetlendi.", mimetype='text/plain'), 404

    # AKILLI AYIRIM
    clean_query = query.replace(" ", "")
    
    if clean_query.isdigit():
        # Sayısal veri (GSM/TC/ID) -> Tek sonuç
        for line in data_list:
            if clean_query in line.replace(" ", ""):
                return Response(line, mimetype='text/plain')
        return Response("Kayit bulunamadi.", mimetype='text/plain'), 404
    else:
        # Metinsel veri (Ad Soyad) -> Kelime bazlı ara ve max 10 sonuç
        query_parts = query.lower().split()
        results = []
        for line in data_list:
            if all(part in line.lower() for part in query_parts):
                results.append(line)
                if len(results) == 10: break
        
        if results:
            # Verileri alt alta tertemiz basar
            return Response("\n".join(results), mimetype='text/plain')
        return Response("Eslesme bulunamadi.", mimetype='text/plain'), 404

# ================= TELEGRAM BOT KOMUTLARI =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🏁 **UNIVERSAL INTEL ENGINE v7.5**\n\nVeri dosyalarını at, API anında oluşsun.\n\n📜 `/liste` - Aktif API'leri gör.")

@bot.message_handler(commands=['liste'])
def list_db(m):
    if not api_database:
        return bot.reply_to(m, "📭 Şu an yüklü veri yok sevgilim.")
    
    text = "📂 **AKTİF APİ LİSTESİ**\n━━━━━━━━━━━━━━\n"
    for db_id in api_database.keys():
        url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{db_id}?q="
        text += f"📍 `{db_id}`\n🔗 [Link]({url})\n\n"
    bot.send_message(m.chat.id, text, disable_web_page_preview=True)

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    raw_name = m.document.file_name
    ext = os.path.splitext(raw_name)[1].lower()
    
    if ext not in ['.txt', '.json', '.py', '.csv']:
        return bot.reply_to(m, "❌ Format desteklenmiyor.")

    msg = bot.reply_to(m, f"⚙️ `{raw_name}` **işleniyor...**")
    
    try:
        db_id = re.sub(r'\W+', '_', os.path.splitext(raw_name)[0]).lower()
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8', errors='ignore')
        
        api_database[db_id] = process_any_file(content, ext)
        
        search_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{db_id}?q="

        bot.edit_message_text(
            f"✅ **NODE AKTİF EDİLDİ**\n\n"
            f"📁 **ID:** `{db_id}`\n"
            f"🔍 **Sorgu:** `{search_url}SORGU`\n\n"
            f"💎 *Tarayıcıda artık veriler alt alta tertemiz görünecek.*",
            m.chat.id, msg.message_id, disable_web_page_preview=True
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Hata: {str(e)}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
