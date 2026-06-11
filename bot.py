import requests
from bs4 import BeautifulSoup
import time
import os
import threading
from flask import Flask

# --- AYARLAR ---
TELEGRAM_BOT_TOKEN = "8722947013:AAHf4aIVmHUV1UHMrXVoVytTIq7y8I28hT0"
TELEGRAM_CHAT_ID = "-5071774844"
FORUM_URL = "https://forum.donanimarsivi.com/forumlar/Sicakfirsatlar/"
KONTROL_SURESI = 180 
HAFIZA_DOSYASI = "gonderilenler.txt"

# --- FLASK WEB SUNUCUSU (Sistemi uyanık tutmak için) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Sıcak Fırsatlar Botu 7/24 Ayakta ve Pusuda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT FONKSİYONLARI ---
if os.path.exists(HAFIZA_DOSYASI):
    with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
        gorulen_konular = set(f.read().splitlines())
else:
    gorulen_konular = set()

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except:
        return False

def konulari_kontrol_et():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(FORUM_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        konular = soup.find_all("div", class_="structItem")
        
        for konu in konular:
            if "structItem-status--sticky" in konu.get("class", []):
                continue
                
            title_div = konu.find("div", class_="structItem-title")
            if not title_div:
                continue
                
            baslik_metni = title_div.text.strip()
            baslik_temiz = " ".join(baslik_metni.split()) 
            
            if "İndirim Bitti" in baslik_metni or "İndirim" not in baslik_metni:
                continue
                
            time_tag = konu.find("time")
            if not time_tag or "data-timestamp" not in time_tag.attrs:
                continue
                
            if (time.time() - int(time_tag["data-timestamp"])) > 259200: 
                continue 
            
            link = None
            for a_etiketi in title_div.find_all("a", href=True):
                if "/konu/" in a_etiketi["href"]:
                    link = "https://forum.donanimarsivi.com" + a_etiketi["href"]
                    break
            
            if not link or link in gorulen_konular:
                continue
                
            mesaj = f"🔥 <b>YENİ FIRSAT!</b> 🔥\n\n📌 {baslik_temiz}\n🔗 {link}"
            
            if telegram_mesaj_gonder(mesaj):
                gorulen_konular.add(link)
                with open(HAFIZA_DOSYASI, "a", encoding="utf-8") as f:
                    f.write(link + "\n")
                time.sleep(1) 
                
    except Exception as e:
        print("Hata:", e)

def bot_dongusu():
    print("🚀 Bot döngüsü başlatıldı!")
    konulari_kontrol_et()
    while True:
        time.sleep(KONTROL_SURESI)
        konulari_kontrol_et()

if __name__ == "__main__":
    # Flask sunucusunu ayrı bir thread (iş parçacığı) olarak başlatıyoruz
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Asıl botumuzu çalıştırıyoruz
    bot_dongusu()
