import os
import gc
import sys
import subprocess
import importlib.util

# 1. Auto-Install Requirement (Agar requirements.txt na ho tab bhi chalega)
if importlib.util.find_spec("telegram") is None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "python-telegram-bot==21.6"]
    )

import asyncio
import logging
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Console logs ko clean rakhne ke liye
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Aapke dono Bot Tokens
TOKEN_1 = "8974303184:AAEHdxt8vCGmFx4XurGdb5ubTMfSfmV_-PE"
TOKEN_2 = "8824940007:AAFyn4h_YCpeY5lq293csaQCFT0CtwpGPw0"

# --- RENDER WEB SERVER (Port Error aur Cron-Job Ping ke liye) ---
async def health_check(request):
    return web.Response(text="Bots are running 24/7 on Render!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Render Web Server port {port} par live hai.")
    return runner

# --- RAM CLEANER (512MB Render limit crash se bachne ke liye) ---
async def ram_cleaner_loop():
    while True:
        await asyncio.sleep(60)
        gc.collect()

# Global Error Handler (Taaki chat me koi error reply na jaye)
async def silent_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Handled background error: {context.error}")

# --- BOT 1 KE COMMANDS ---
async def start_bot1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Namaste! Bot 1 ab 24/7 live hai.")

async def reply_bot1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Bot 1 ne receive kiya: {update.message.text}")

# --- BOT 2 KE COMMANDS ---
async def start_bot2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Hello! Bot 2 bhi ab 24/7 live hai.")

async def reply_bot2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(f"Bot 2 ne receive kiya: {update.message.text}")

# --- DONO BOTS KO EK SAATH START KARNE KA ENGINE ---
async def start_single_bot(token: str, start_handler, text_handler, bot_name: str):
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(silent_error_handler)
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info(f"{bot_name} successfully start ho gaya hai!")
    return app

async def main():
    # Render port bind karein taaki deployment fail na ho
    web_runner = await start_web_server()
    
    # Dono bots aur RAM cleaner start karein
    app1 = await start_single_bot(TOKEN_1, start_bot1, reply_bot1, "Bot 1")
    app2 = await start_single_bot(TOKEN_2, start_bot2, reply_bot2, "Bot 2")
    cleaner_task = asyncio.create_task(ram_cleaner_loop())

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        cleaner_task.cancel()
        for app in (app1, app2):
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
        await web_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
  
