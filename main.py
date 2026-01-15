import telebot
import os
import re
import threading
import json
import io
import pandas as pd
from flask import Flask, Response, request

# ================= AYARLAR =================
TOKEN = "8215957977:AAElCmNyvV-cclX2JuD8SWeEHwx1afuiipc"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# Bellek tabanlı veritabanı (Bot kapanınca sıfırlanır - Güvenli Mod)
api_database = {}

# ================= VERİ AYIKLAMA MOTORU =================
def clean_universal_data(content, extension):
    try:
        if extension == '.json':
            data = json.loads(content)
            text_content = json.dumps(data, indent=2, ensure_ascii=False)
        elif extension == '.csv':
            df = pd.read_csv(io.StringIO(content))
            text_content = df.to_string(index=False)
        else:
            text_content = content
        
        # Temizlik: Sadece veriyi bırak, alt alta diz
        lines = text_content.splitlines()
        clean_lines = [re.sub(r'[^\w\s\d:|\-.,]', '', line).strip() for line in lines if line.strip()]
        return "\n".join(clean_lines)
    except:
        return content # Hata durumunda ham metni koru

# ================= HAYALET ANA SAYFA =================
@app.route('/')
def home():
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <h2>> STATUS: SYSTEM_READY</h2>
        <p>> DATABASE_NODES: {len(api_database)} ACTIVE</p>
        <p>> UPTIME_MODE: VOLATILE_MEMORY (Session-Only)</p>
        <hr>
        <p style="color:#333;">Secure Handshake Active. No logs stored on disk.</p>
    </body>
    """

# ================= ÇOKLU API TÜNELİ =================
@app.route('/api/v1/data/<path:filename>')
def get_data(filename):
    # Bellekten dosyayı getir
    data = api_database.get(filename)
    if data:
        # Gerçek bir .txt dosyası gibi ham metin döner
        return Response(data, mimetype='text/plain')
    return "404 - Veri bulunamadı veya sunucu yeniden başlatıldı.", 404

# ================= TELEGRAM BOT MANTIĞI =================
@bot.message_handler(commands=['start'])
def welcome(m):
    bot.reply_to(m, (
        "🏁 **LORD MULTI-FORMAT API ENGINE**\n\n"
        "Desteklenen formatlar: `.txt, .json, .csv, .py`\n"
        "Her dosya adı için ayrı bir API oluşturulur.\n\n"
        "⚠️ *Not: Sunucu kapandığında veriler güvenlik gereği silinir.*"
    ))

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    # Uzantıyı ve güvenli dosya adını al
    ext = os.path.splitext(m.document.file_name)[1].lower()
    if ext not in ['.txt', '.json', '.py', '.csv']:
        return bot.reply_to(m, "❌ Geçersiz format!")

    status_msg = bot.reply_to(m, "⚙️ **Dosya işleniyor...**")
    
    try:
        # Dosya adını URL dostu yap (Örn: "Veri Dosyam.txt" -> "veri_dosyam")
        file_base_name = os.path.splitext(m.document.file_name)[0]
        safe_name = re.sub(r'\W+', '_', file_base_name).lower()
        
        # Dosyayı indir
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8', errors='ignore')
        
        # Veriyi işle ve belleğe (RAM) kaydet
        processed_data = clean_universal_data(content, ext)
        api_database[safe_name] = processed_data
        
        # Dinamik Link Oluştur
        api_link = f"https://{RENDER_NAME}.onrender.com/api/v1/data/{safe_name}"

        res_text = (
            f"✅ **BELLEĞE YÜKLENDİ**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 **Dosya:** `{m.document.file_name}`\n"
            f"📊 **Durum:** `{len(processed_data.splitlines())} Satır İşlendi`\n"
            f"🔗 **API URL:**\n`{api_link}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *API, sunucu açık kaldığı sürece aktif kalacaktır.*"
        )
        bot.edit_message_text(res_text, m.chat.id, status_msg.message_id, disable_web_page_preview=True)

    except Exception as e:
        bot.edit_message_text(f"❌ Hata: `{str(e)}`", m.chat.id, status_msg.message_id)

# ================= BAŞLATICI =================
if __name__ == "__main__":
    # Botu arka planda çalıştır
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    
    # Flask sunucusunu Render'ın portunda başlat
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
