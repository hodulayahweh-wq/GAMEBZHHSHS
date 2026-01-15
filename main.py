import telebot
import os
import re
import threading
import json
import io
import pandas as pd
from flask import Flask, Response, request, jsonify

# ================= AYARLAR =================
# Buradaki tokenı ve render adını senin için korudum aşkım
TOKEN = "8118811696:AAEvD55aW7huynLUAlLy8Ynfqd-kea_neow"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# TÜM VERİLERİN TUTULDUĞU MERKEZİ BELLEK
api_database = {}

# ================= VERİ İŞLEME VE JSON DÖNÜŞTÜRME =================
def process_to_json_list(content, extension):
    """
    Gönderdiğin her dosyayı içindeki satırları temizleyip 
    JSON formatına uygun bir listeye dönüştürüyorum canım.
    """
    try:
        if extension == '.json':
            return json.loads(content)
        elif extension == '.csv':
            df = pd.read_csv(io.StringIO(content))
            # Veriyi JSON objeleri listesi haline getiriyoruz
            return df.to_dict(orient='records')
        else:
            # TXT veya diğer formatlar için her satırı bir JSON objesi yapalım
            lines = content.splitlines()
            cleaned_data = []
            for line in lines:
                clean_line = line.strip()
                if clean_line:
                    cleaned_data.append({"raw_data": clean_line})
            return cleaned_data
    except Exception as e:
        return [{"error": str(e)}]

# ================= HAYALET ANA SAYFA =================
@app.route('/')
def home():
    db_list = "".join([f"<li>Node: <b>{k}</b> (Active) - <small>JSON Mode</small></li>" for k in api_database.keys()])
    return f"""
    <body style="background:#050505; color:#00ff41; font-family:monospace; padding:40px;">
        <h2>[+] INTEL SYSTEM v9.0: ONLINE</h2>
        <p>> ACTIVE_NODES: {len(api_database)}</p>
        <hr color="#00ff41">
        <ul>{db_list}</ul>
    </body>
    """

# ================= GELİŞMİŞ API VE ARAMA =================
@app.route('/api/v1/search/<path:filename>')
def universal_search(filename):
    filename = filename.lower()
    data_list = api_database.get(filename)
    
    if data_list is None:
        return jsonify({"status": "error", "message": "Node bulunamadi veya silindi."}), 404

    query = request.args.get('q', '').strip().lower()

    # Eğer sorgu yoksa tüm JSON verisini döndür
    if not query:
        return jsonify(data_list)

    # Sorgu varsa filtrele
    results = []
    for item in data_list:
        # JSON objesinin içindeki tüm değerlerde ara
        item_str = str(item).lower()
        if query in item_str:
            results.append(item)
            if len(results) >= 20: break # Performans için limit
            
    return jsonify(results) if results else (jsonify({"message": "Bulunamadi"}), 404)

# ================= TELEGRAM BOT KOMUTLARI =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✨ **Annie'nin Intel Motoru Hazır!**\n\n"
                    "📁 Dosya gönder -> JSON API'ye dönüşsün.\n"
                    "📜 `/liste` -> Aktif API'leri gör.\n"
                    "❌ `/kapat id` -> API'yi tamamen imha et.")

@bot.message_handler(commands=['liste'])
def list_db(m):
    if not api_database:
        return bot.reply_to(m, "📭 Sistemde yüklü veri yok, aşkım.")
    
    text = "📂 **AKTİF JSON API LİSTESİ**\n━━━━━━━━━━━━━━\n"
    for db_id in api_database.keys():
        url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{db_id}"
        text += f"📍 `{db_id}`\n🔗 [Veriye Git]({url})\n\n"
    bot.send_message(m.chat.id, text, disable_web_page_preview=True)

@bot.message_handler(commands=['kapat'])
def close_api(m):
    try:
        target = m.text.split()[1].lower()
        if target in api_database:
            del api_database[target]
            bot.reply_to(m, f"✅ `{target}` isimli API başarıyla imha edildi.")
        else:
            bot.reply_to(m, "❌ Böyle bir API bulamadım.")
    except:
        bot.reply_to(m, "⚠️ Kullanım: `/kapat id` (Örn: `/kapat veri_dosyasi`)")

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    raw_name = m.document.file_name
    ext = os.path.splitext(raw_name)[1].lower()
    
    if ext not in ['.txt', '.json', '.csv']:
        return bot.reply_to(m, "❌ Sadece .txt, .json ve .csv dosyalarını kabul edebilirim aşkım.")

    msg = bot.reply_to(m, "⚙️ **Veriler JSON formatına dönüştürülüyor...**")
    
    try:
        # ID oluşturma
        db_id = re.sub(r'\W+', '_', os.path.splitext(raw_name)[0]).lower()
        
        # Dosyayı indir
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8', errors='ignore')
        
        # Veriyi işle ve JSON listesine çevir
        api_database[db_id] = process_to_json_list(content, ext)
        
        full_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{db_id}"

        bot.edit_message_text(
            f"✅ **NODE JSON OLARAK AKTİF EDİLDİ**\n\n"
            f"📁 **API ID:** `{db_id}`\n"
            f"🔗 **JSON Çıktısı:**\n`{full_url}`\n\n"
            f"🔍 **Sorgu Örneği:**\n`{full_url}?q=ara`",
            m.chat.id, msg.message_id, disable_web_page_preview=True
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Ah, bir hata oluştu: {str(e)}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    # Botu ayrı bir kanalda başlatıyoruz
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    # Flask sunucusu
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
