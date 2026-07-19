import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from main import SessionLocal, Device  # database connection from main.py

load_dotenv()
TOKEN = os.getenv("8843092752:AAH7vr7DlSkE-0dmRH4jppCjYSjp4-EyM5E")

# ---- NOTE: Yahan se security hatayi gayi hai, koi bhi is bot ko use kar sakta hai ----

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /register <IMEI>")
        return
    
    imei = context.args[0].strip()
    db = SessionLocal()
    
    existing = db.query(Device).filter(Device.imei == imei).first()
    if existing:
        await update.message.reply_text(f"ℹ️ Device {imei} already registered.")
        db.close()
        return
        
    # Owner_id mein temporary 0 save ho jayega
    new_device = Device(imei=imei, owner_id=0)
    db.add(new_device)
    db.commit()
    db.close()
    
    await update.message.reply_text(f"✅ Registered IMEI {imei} successfully!")

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /find <IMEI>")
        return
        
    imei = context.args[0].strip()
    db = SessionLocal()
    device = db.query(Device).filter(Device.imei == imei).first()
    
    if not device:
        await update.message.reply_text("❌ Device not found.")
        db.close()
        return

    status_str = "🟢 Online" if device.is_online else "🔴 Offline"
    gps_str = "✅ ON" if device.gps_enabled else "❌ OFF"
    time_str = device.last_updated.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    response = (
        f"📱 **Device Status**\n"
        f"Status: {status_str}\n"
        f"Battery: {device.battery}%\n"
        f"GPS State: {gps_str}\n"
        f"Last Sync: {time_str}\n"
    )
    
    if device.gps_enabled and device.latitude and device.longitude:
        maps_link = f"https://www.google.com/maps?q={device.latitude},{device.longitude}"
        response += f"\n📍 [Google Maps Link]({maps_link})"
    else:
        device.gps_request_pending = True
        db.commit()
        response += f"\n⚠️ **GPS OFF.** Activation signal sent to tablet."

    db.close()
    await update.message.reply_text(response, parse_mode="Markdown")

def main():
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing in .env file")
        return
    application = Application.builder().token(TOKEN).build()
    
    # Simple open handlers without security wrappers
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("find", find))
    
    print("Bot is listening (PUBLIC MODE)...")
    application.run_polling()

if __name__ == "__main__":
    main()
