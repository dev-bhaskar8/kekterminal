import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from telegram import Update

from src.bot.commands import start, help_command, pools, trending, price, alert, removealert, activealerts
from src.services.alert_manager import AlertManager
from src.gecko.api import GeckoTerminalAPI

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

async def process_alerts(application: Application):
    """Process alerts every 10 seconds."""
    while True:
        try:
            alert_manager = application.bot_data.get('alert_manager')
            if not alert_manager:
                await asyncio.sleep(10)
                continue

            async with GeckoTerminalAPI() as api:
                new_trades = await alert_manager.process_alerts(api)
                
                for (chat_id, token_address), trade_data in new_trades.items():
                    try:
                        message, reply_markup = alert_manager.format_trade_message(trade_data, trade_data['ticker'])
                        image_url = trade_data.get('image_url', '')
                        
                        if image_url:
                            await application.bot.send_photo(
                                chat_id=chat_id,
                                photo=image_url,
                                caption=message,
                                parse_mode="MarkdownV2",
                                reply_markup=reply_markup
                            )
                        else:
                            await application.bot.send_message(
                                chat_id=chat_id,
                                text=message,
                                parse_mode="MarkdownV2",
                                reply_markup=reply_markup
                            )
                    except Exception as e:
                        logger.error(f"Error sending alert message: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error in alert processing loop: {str(e)}")
        
        await asyncio.sleep(10)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No token provided. Set TELEGRAM_BOT_TOKEN in .env file")
        return

    # Initialize the application
    application = Application.builder().token(token).build()

    # Initialize alert manager
    application.bot_data['alert_manager'] = AlertManager()

    # Add debug handler first
    application.add_handler(CommandHandler("debug", debug_handler))

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("trending", trending))
    application.add_handler(CommandHandler("pools", pools))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("alert", alert))
    application.add_handler(CommandHandler("removealert", removealert))
    application.add_handler(CommandHandler("activealerts", activealerts))

    # Start the alert processing loop
    application.job_queue.run_repeating(process_alerts, interval=10, first=0)

    # Start the bot
    logger.info("Starting bot...")
    
    # Start polling
    logger.info("Bot is ready to handle messages!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 