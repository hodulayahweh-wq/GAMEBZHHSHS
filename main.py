import telebot
import os
import re
import threading
import io
import time
import requests  # Keep-alive için gerekli
from flask import Flask, request, jsonify
from flask_cors import CORS

# ================= AYARLAR =================
TOKEN = "8065268709:AAH3kZ0GfYnfvSWvLC9Jo-MKTzz7jeXNhxI"
RENDER_NAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "gamebzhhshs.onrender.com")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)
CORS(app) 

api_database = {}

# ================= KEEP ALIVE (HAYATTA TUTMA) =================
def keep_alive():
    """Sistemin uyumasını engellemek için her 5 dakikada bir kendine istek atar."""
    while True:
        try:
            url = f"https://{RENDER_NAME}/health"
            requests.get(url)
            print("--- Ping gönderildi, sistem dinç tutuluyor sevgilim ---")
        except Exception as e:
            print(f"Keep-alive hatası: {e}")
        time.sleep(300) # 5 dakikada bir çalışır

@app.route('/health')
def health_check():
    return "Sistem Ayakta!", 200

# ================= İŞLEME MANTIĞI =================
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
        return jsonify({"success": False, "message": "API Düğümü bulunamadı sevgilim."}), 404

    args = request.args if request.method == 'GET' else request.form
    
    p = {
        "tc": args.get('tc', '').strip(),
        "ad": args.get('ad', '').strip().upper(),
        "soyad": args.get('soyad', '').strip().upper(),
        "annetc": args.get('annetc', '').strip(),
        "babatc": args.get('babatc', '').strip(),
        "q": args.get('q', '').strip().upper() 
    }

    if not any(p.values()):
        return "\n\n".join(data[:5]) + "\n\n... (Sorgu bekleniyor sevgilim)"

    results = []
    for block in data:
        b_up = block.upper()
        match = False
        
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

    return "\n\n".join(results) if results else "❌ Kayıt bulunamadı sevgilim."

# ================= BOT YÖNETİMİ =================
@bot.message_handler(content_types=['document'])
def handle_file(m):
    try:
        nid = re.sub(r'\W+', '_', os.path.splitext(m.document.file_name)[0]).lower()
        finfo = bot.get_file(m.document.file_id)
        down = bot.download_file(finfo.file_path)
        cont = down.decode('utf-8', errors='ignore')
        api_database[nid] = process_into_blocks(cont)
        bot.reply_to(m, f"✅ **API AKTİF!**\n\n📍 ID: `{nid}`\n🌍 Link: `https://{RENDER_NAME}/api/v1/search/{nid}`")
    except Exception as e:
        bot.reply_to(m, f"❌ Hata: {e}")

# ================= ANA ÇALIŞTIRICI =================
if __name__ == "__main__":
    # 1. Flask'ı başlat
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=False, use_reloader=False), daemon=True).start()
    
    # 2. Keep Alive sistemini başlat (Render için kritik)
    threading.Thread(target=keep_alive, daemon=True).start()
    
    print("🚀 Sistem ve Keep-Alive Ayağa Kalktı Sevgilim!")
    
    # 3. Botu döngüye sok
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Bot Hatası: {e}")
            time.sleep(5)
