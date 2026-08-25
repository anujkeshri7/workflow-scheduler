from overlay import images
from telegram_sender import send_to_telegram

for item in images:
    print(f"Sending {item['out']} to Telegram...")
    send_to_telegram(item["out"], item.get("caption", "Trending News!"))
