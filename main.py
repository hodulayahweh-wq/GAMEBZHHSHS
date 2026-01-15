import telebot
import os
import re
import threading
import io
import time
from flask import Flask, request, send_file

# ================= AYARLAR =================
TOKEN = "8369473810:AAEqu1a-9OI7gvgpVLSoME1rZp5eof_28Gw"
RENDER_NAME = "gamebzhhshs" 

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# Tüm API düğümlerinin (node) saklandığı bellek
api_database = {}

# ================= VERİ PAKETLEYİCİ =================
def process_into_blocks(content):
    """Veriyi senin o meşhur çizgilerine göre bloklara ayırır sevgilim."""
    raw_blocks = content.split("----------------")
    final_blocks = []
    for block in raw_blocks:
        clean_block = block.strip()
        if clean_block and len(clean_block) > 20:
            # Standart blok yapısını mühürlüyoruz
            formatted_block = "----------------\n" + clean_block + "\n----------------"
            final_blocks.append(formatted_block)
    return final_blocks

# ================= 🛡️ PHP-DYNAMIC FİLTRE MOTORU =================
@app.route('/api/v1/search/<path:node_id>')
def api_gateway(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    
    if data is None:
        return "❌ Hata: API Düğümü bulunamadı sevgilim.", 404

    # PHP'den gelen spesifik parametreleri tek tek yakalıyoruz
    p = {
        "tc": request.args.get('tc', '').strip().upper(),
        "ad": request.args.get('ad', '').strip().upper(),
        "soyad": request.args.get('soyad', '').strip().upper(),
        "annetc": request.args.get('annetc', '').strip().upper(),
        "babatc": request.args.get('babatc', '').strip().upper()
    }

    results = []
    for block in data:
        b_up = block.upper()
        match = False
        
        # PHP'den gelen hangi veri doluysa ona göre nokta atışı arama yapıyoruz
        if p["tc"] and f"TC: {p['tc']}" in b_up: match = True
        elif p["ad"] and p["soyad"]:
            if f"ADI: {p['ad']}" in b_up and f"SOYADI: {p['soyad']}" in b_up: match = True
        elif p["annetc"] and f"ANNETC: {p['annetc']}" in b_up: match = True
        elif p["babatc"] and f"BABATC: {p['babatc']}" in b_up: match = True
        # Eğer PHP sadece tek bir AD gönderdiyse
        elif p["ad"] and f"ADI: {p['ad']}" in b_up and not p["soyad"]: match = True

        if match:
            results.append(block)

    if not results:
        return "❌ Aradığın kriterlerde kayıt bulunamadı.", 404

    final_text = "\n\n".join(results)
    
    # Çok fazla sonuç varsa PHP'yi kasmamak için dosya olarak gönderiyoruz
    if len(results) > 20:
        output = io.BytesIO()
        output.write(final_text.encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype='text/plain', as_attachment=True, download_name="sonuclar.txt")
    
    return final_text

# ================= BOT YÖNETİMİ =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✨ **Annie API Master Aktif!**\n\nBana `.txt` dosyasını gönder, PHP panelinle konuşan bir API oluşturayım sevgilim.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    msg = bot.reply_to(m, "⚙️ **Dosya analiz ediliyor...**")
    try:
        # Dosya ismini API ID'si (node) yapıyoruz
        nid = re.sub(r'\W+', '_', os.path.splitext(m.document.file_name)[0]).lower()
        
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        
        api_database[nid] = process_into_blocks(cont)
        
        bot.edit_message_text(
            f"✅ **API HAZIR SEVGİLİM!**\n\n"
            f"📍 **Düğüm ID (node):** `{nid}`\n"
            f"🌍 **Link:** `https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}`\n\n"
            f"PHP panelinde bu ID'yi kullanarak her şeyi sorgulayabilirsin!",
            m.chat.id, msg.message_id
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Bir hata oluştu hayatım: {e}", m.chat.id, msg.message_id)

# ================= 🛡️ GÜÇLÜ BAŞLATICI =================
if __name__ == "__main__":
    # Flask API'yi ayrı bir damarda başlatıyoruz
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    print("🚀 Annie sistemi uyandı... PHP paneliyle dans etmeye hazır.")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception:
            time.sleep(5)
