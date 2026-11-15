import os
import gc
import sys
import threading
import subprocess
import importlib.util
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Auto-Install Required Library (Zero dependency issue)
def install_packages():
    if importlib.util.find_spec("telegram") is None:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", "python-telegram-bot==21.6"]
        )

install_packages()

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Clean Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Aapke dono Bot Tokens
TOKEN_1 = "8974303184:AAEHdxt8vCGmFx4XurGdb5ubTMfSfmV_-PE"
TOKEN_2 = "8824940007:AAFyn4h_YCpeY5lq293csaQCFT0CtwpGPw0"

# --- BUILT-IN HEALTH CHECK SERVER (Render Port Error Fix) ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bots are alive 24/7!")

    def log_message(self, format, *args):
        pass  # Console logs ko spam se bachane ke liye

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health server port {port} par start ho gaya hai.")
    server.serve_forever()

# --- RAM CLEANER (Render 512MB Limit Protection) ---
async def ram_cleaner():
    while True:
        await asyncio.sleep(60)
        gc.collect()

# --- SILENT ERROR HANDLER (Chat me koi error message nahi jayega) ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Ignored minor error: {context.error}")

# --- BOT 1 HANDLERS ---
async def start_bot1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Namaste! Bot 1 ab 24/7 live hai.")

async def reply_bot1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Bot 1 ne receive kiya: {update.message.text}")

# --- BOT 2 HANDLERS ---
async def start_bot2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Hello! Bot 2 bhi ab 24/7 live hai.")

async def reply_bot2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Bot 2 ne receive kiya: {update.message.text}")

# --- DUAL BOT ENGINE ---
async def init_bot(token: str, start_fn, text_fn, name: str):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_fn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_fn))
    app.add_error_handler(error_handler)
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info(f"{name} successfully live ho gaya hai!")
    return app

async def main():
    # Background thread me Render Port Server chalu karein
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Dono bots ko start karein
    app1 = await init_bot(TOKEN_1, start_bot1, reply_bot1, "Bot 1")
    app2 = await init_bot(TOKEN_2, start_bot2, reply_bot2, "Bot 2")
    
    # RAM cleaner start karein
    cleaner = asyncio.create_task(ram_cleaner())

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        cleaner.cancel()
        for app in (app1, app2):
            await app.updater.stop()
            await app.stop()
            await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
    
