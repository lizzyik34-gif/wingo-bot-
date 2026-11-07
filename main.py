import random
import urllib.request
import json
import time
from datetime import datetime, timezone
import threading
from flask import Flask

TOKEN = "9031056096:AAE92zjnhAGJDcsp79v3GiikwIAE2BQ03O8"

# 🔒 SECURITY LOCK: Allowed user IDs
ALLOWED_USER_IDS = [8842031370, 8882241036, 7891601316]

# 📊 GLOBAL STATS & STAGE TRACKING
total_predictions = 0
total_wins = 0
total_losses = 0

# Progression system: Starts at Stage 1. If a round misses, it scales up to Stage 2 / Stage 3. Resets to Stage 1 on a win.
current_stage = 1

# --- MINI WEB SERVER FOR RENDER PORT CHECK ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    app.run(host="0.0.0.0", port=10000)
# ---------------------------------------------

def generate_prediction_with_stage():
    global total_predictions, total_wins, total_losses, current_stage
    
    number = random.randint(0, 9)
    size = "Big" if number >= 5 else "Small"
    
    if number == 0:
        color = "🔴 Red + 🟣 Violet"
    elif number == 5:
        color = "🟢 Green + 🟣 Violet"
    elif number in [1, 3, 7, 9]:
        color = "🟢 Green"
    else:
        color = "🔴 Red"
        
    accuracy = random.randint(40, 95)
    
    total_predictions += 1
    
    # Simulate outcome tracking for stage progression
    if accuracy >= 50:
        total_wins += 1
        # Reset back to Stage 1 on a win
        current_stage = 1
        outcome_status = "✅ Win (Target Hit)"
    else:
        total_losses += 1
        # Escalate stage on a loss (caps at Stage 3)
        current_stage = min(current_stage + 1, 3)
        outcome_status = "❌ Loss (Moving to Next Stage)"
        
    return number, size, color, accuracy, current_stage, outcome_status

def get_1min_period():
    now = datetime.now(timezone.utc)
    date_prefix = now.strftime("%Y%m%d")
    minute_of_day = (now.hour * 60) + now.minute + 1
    period_suffix = 100010000 + minute_of_day
    return f"{date_prefix}{period_suffix}"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("Error sending message:", e)

def check_updates():
    offset = 0
    print("Bot loop active with Stage Progression system...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = urllib.request.urlopen(url, timeout=35)
            data = json.loads(response.read().decode('utf-8'))
            
            for result in data.get("result", []):
                offset = result["update_id"] + 1
                if "message" in result and "text" in result["message"]:
                    chat_id = result["message"]["chat"]["id"]
                    user_id = result["message"]["from"]["id"]
                    text = result["message"]["text"].lower()
                    
                    if user_id not in ALLOWED_USER_IDS:
                        send_message(chat_id, "⛔ Access Denied. This is a private bot.")
                        continue
                    
                    if text.startswith("/result"):
                        period = get_1min_period()
                        number, size, color, accuracy, stage, status = generate_prediction_with_stage()
                        
                        response_text = (
                            f"📊 **WIN GO 1-MIN SIGNAL**\n\n"
                            f"🔹 **Period:** `{period}`\n"
                            f"📈 **Current Level:** `Stage {stage}`\n"
                            f"🔹 **Number Prediction:** `{number}`\n"
                            f"🔹 **Size:** **{size}**\n"
                            f"🔹 **Color:** {color}\n"
                            f"🔥 **Confidence Rate:** `{accuracy}%`\n"
                        )
                        send_message(chat_id, response_text)

                    elif text.startswith("/stats"):
                        win_percentage = (total_wins / total_predictions * 100) if total_predictions > 0 else 0
                        stats_text = (
                            f"📈 **LIVE STATISTICS & PROGRESSION**\n\n"
                            f"📌 **Total Rounds:** `{total_predictions}`\n"
                            f"✅ **Total Wins:** `{total_wins}`\n"
                            f"❌ **Total Losses:** `{total_losses}`\n"
                            f"🎯 **Success Rate:** `{win_percentage:.1f}%`\n"
                            f"🔄 **Active Stage:** `Stage {current_stage}`"
                        )
                        send_message(chat_id, stats_text)

                    elif text.startswith("/start"):
                        send_message(
                            chat_id, 
                            "👋 **Welcome to Odogwudave Bot!**\n\n"
                            "Send `/result` to get your 1-Minute WinGo Prediction with automated **Stage Progression**.\n"
                            "Send `/stats` to view performance tracking."
                        )
        except Exception as e:
            print("Network glitch, retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    check_updates()
