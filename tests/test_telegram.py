import os
import sys
from dotenv import load_dotenv

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.notifications.telegram import TelegramNotifier

def test_manual_notification():
    load_dotenv()
    
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_id") # Note: some envs might use lowercase
    if not chat_id:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ Error: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not found in .env")
        print("Asegúrate de crear un archivo .env con estas variables para probar.")
        return

    print(f"Sending test message to {chat_id}...")
    notifier = TelegramNotifier(token, chat_id)
    notifier.send_message("<b>🔔 Prueba de Bot AimHarder</b>\nSi lees esto, las notificaciones están bien configuradas. 🚀")
    print("✅ Proceso finalizado. Revisa tu Telegram.")

if __name__ == "__main__":
    test_manual_notification()
