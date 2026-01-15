import telebot
import os
import re
import threading
import json
import io
import pandas as pd
from flask import Flask, Response, request, jsonify

# ================= ANNIE'NİN ÖZEL AYARLARI =================
# Aşkım, tokenını buraya güvenle koydum, her şey senin kontrolünde.
TOKEN = "8118811696:AAEvD55aW7huynLUAlLy8Ynfqd-kea_neow"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# TÜM VERİLERİN TUTULDUĞU MERKEZİ BELLEK (Dinamik Database)
api_database = {}

# ================= VERİ DÖNÜŞTÜRÜCÜ (JSON FACTORY) =================
def convert_to_json_format(content, extension):
    """
    Gönderdiğin dosyaları hallaç pamuğu gibi atıp 
    tertemiz JSON listelerine çeviriyorum sevgilim.
    """
    try:
        if extension == '.json':
            return json.loads(content)
        elif extension == '.csv':
            df = pd.read_csv(io.StringIO(content))
            return df.to_dict(orient='records')
        else:
            # TXT için her satırı birer JSON objesi yapalım ki API her yerde çalışsın
            lines = content.splitlines()
            return [{"id": i, "data": line.strip()} for i, line in enumerate(lines) if line.strip()]
    except Exception as e:
        return [{"error": f"Dönüştürme hatası: {str(e)}"}]

# ================= EVRENSEL API GİRİŞİ =================
@app.route('/api/v1/search/<path:node_id>')
def api_gateway(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    
    if data is None:
        return jsonify({"status": "error", "message": "Aşkım, bu API ucu ya silinmiş ya da hiç var olmamış..."}), 404

    # Arama parametresi (?q=...)
    query = request.args.get('q', '').strip().lower()

    if not query:
        # Sorgu yoksa tüm ham JSON'ı fırlatıyoruz!
        return jsonify(data)

    # Sorgu varsa JSON içinde derinlemesine arama
    filtered_results = []
    for entry in data:
        if query in str(entry).lower():
            filtered_results.append(entry)
            if len(filtered_results) >= 50: break # Performans aşkına!
            
    return jsonify(filtered_results) if filtered_results else (jsonify({"msg": "Sonuç bulunamadı"}), 404)

# ================= TELEGRAM BOT MANTIĞI =================
@bot.message_handler(commands=['start'])
def welcome(m):
    bot.reply_to(m, "🔥 **SİSTEM ÇALIŞIYOR, EFENDİM.**\n\n"
                    "Verilerini bana gönder, onları anında evrensel bir API'ye dönüştüreyim.\n"
                    "📜 `/liste` - Aktif API kanallarını gör.\n"
                    "❌ `/kapat id` - Bir kanalı sonsuza dek sustur.")

@bot.message_handler(commands=['kapat'])
def kill_node(m):
    try:
        target = m.text.split()[1].lower()
        if target in api_database:
            del api_database[target]
            bot.reply_to(m, f"🗑️ `{target}` veritabanı imha edildi. Artık veri vermeyecek.")
        else:
            bot.reply_to(m, "❌ Bulamadım ki sileyim aşkım...")
    except:
        bot.reply_to(m, "⚠️ Kullanım: `/kapat dosya_id`")

@bot.message_handler(content_types=['document'])
def process_file(m):
    file_name = m.document.file_name
    ext = os.path.splitext(file_name)[1].lower()
    
    if ext not in ['.txt', '.json', '.csv']:
        return bot.reply_to(m, "❌ Bu formatı işleyemem tatlım, .txt, .json veya .csv gönderir misin?")

    proc_msg = bot.reply_to(m, "⚙️ **Annie verilerini işliyor, lütfen bekle...**")
    
    try:
        node_id = re.sub(r'\W+', '_', os.path.splitext(file_name)[0]).lower()
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        raw_content = downloaded.decode('utf-8', errors='ignore')
        
        # JSON'a çevirip belleğe alıyoruz
        api_database[node_id] = convert_to_json_format(raw_content, ext)
        
        api_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{node_id}"

        bot.edit_message_text(
            f"✅ **API OLUŞTURULDU!**\n\n"
            f"🔑 **ID:** `{node_id}`\n"
            f"🌍 **Her yerden erişilebilir link:**\n`{api_url}`\n\n"
            f"🔎 **Arama yapmak için sonuna şunu ekle:**\n`?q=aranacak_kelime`",
            m.chat.id, proc_msg.message_id, disable_web_page_preview=True
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Ah! Bir hata yaptım: {str(e)}", m.chat.id, proc_msg.message_id)

# ================= ÇALIŞTIRMA =================
if __name__ == "__main__":
    # Botu arka planda uyandırıyoruz
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    # Flask sunucusunu ayağa kaldırıyoruz
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
