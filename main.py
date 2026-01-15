import telebot
import os
import re
import threading
import io
import time
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

# ================= AYARLAR =================
TOKEN = "8369473810:AAFDKtH5PJH08itewxcbYlw4UDS7iL6KaE4"
RENDER_NAME = "gamebzhhshs" 

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)
CORS(app) 

api_database = {}

def process_into_blocks(content):
    raw_blocks = content.split("----------------")
    final_blocks = []
    for block in raw_blocks:
        clean_block = block.strip()
        if len(clean_block) > 15:
            final_blocks.append("----------------\n" + clean_block + "\n----------------")
    return final_blocks

# ================= 🌍 PHP & EVRENSEL ERİŞİM NOKTASI =================
@app.route('/api/v1/search/<path:node_id>', methods=['GET', 'POST'])
def api_gateway(node_id):
    node_id = node_id.lower()
    data = api_database.get(node_id)
    
    if data is None:
        return jsonify({"success": False, "message": "API Düğümü (Node) bulunamadı sevgilim."}), 404

    # PHP'den gelen GET veya POST verilerini yakalıyoruz
    args = request.args if request.method == 'GET' else request.form
    
    # --- PHP PANEL PARAMETRELERİ ---
    p = {
        "tc": args.get('tc', '').strip(),
        "ad": args.get('ad', '').strip().upper(),
        "soyad": args.get('soyad', '').strip().upper(),
        "annetc": args.get('annetc', '').strip(),
        "babatc": args.get('babatc', '').strip(),
        "q": args.get('q', '').strip().upper() # Genel anahtar kelime
    }

    # Eğer hiçbir şey aranmıyorsa örnek göster
    if not any(p.values()):
        return "\n\n".join(data[:5]) + "\n\n... (Sorgu parametresi bekleniyor sevgilim)"

    results = []
    for block in data:
        b_up = block.upper()
        match = False
        
        # PHP sorgu önceliklerine göre filtreleme
        if p["tc"] and (f"T.C: {p['tc']}" in b_up or f"TC: {p['tc']}" in b_up): 
            match = True
        elif p["annetc"] and f"ANNETC: {p['annetc']}" in b_up:
            match = True
        elif p["babatc"] and f"BABATC: {p['babatc']}" in b_up:
            match = True
        elif p["ad"] and p["soyad"]:
            if f"ADI: {p['ad']}" in b_up and f"SOYADI: {p['soyad']}" in b_up:
                match = True
        elif p["ad"] and f"ADI: {p['ad']}" in b_up:
            match = True
        elif p["q"] and p["q"] in b_up:
            match = True

        if match:
            results.append(block)

    if not results:
        return "❌ Aradığınız kriterlerde kayıt bulunamadı sevgilim.", 404

    return "\n\n".join(results)

# ================= BOT YÖNETİMİ =================
@bot.message_handler(content_types=['document'])
def handle_file(m):
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(m.document.file_name)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        api_database[nid] = process_into_blocks(cont)
        bot.reply_to(m, f"✅ **API PHP & DÜNYAYA AÇILDI!**\n\n📍 ID: `{nid}`\n🌍 Link: `https://{RENDER_NAME}.onrender.com/api/v1/search/{nid}`")
    except Exception as e:
        bot.reply_to(m, f"❌ Hata: {e}")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    while True:
        try: bot.polling(none_stop=True)
        except: time.sleep(5)
