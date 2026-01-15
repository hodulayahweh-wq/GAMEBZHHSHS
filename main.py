import telebot
import os
import re
import threading
import json
import io
import pandas as pd
from flask import Flask, Response, request, jsonify

# ================= AYARLAR =================
TOKEN = "8173921081:AAE-YxozU3YZzKM3Uf4UnfUTUEwLNIbjg6E"
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
        # Her türlü veriyi temizle ve listeye çevir
        return [re.sub(r'[^\w\s\d:|\-.,@]', '', line).strip() for line in lines if line.strip()]
    except:
        return content.splitlines()

# ================= HAYALET ANA SAYFA =================
@app.route('/')
def home():
    return f"<h2>> MULTI-INTEL NODE: ACTIVE</h2><p>> LOADED_DATABASES: {len(api_database)}</p>"

# ================= EVRENSEL AKILLI ARAMA API'Sİ =================
@app.route('/api/v1/search/<path:filename>')
def universal_search(filename):
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Sorgu bos olamaz"}), 400
    
    # İlgili veritabanını seç
    data_list = api_database.get(filename.lower())
    if not data_list:
        return jsonify({"error": "Veri bulunamadi veya sunucu resetlendi"}), 404

    # AKILLI AYIRIM: GSM/TC mi yoksa Metin mi?
    clean_query = query.replace(" ", "")
    
    if clean_query.isdigit():
        # Sayısal veri (GSM/TC/ID) -> Tek sonuç için tara
        for line in data_list:
            if clean_query in line.replace(" ", ""):
                return Response(line, mimetype='text/plain')
        return "Kayit bulunamadi.", 404
    else:
        # Metinsel veri (Ad Soyad/Adres) -> Kelime bazlı ara ve max 10 sonuç ver
        query_parts = query.lower().split()
        results = []
        for line in data_list:
            if all(part in line.lower() for part in query_parts):
                results.append(line)
                if len(results) == 10: break
        
        if results:
            return Response("\n".join(results), mimetype='text/plain')
        return "Eslesme bulunamadi.", 404

# ================= TELEGRAM BOT =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🏁 **UNIVERSAL INTEL ENGINE v7.0**\n\nHer türlü veriyi (TXT, JSON, CSV) atabilirsin. Bot hepsini otomatik tanır ve akıllı arama API'sine dönüştürür.")

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    raw_name = m.document.file_name
    ext = os.path.splitext(raw_name)[1].lower()
    
    if ext not in ['.txt', '.json', '.py', '.csv']:
        return bot.reply_to(m, "❌ Format desteklenmiyor.")

    msg = bot.reply_to(m, f"⚙️ `{raw_name}` **isleniyor...**")
    
    try:
        # Dosya adını URL uyumlu ID'ye çevir
        db_id = re.sub(r'\W+', '_', os.path.splitext(raw_name)[0]).lower()
        
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8', errors='ignore')
        
        # Veriyi belleğe al
        api_database[db_id] = process_any_file(content, ext)
        
        search_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{db_id}?q="

        bot.edit_message_text(
            f"✅ **YENI NODE HAZIR**\n\n"
            f"📁 **Veritabani:** `{db_id}`\n"
            f"🔍 **Akilli Sorgu:**\n`{search_url}SORGU`\n\n"
            f"💎 *Bu link artik her turlu veri tipinde (Ad-Soyad veya GSM) calisir.*",
            m.chat.id, msg.message_id, disable_web_page_preview=True
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Hata: {str(e)}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
