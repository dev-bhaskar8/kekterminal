from telegram import Update
from telegram.ext import ContextTypes
from src.gecko.api import GeckoTerminalAPI
import logging

logger = logging.getLogger(__name__)

def format_price(price: str) -> str:
    """Format price with appropriate precision."""
    if not price or price == "N/A":
        return "N/A"
    try:
        price_float = float(price)
        if price_float < 0.01:
            return f"${price_float:.8f}"
        elif price_float < 1:
            return f"${price_float:.4f}"
        else:
            return f"${price_float:.2f}"
    except (ValueError, TypeError):
        return "N/A"

def format_volume(volume: str) -> str:
    """Format volume with appropriate precision."""
    if not volume or volume == "N/A":
        return "N/A"
    try:
        volume_float = float(volume)
        if volume_float == 0:
            return "N/A"
        return f"${volume_float:,.2f}"
    except (ValueError, TypeError):
        return "N/A"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    logger.debug("Start command received")
    try:
        welcome_message = (
            "👋 Welcome to the Ronin Pools Bot!\n\n"
            "Available commands:\n"
            "/trending - Get top 10 trending pools on Ronin\n"
            "/pools - Get list of top Ronin pools\n"
            "/price <token_address> - Get price info for a token\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(welcome_message)
        logger.debug("Start command response sent")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    logger.debug("Help command received")
    await start(update, context)

async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top 10 trending pools on Ronin."""
    async with GeckoTerminalAPI() as api:
        data = await api.get_trending_ronin_pools()
        if not data or "data" not in data:
            await update.message.reply_text("❌ Failed to fetch trending pools data. Please try again later.")
            return

        pools_list = data["data"]
        if not pools_list:
            await update.message.reply_text("No trending pools found.")
            return

        message = "🔥 Top 10 Trending Pools on Ronin:\n\n"
        for pool in pools_list[:10]:  # Show top 10 trending pools
            try:
                attributes = pool["attributes"]
                relationships = pool["relationships"]
                
                # Get token symbols and addresses
                base_token_id = relationships["base_token"]["data"]["id"]
                quote_token_id = relationships["quote_token"]["data"]["id"]
                
                # Find token data in included section
                included = data.get("included", [])
                base_token = next((t for t in included if t["id"] == base_token_id), None)
                quote_token = next((t for t in included if t["id"] == quote_token_id), None)
                
                if not base_token or not quote_token:
                    logger.debug(f"Base or quote token not found. Base: {base_token}, Quote: {quote_token}")
                    continue
                
                base_symbol = base_token["attributes"]["symbol"]
                quote_symbol = quote_token["attributes"]["symbol"]
                
                # Get clean addresses (without ronin_ prefix)
                base_address = base_token_id.replace('ronin_', '')
                quote_address = quote_token_id.replace('ronin_', '')
                
                # Format price and volume data
                base_token_price = format_price(attributes.get("base_token_price_usd"))
                volume_24h = format_volume(attributes.get("volume_usd", {}).get("h24"))
                price_change_24h = attributes.get("price_change_percentage", {}).get("h24")
                price_change = f"{float(price_change_24h):.2f}%" if price_change_24h else "N/A"
                liquidity = format_volume(attributes.get("reserve_in_usd"))

                message += (
                    f"🔹 {base_symbol} / {quote_symbol}\n"
                    f"💧 Liquidity: {liquidity}\n"
                    f"📊 Volume 24h: {volume_24h}\n"
                    f"📈 Price: {base_token_price}\n"
                    f"🔄 Price Change 24h: {price_change}\n"
                    f"🏷️ {base_symbol} Address: `{base_address}`\n"
                    f"🏷️ {quote_symbol} Address: `{quote_address}`\n\n"
                )
            except Exception as e:
                logger.error(f"Error processing pool data: {str(e)}")
                continue

        if message == "🔥 Top 10 Trending Pools on Ronin:\n\n":
            await update.message.reply_text("❌ No valid pool data found.")
        else:
            await update.message.reply_text(message, parse_mode="Markdown")

async def pools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get list of top Ronin pools."""
    async with GeckoTerminalAPI() as api:
        data = await api.get_ronin_pools()
        if not data or "data" not in data:
            await update.message.reply_text("❌ Failed to fetch pools data. Please try again later.")
            return

        pools_list = data["data"]
        included = data.get("included", [])
        if not pools_list:
            await update.message.reply_text("No pools found.")
            return

        message = "🏊‍♂️ Top Ronin Pools:\n\n"
        for pool in pools_list[:10]:  # Show top 10 pools
            try:
                attributes = pool["attributes"]
                relationships = pool["relationships"]
                
                # Get token symbols and addresses
                base_token_id = relationships["base_token"]["data"]["id"]
                quote_token_id = relationships["quote_token"]["data"]["id"]
                
                base_token = next((t for t in included if t["id"] == base_token_id), None)
                quote_token = next((t for t in included if t["id"] == quote_token_id), None)
                
                if not base_token or not quote_token:
                    logger.debug(f"Base or quote token not found. Base: {base_token}, Quote: {quote_token}")
                    continue
                
                base_symbol = base_token["attributes"]["symbol"]
                quote_symbol = quote_token["attributes"]["symbol"]
                
                # Get clean addresses (without ronin_ prefix)
                base_address = base_token_id.replace('ronin_', '')
                quote_address = quote_token_id.replace('ronin_', '')
                
                # Format price and volume data
                volume_24h = format_volume(attributes.get("volume_usd", {}).get("h24"))
                liquidity = format_volume(attributes.get("reserve_in_usd"))

                message += (
                    f"🔹 {base_symbol} / {quote_symbol}\n"
                    f"💧 Liquidity: {liquidity}\n"
                    f"📊 Volume 24h: {volume_24h}\n"
                    f"🏷️ {base_symbol} Address: `{base_address}`\n"
                    f"🏷️ {quote_symbol} Address: `{quote_address}`\n\n"
                )
            except Exception as e:
                logger.error(f"Error processing pool data: {str(e)}")
                continue

        if message == "🏊‍♂️ Top Ronin Pools:\n\n":
            await update.message.reply_text("❌ No valid pool data found.")
        else:
            await update.message.reply_text(message, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get price information for a specific token."""
    if not context.args:
        await update.message.reply_text("❌ Please provide a token address.\nUsage: /price <token_address>")
        return

    token_address = context.args[0].lower()  # Convert to lowercase
    # Remove ronin_ prefix if present
    if token_address.startswith('ronin_'):
        token_address = token_address[6:]
    
    logger.debug(f"Processing price command for token: {token_address}")
    
    async with GeckoTerminalAPI() as api:
        data = await api.get_token_pools(token_address)
        if not data:
            await update.message.reply_text("❌ Failed to fetch token information. The token might not exist on Ronin network.")
            return
        
        if "data" not in data or not data["data"]:
            await update.message.reply_text(f"❌ No pools found for token address: {token_address}")
            return

        pools = data["data"]
        included = data.get("included", [])
        
        # Get token info from included data
        token_info = next((t for t in included if t["type"] == "token" and t["id"].lower() == f"ronin_{token_address}"), None)
        if not token_info:
            logger.debug(f"Token info not found in included data: {included}")
            await update.message.reply_text(f"❌ Token information not found for address: {token_address}")
            return
            
        token_symbol = token_info["attributes"]["symbol"]
        message = f"💰 Price Info for {token_symbol}:\n\n"
        
        for pool in pools[:5]:  # Show top 5 pools
            try:
                attributes = pool["attributes"]
                relationships = pool["relationships"]
                
                # Get token symbols and addresses
                base_token_id = relationships["base_token"]["data"]["id"]
                quote_token_id = relationships["quote_token"]["data"]["id"]
                
                base_token = next((t for t in included if t["id"] == base_token_id), None)
                quote_token = next((t for t in included if t["id"] == quote_token_id), None)
                
                if not base_token or not quote_token:
                    logger.debug(f"Base or quote token not found. Base: {base_token}, Quote: {quote_token}")
                    continue
                
                base_symbol = base_token["attributes"]["symbol"]
                quote_symbol = quote_token["attributes"]["symbol"]
                
                # Get clean addresses (without ronin_ prefix)
                base_address = base_token_id.replace('ronin_', '')
                quote_address = quote_token_id.replace('ronin_', '')
                
                # Format price and volume data
                base_token_price = format_price(attributes.get("base_token_price_usd"))
                volume_24h = format_volume(attributes.get("volume_usd", {}).get("h24"))
                price_change_24h = attributes.get("price_change_percentage", {}).get("h24")
                price_change = f"{float(price_change_24h):.2f}%" if price_change_24h else "N/A"
                liquidity = format_volume(attributes.get("reserve_in_usd"))

                message += (
                    f"🔹 {base_symbol} / {quote_symbol}\n"
                    f"💧 Liquidity: {liquidity}\n"
                    f"📊 Volume 24h: {volume_24h}\n"
                    f"📈 Price: {base_token_price}\n"
                    f"🔄 Price Change 24h: {price_change}\n"
                    f"🏷️ {base_symbol} Address: `{base_address}`\n"
                    f"🏷️ {quote_symbol} Address: `{quote_address}`\n\n"
                )
            except Exception as e:
                logger.error(f"Error processing pool data: {str(e)}")
                continue

        if message == f"💰 Price Info for {token_symbol}:\n\n":
            await update.message.reply_text(f"❌ No valid pool data found for token: {token_symbol}")
        else:
            await update.message.reply_text(message, parse_mode="Markdown") 