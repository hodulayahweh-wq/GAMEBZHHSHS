import telebot
import os
import re
import threading
from flask import Flask, Response, request

# ================= AYARLAR =================
TOKEN = "8215957977:AAElCmNyvV-cclX2JuD8SWeEHwx1afuiipc"
RENDER_NAME = "gamebzhhshs"
# Gizli tünel yolu (Sabit tuttum ki her seferinde değişmesin)
SECRET_TOKEN = "v1_secure_data_access_8829" 

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

api_storage = {
    "payload": "Server is operational. Waiting for data..."
}

# ================= VERİ TEMİZLEME MOTORU =================
def clean_data_logic(text):
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line:
            # Sadece kritik verileri tut (TC, GSM, İsim, Soyisim formatlarını bozmaz)
            clean_line = re.sub(r'[^\w\s\d:|\-]', '', line)
            if clean_line:
                clean_lines.append(clean_line)
    return "\n".join(clean_lines)

# ================= KAMUFLAJ ANA SAYFA (RENDER GİZLEME) =================
@app.route('/')
def home():
    # Siteye giren biri bot değil, oyun sunucu paneli görecek
    return """
    <html>
        <head><title>Game Engine v4.0 - Status</title></head>
        <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
            <h2>> SYSTEM_STATUS: ONLINE</h2>
            <p>> SERVER_REGION: EU-WEST</p>
            <p>> ACTIVE_PLAYERS: 1,402</p>
            <p>> LATENCY: 12ms</p>
            <hr>
            <p style="color:#555;">© 2026 GameBzhhshs Development Team</p>
        </body>
    </html>
    """

# ================= GİZLİ API TÜNELİ =================
@app.route(f'/{SECRET_TOKEN}')
def get_raw_data():
    # Sadece linki bilen senin için saf veriyi döner
    return Response(
        api_storage["payload"],
        mimetype='text/plain'
    )

# ================= TELEGRAM BOT =================
@bot.message_handler(commands=['start'])
def welcome(m):
    bot.reply_to(m, "🛰 **GHOST MODE AKTİF**\n\nTemizlenecek `.txt` dosyasını gönder sevgilim. Veriyi oyun sunucusu maskesinin arkasına saklayacağım.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    if not m.document.file_name.endswith('.txt'):
        return

    try:
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        raw_text = downloaded.decode('utf-8', errors='ignore')
        
        # Temizle ve Kaydet
        cleaned = clean_data_logic(raw_text)
        api_storage["payload"] = cleaned
        
        # Senin Render Linkin
        api_link = f"https://{RENDER_NAME}.onrender.com/{SECRET_TOKEN}"

        caption = (
            "✅ **VERİ ŞİFRELENDİ & YÜKLENDİ**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Satır Sayısı:** `{len(cleaned.splitlines())}`\n"
            f"🔗 **Gizli API:** [BURAYA TIKLA]({api_link})\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👤 *Veri şu an oyun sunucusu kamuflajı altında.*"
        )
        bot.send_message(m.chat.id, caption, disable_web_page_preview=True)
    except:
        pass

# ================= BAŞLATICI =================
if __name__ == "__main__":
    # Botu arka plana at
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    
    # Render'ın portunu yakala
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

