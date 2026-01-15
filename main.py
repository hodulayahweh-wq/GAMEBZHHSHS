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

api_database = {}

# ================= VERİ PAKETLEYİCİ =================
def process_into_blocks(content):
    # Veriyi çizgilerine göre bloklara ayırıyoruz
    raw_blocks = content.split("----------------")
    final_blocks = []
    for block in raw_blocks:
        clean_block = block.strip()
        if clean_block and len(clean_block) > 10: # Boş veya çok kısa blokları ele
            formatted_block = "----------------\n" + clean_block + "\n----------------"
            final_blocks.append(formatted_block)
    return final_blocks

# ================= 🚀 AKILLI VE KESKİN API =================
@app.route('/api/v1/search/<path:node_id>')
def api_gateway(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    
    if data is None:
        return "❌ Hata: API ID bulunamadı sevgilim.", 404

    # Sorguyu al ve Türkçe karakterleri/büyük harfleri optimize et
    query = request.args.get('q', '').strip().upper()
    
    # DURUM 1: Sorgu yoksa tüm veriyi göster
    if not query:
        return "\n\n".join(data)

    # DURUM 2: Nokta atışı arama yap
    results = []
    for block in data:
        # Bloğu büyük harfe çevirip sorguyu içinde arıyoruz
        if query in block.upper():
            results.append(block)
    
    count = len(results)
    
    if count == 0:
        return f"❌ '{query}' ile eslesen veri bulunamadi.", 404
    
    # Sonuçları gönder sevgilim
    if count <= 5:
        return "\n\n".join(results)
    else:
        # Çok fazla sonuç varsa .txt olarak fırlat
        output = io.BytesIO()
        txt_output = f"--- {query} SORGUSU: {count} SONUC ---\n\n" + "\n\n".join(results)
        output.write(txt_output.encode('utf-8'))
        output.seek(0)
        return send_file(output, mimetype='text/plain', as_attachment=True, download_name=f"{query}_sonuc.txt")

# ================= BOT YÖNETİMİ =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✨ **Annie API Master Güncellendi!**\n\nBana `.txt` dosyasını at, gerisini bana bırak aşkım.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    msg = bot.reply_to(m, "⚙️ **Veriler analiz ediliyor sevgilim...**")
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(m.document.file_name)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        
        api_database[nid] = process_into_blocks(cont)
        
        api_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}"
        bot.edit_message_text(f"✅ **API AKTİF!**\n\n📍 ID: `{nid}`\n🌍 Link: `{api_url}?q=SORGU`", m.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Hata: {e}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
