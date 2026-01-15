import telebot
import os
import re
import threading
import json
import io
import pandas as pd
from flask import Flask, Response, request

# ================= AYARLAR =================
TOKEN = "8173921081:AAE-YxozU3YZzKM3Uf4UnfUTUEwLNIbjg6E"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# ÇOKLU VERİ DEPOSU (Sözlük yapısı: { "dosya_yolu": "veri_icerigi" })
# Bu yapı sayesinde her dosya kendi adıyla ayrı bir API olur.
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
        
        lines = text_content.splitlines()
        # Veriyi temizle ve her satırı alt alta diz
        clean_lines = [re.sub(r'[^\w\s\d:|\-.,]', '', line).strip() for line in lines if line.strip()]
        return "\n".join(clean_lines)
    except:
        return content

# ================= HAYALET ANA SAYFA =================
@app.route('/')
def home():
    # Aktif API yollarını listeler (Sadece ana sayfada kaç tane olduğunu söyler)
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:20px;">
        <h2>> STATUS: MULTI_NODE_ACTIVE</h2>
        <p>> TOTAL_ACTIVE_APIS: {len(api_database)}</p>
        <hr>
        <p style="color:#333;">Session data is stored in volatile memory. Shutdown clears all nodes.</p>
    </body>
    """

# ================= DİNAMİK ÇOKLU API TÜNELİ =================
@app.route('/api/v1/data/<path:filename>')
def get_data(filename):
    # Dosya adını veritabanında ara (Case-insensitive)
    data = api_database.get(filename.lower())
    if data:
        return Response(data, mimetype='text/plain')
    return "404 - Node Not Found. This API may have been cleared during reboot.", 404

# ================= TELEGRAM BOT MANTIĞI =================
@bot.message_handler(commands=['start'])
def welcome(m):
    bot.reply_to(m, (
        "🛰 **DİNAMİK ÇOKLU API SİSTEMİ**\n\n"
        "Her gönderdiğin dosya için ayrı bir link oluşturulur.\n"
        "• `.txt, .json, .csv, .py` dosyalarını destekliyorum.\n\n"
        "💎 **Durum:** `Sistem Hazır`"
    ))

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    # Uzantı ve Dosya Adı İşlemleri
    raw_filename = m.document.file_name
    name_split = os.path.splitext(raw_filename)
    file_base_name = name_split[0]
    ext = name_split[1].lower()

    if ext not in ['.txt', '.json', '.py', '.csv']:
        return bot.reply_to(m, "❌ Bu dosya formatını işleyemem sevgilim.")

    status_msg = bot.reply_to(m, f"⚙️ `{raw_filename}` **ayrı bir API hattına bağlanıyor...**")
    
    try:
        # Dosya adını URL uyumlu temiz bir hale getir (Boşlukları '_' yapar)
        safe_name = re.sub(r'\W+', '_', file_base_name).lower()
        
        # Dosyayı indir
        file_info = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8', errors='ignore')
        
        # Veriyi işle ve ÇOKLU veritabanına ekle
        processed_data = clean_universal_data(content, ext)
        
        # BURASI KRİTİK: Mevcut verileri silmez, yenisini yanına ekler.
        api_database[safe_name] = processed_data
        
        # Her dosya için benzersiz URL
        api_link = f"https://{RENDER_NAME}.onrender.com/api/v1/data/{safe_name}"

        res_text = (
            f"✅ **YENİ API HATTI OLUŞTURULDU**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 **Dosya:** `{raw_filename}`\n"
            f"🆔 **ID:** `{safe_name}`\n"
            f"🔗 **API URL:**\n`{api_link}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 *Toplam `{len(api_database)}` farklı API şu an yayında!*"
        )
        bot.edit_message_text(res_text, m.chat.id, status_msg.message_id, disable_web_page_preview=True)

    except Exception as e:
        bot.edit_message_text(f"❌ Hata: `{str(e)}`", m.chat.id, status_msg.message_id)

# ================= BAŞLATICI =================
if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
