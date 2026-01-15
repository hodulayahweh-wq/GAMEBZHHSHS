import telebot
import os
import re
import threading
import json
import io
from flask import Flask, request, jsonify, send_file

# ================= AYARLAR =================
TOKEN = "8316865240:AAGtx8L-1HijKQfKG0H1d9jo58gc59Xn-nI"
RENDER_NAME = "gamebzhhshs"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# Tüm API verilerinin saklandığı merkezi hafıza
api_database = {}

# ================= VERİ ANALİZ VE BLOKLAMA =================
def process_into_blocks(content):
    """Veriyi senin istediğin o çerçeveli bloklara ayırır sevgilim."""
    raw_blocks = content.split("╭━━━━━━━━━━━━━━━╮")
    final_blocks = []
    for block in raw_blocks:
        clean_block = block.strip().replace("╰━━━━━━━━━━━━━━━╯", "")
        if clean_block:
            # Her bir kişiyi tam bir blok olarak kaydediyoruz
            formatted_block = "╭━━━━━━━━━━━━━━━╮\n" + clean_block + "\n╰━━━━━━━━━━━━━━━╯"
            final_blocks.append(formatted_block)
    return final_blocks

# ================= 🚀 AKILLI API SORGULAMA SİSTEMİ =================
@app.route('/api/v1/search/<path:node_id>')
def api_gateway(node_id):
    node_id = node_id.lower()
    # API isteği atan yerin aradığı veriyi çekiyoruz
    data = api_database.get(node_id)
    
    if data is None:
        return "❌ Hata: Bu API ID'si aktif değil sevgilim.", 404

    # Dışarıdan gelen sorgu parametresi: ?q=SORGU
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        return "⚠️ Lütfen bir sorgu (q) parametresi gönderin aşkım.", 400

    # API BURADA ARAMA YAPIYOR:
    # Gelen istekteki kelimeyi (TC/GSM/AD) tüm blokların içinde tarıyoruz
    results = [block for block in data if query in block.lower()]
    
    count = len(results)
    
    if count == 0:
        return f"❌ '{query}' için hiçbir veri bulunamadı.", 404
    
    # İsteği atan yere veriyi gönderiyoruz:
    if count <= 2:
        # Eğer az sonuç varsa direkt metin olarak gönder (Diğer botlar rahat okur)
        return "\n\n".join(results)
    else:
        # Eğer çok sonuç varsa, isteği atan yere bir .txt dosyası olarak fırlat
        output = io.BytesIO()
        txt_content = f"--- '{query.upper()}' SORGUSU: {count} SONUC ---\n\n" + "\n\n".join(results)
        output.write(txt_content.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{query}_results.txt"
        )

# ================= BOT YÖNETİMİ =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✨ **Annie API Builder Aktif!**\n\nBana bir `.txt` dosyası gönder, ben onu anında sorgulanabilir bir API'ye dönüştüreyim sevgilim.")

@bot.message_handler(content_types=['document'])
def handle_file(m):
    fname = m.document.file_name
    msg = bot.reply_to(m, "⚙️ **API oluşturuluyor ve sorguya hazır hale getiriliyor...**")
    try:
        # Dosya isminden temiz bir API ID'si oluşturuyoruz
        nid = re.sub(r'\W+', '_', os.path.splitext(fname)[0]).lower()
        
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        
        # Veriyi bloklara ayırıp hafızaya alıyoruz
        api_database[nid] = process_into_blocks(cont)
        
        api_url = f"https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}?q=ARANACAK_VERI"
        
        bot.edit_message_text(
            f"✅ **API BAŞARIYLA OLUŞTURULDU!**\n\n"
            f"🔗 **API URL:** `{api_url}`\n\n"
            f"🔎 Bu linke bir sorgu gönderildiğinde, API verilerin içinde arama yapacak ve sonucu isteği atan yere anında döndürecektir aşkım!",
            m.chat.id, msg.message_id
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Bir hata oluştu tatlım: {e}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    # Bot ve API aynı anda çalışıyor
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
