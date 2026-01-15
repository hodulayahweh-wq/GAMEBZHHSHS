import telebot
import os
import re
import threading
import io
import time
from flask import Flask, request, send_file

# ================= AYARLAR =================
TOKEN = "8369473810:AAG5KqjuNUxivnJOpNq6gFP1rm1AIDhtYaE"
RENDER_NAME = "gamebzhhshs" 

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)
api_database = {}

# ================= VERİ PAKETLEYİCİ =================
def process_into_blocks(content):
    # Veriyi çizgilerine göre bloklara ayırıyoruz
    raw_blocks = content.split("----------------")
    final_blocks = []
    for block in raw_blocks:
        clean_block = block.strip()
        if clean_block and len(clean_block) > 10:
            formatted_block = "----------------\n" + clean_block + "\n----------------"
            final_blocks.append(formatted_block)
    return final_blocks

# ================= 🛡️ PHP PARAMETRE YAKALAYICI =================
@app.route('/api/v1/search/<path:node_id>')
def api_gateway(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    
    if data is None:
        return "❌ Hata: API ID bulunamadı sevgilim.", 404

    # PHP'den gelen tüm olası parametreleri tek tek yakalıyoruz
    p_tc = request.args.get('tc', '').strip().upper()
    p_ad = request.args.get('ad', '').strip().upper()
    p_soyad = request.args.get('soyad', '').strip().upper()
    p_genel = request.args.get('q', '').strip().upper() # Eski uyum için

    results = []
    
    # Veri bloklarını tara
    for block in data:
        block_up = block.upper()
        match = False
        
        # 1. Eğer TC ile arama yapılıyorsa
        if p_tc and f"TC: {p_tc}" in block_up:
            match = True
        # 2. Eğer AD ve SOYAD birlikte arama yapılıyorsa (Nokta atışı!)
        elif p_ad and p_soyad:
            if f"ADI: {p_ad}" in block_up and f"SOYADI: {p_soyad}" in block_up:
                match = True
        # 3. Eğer sadece isim veya sadece soyisim aratılıyorsa
        elif p_ad and f"ADI: {p_ad}" in block_up:
            match = True
        elif p_soyad and f"SOYADI: {p_soyad}" in block_up:
            match = True
        # 4. Genel arama parametresi 'q' gelmişse
        elif p_genel and p_genel in block_up:
            match = True

        if match:
            results.append(block)

    if not results:
        return "❌ Aradığın kriterlerde kayıt bulunamadı sevgilim.", 404

    return "\n\n".join(results)

# ================= BOT VE SUNUCU BAŞLATICI =================
@bot.message_handler(content_types=['document'])
def handle_file(m):
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(m.document.file_name)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        api_database[nid] = process_into_blocks(cont)
        bot.reply_to(m, f"✅ **API Aktif!**\nID: `{nid}`\nURL: `https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}`")
    except Exception as e:
        bot.reply_to(m, f"❌ Hata: {e}")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True)
        except:
            time.sleep(5)
