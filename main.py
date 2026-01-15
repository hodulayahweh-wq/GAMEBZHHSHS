import telebot
import os
import re
import threading
import json
import io
from flask import Flask, request, jsonify

# ================= AYARLAR =================
TOKEN = "8118811696:AAE-MMRdl1CVlfO6UmlZahN7n0_WBm7hEQ4"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

api_database = {}

# ================= VERİ GRUPLAYICI (BLOCK ENGINE) =================
def process_into_blocks(content):
    """
    Bu fonksiyon, senin o sembollü (┃➥) verilerini 
    kişi bazlı bloklara ayırır aşkım.
    """
    # Veriyi kişi bloklarına bölüyoruz (Genelde çerçeve çizgisiyle ayrılır)
    # Eğer dosyan "╭━━━━" ile başlıyorsa ona göre bölelim
    raw_blocks = content.split("╭━━━━━━━━━━━━━━━╮")
    final_blocks = []
    
    for block in raw_blocks:
        clean_block = block.strip().replace("╰━━━━━━━━━━━━━━━╯", "")
        if clean_block:
            # Bloğu geri eski haline getirip tek bir metin objesi yapıyoruz
            formatted_block = "╭━━━━━━━━━━━━━━━╮\n" + clean_block + "\n╰━━━━━━━━━━━━━━━╯"
            final_blocks.append({"full_data": formatted_block})
            
    return final_blocks

# ================= API ARAMA =================
@app.route('/api/v1/search/<path:node_id>')
def search_api(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    if data is None:
        return jsonify({"status": "error", "message": "Node bulunamadi"}), 404

    query = request.args.get('q', '').strip().lower()
    
    # Eğer sorgu yoksa tüm blokları ver
    if not query:
        return jsonify(data)

    # Sorgu varsa, blokların içinde ara ve eşleşen TÜM BLOĞU getir
    results = [item for item in data if query in item['full_data'].lower()]
    
    # Veriyi senin istediğin gibi alt alta metin olarak basmak için (Plain Text Mode)
    # İstersen direkt JSON listesi olarak da bırakabilirsin aşkım.
    return jsonify(results[:10]) 

# ================= BOT KOMUTLARI =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 **Annie Blok Veri Sistemi Hazır!**\nDosyayı gönder, ben onları kişi kişi paketleyeyim.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    fname = m.document.file_name
    msg = bot.reply_to(m, "⚙️ **Bloklar oluşturuluyor sevgilim...**")
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(fname)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        
        # BURASI ÖNEMLİ: Veriyi bloklara ayırıyoruz
        api_database[nid] = process_into_blocks(cont)
        
        url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}"
        bot.edit_message_text(f"✅ **API HAZIR!**\nArtık her arama tam bir kimlik bloğu döndürecek.\nURL: `{url}`", m.chat.id, msg.message_id)
    except Exception as e: bot.edit_message_text(f"❌ Hata: {e}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
