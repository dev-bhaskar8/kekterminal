import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from telegram import Update

from src.bot.commands import start, help_command, pools, trending, price

# Load environment variables
load_dotenv()

# Configure logging - Set to DEBUG level
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG  # Changed to DEBUG for more detailed logs
)
logger = logging.getLogger(__name__)

async def debug_handler(update: Update, context):
    """Debug handler to log all updates."""
    logger.debug(f"Received update: {update}")
    await update.message.reply_text("Debug message received!")
    return True

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No token provided. Set TELEGRAM_BOT_TOKEN in .env file")
        return

    # Initialize the application
    application = Application.builder().token(token).build()

    # Add debug handler first
    application.add_handler(CommandHandler("debug", debug_handler))

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("trending", trending))
    application.add_handler(CommandHandler("pools", pools))
    application.add_handler(CommandHandler("price", price))

    # Start the bot
    logger.info("Starting bot...")
    
    # Start polling
    logger.info("Bot is ready to handle messages!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 