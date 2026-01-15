import telebot
import os
import re
import threading
import json
import io
from flask import Flask, request, jsonify, send_file

# ================= AYARLAR =================
TOKEN = "8498288720:AAF4hUTWn6b3Z3rQmaJWaAXwYvfFzU3GVOc"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# Yüklenen tüm verilerin kişi blokları halinde saklandığı yer
api_database = {}

# ================= VERİ PAKETLEYİCİ =================
def process_into_blocks(content):
    """Veriyi senin o meşhur çerçeveli bloklarına ayırır sevgilim."""
    raw_blocks = content.split("╭━━━━━━━━━━━━━━━╮")
    final_blocks = []
    for block in raw_blocks:
        clean_block = block.strip().replace("╰━━━━━━━━━━━━━━━╯", "")
        if clean_block:
            # Her bir kişiyi tam bir blok olarak geri paketliyoruz
            formatted_block = "╭━━━━━━━━━━━━━━━╮\n" + clean_block + "\n╰━━━━━━━━━━━━━━━╯"
            final_blocks.append(formatted_block)
    return final_blocks

# ================= 🚀 CANLI API MOTORU (GÖSTER & ARA) =================
@app.route('/api/v1/search/<path:node_id>')
def api_gateway(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    
    if data is None:
        return "❌ Hata: Bu API ID'si (dosya) bulunamadı sevgilim.", 404

    # API'ye gelen sorgu: ?q=SORGU (TC, İsim veya GSM olabilir)
    query = request.args.get('q', '').strip().lower()
    
    # DURUM A: Eğer sorgu yoksa (?q= boşsa), tüm verileri göster
    if not query:
        return "\n\n".join(data)

    # DURUM B: API'ye bir istek geldiğinde (Arama Yapma)
    # Gelen sorguyu her bloğun içinde tarar ve eşleşen bloğu bulup gönderir
    results = [block for block in data if query in block.lower()]
    
    count = len(results)
    
    if count == 0:
        return f"❌ '{query}' ile eşleşen bir veri bulunamadı.", 404
    
    # Eşleşen verileri isteği atan yere geri gönderiyoruz
    if count <= 5:
        # 5'ten az sonuç varsa direkt metin olarak fırlat
        return "\n\n".join(results)
    else:
        # Çok sonuç varsa otomatik .txt dosyası oluşturup gönder
        output = io.BytesIO()
        txt_content = f"--- '{query.upper()}' SORGUSU: {count} SONUC ---\n\n" + "\n\n".join(results)
        output.write(txt_content.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{query}_sonuclar.txt"
        )

# ================= BOT YÖNETİMİ =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✨ **Annie API Master Aktif!**\n\nBana `.txt` dosyasını at, ben onu hem veri gösteren hem de sorgu bulup gönderen bir API yapayım sevgilim.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    fname = m.document.file_name
    msg = bot.reply_to(m, "⚙️ **API katmanı oluşturuluyor ve arama motoru kuruluyor...**")
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(fname)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        
        # Veriyi blokla ve hafızaya al
        api_database[nid] = process_into_blocks(cont)
        
        api_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}"
        
        bot.edit_message_text(
            f"✅ **API CANLI VE AKILLI!**\n\n"
            f"📍 **ID:** `{nid}`\n"
            f"🌍 **Tüm Veriler:** `{api_url}`\n"
            f"🔎 **Sorgu Yapmak İçin:** `{api_url}?q=SORGU`\n\n"
            f"API artık kendisine gelen her isteği verilerin içinde arayıp bulacak sevgilim!",
            m.chat.id, msg.message_id
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Ah, hata yaptım aşkım: {e}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
