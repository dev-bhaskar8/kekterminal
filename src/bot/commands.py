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
        if price_float < 0.00000001:
            return f"${price_float:.12f}"
        elif price_float < 0.01:
            return f"${price_float:.8f}"
        elif price_float < 1:
            return f"${price_float:.6f}"
        else:
            return f"${price_float:.4f}"
    except (ValueError, TypeError):
        return "N/A"

def format_mcap(mcap: str) -> str:
    """Format market cap with appropriate precision and suffix."""
    if not mcap or mcap == "N/A":
        return "N/A"
    try:
        mcap_float = float(mcap)
        if mcap_float == 0:
            return "N/A"
        elif mcap_float >= 1_000_000_000:  # Billions
            return f"${mcap_float/1_000_000_000:.2f}B"
        elif mcap_float >= 1_000_000:  # Millions
            return f"${mcap_float/1_000_000:.2f}M"
        elif mcap_float >= 1_000:  # Thousands
            return f"${mcap_float/1_000:.2f}K"
        else:
            return f"${mcap_float:,.2f}"
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
            "🚀 Welcome to KEK Terminal Bot!\n\n"
            "Your ultimate companion for tracking Ronin trades and pools.\n\n"
            "🛠 Available Commands:\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📊 Market Data:\n"
            "/trending - Top 10 trending pools on Ronin\n"
            "/pools - List of top Ronin pools\n"
            "/price <token_address> - Get detailed price info\n\n"
            "⚡️ Trade Alerts:\n"
            "/alert <token_address> [buy|sell] [min_amount] - Set alerts\n"
            "/removealert <token_address> - Remove alerts\n"
            "/activealerts - View your active alerts\n"
            "/help - Show this help message\n\n"
            "🏆 Trade Size Categories:\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🦐 Shrimp: $1 - $100\n"
            "🐟 Fish: $101 - $1,000\n"
            "🐬 Dolphin: $1,001 - $2,000\n"
            "🐋 Whale: $2,001+\n\n"
            "📝 Alert Examples:\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "• /alert 0x123... - Track all trades\n"
            "• /alert 0x123... buy - Track only buys\n"
            "• /alert 0x123... sell 100 - Track sells of 100+ tokens\n"
            "• /alert 0x123... buy 50 - Track buys of 50+ tokens\n\n"
            "💡 Alert Features:\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "• Auto-fetches token name and symbol\n"
            "• Includes token image in alerts\n"
            "• Shows trade size category\n"
            "• Monitors most liquid pool\n"
            "• Real-time price and value\n\n"
            "Made with 💜 by KEK Terminal"
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

        message = "🔥 KEK Terminal - Top Trending Pools\n━━━━━━━━━━━━━━━━━━\n\n"
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
                
                # Get market cap or use FDV as fallback
                market_cap = base_token["attributes"].get("market_cap_usd")
                if not market_cap or market_cap == "null":
                    market_cap = attributes.get("fdv_usd")
                base_mcap = format_mcap(market_cap)

                message += (
                    f"🔹 {base_symbol} / {quote_symbol}\n"
                    f"💧 Liquidity: {liquidity}\n"
                    f"📊 Volume 24h: {volume_24h}\n"
                    f"📈 Price: {base_token_price}\n"
                    f"💰 Market Cap: {base_mcap}\n"
                    f"🔄 Price Change 24h: {price_change}\n\n"
                )
            except Exception as e:
                logger.error(f"Error processing pool data: {str(e)}")
                continue

        if message == "🔥 KEK Terminal - Top Trending Pools\n━━━━━━━━━━━━━━━━━━\n\n":
            await update.message.reply_text("❌ No valid pool data found.")
        else:
            await update.message.reply_text(message)

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

        message = "🏊‍♂️ KEK Terminal - Top Pools\n━━━━━━━━━━━━━━━━━━\n\n"
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
                base_token_price = format_price(attributes.get("base_token_price_usd"))
                volume_24h = format_volume(attributes.get("volume_usd", {}).get("h24"))
                liquidity = format_volume(attributes.get("reserve_in_usd"))
                
                # Get market cap or use FDV as fallback
                market_cap = base_token["attributes"].get("market_cap_usd")
                if not market_cap or market_cap == "null":
                    market_cap = attributes.get("fdv_usd")
                base_mcap = format_mcap(market_cap)

                message += (
                    f"🔹 {base_symbol} / {quote_symbol}\n"
                    f"💧 Liquidity: {liquidity}\n"
                    f"📊 Volume 24h: {volume_24h}\n"
                    f"📈 Price: {base_token_price}\n"
                    f"💰 Market Cap: {base_mcap}\n\n"
                )
            except Exception as e:
                logger.error(f"Error processing pool data: {str(e)}")
                continue

        if message == "🏊‍♂️ KEK Terminal - Top Pools\n━━━━━━━━━━━━━━━━━━\n\n":
            await update.message.reply_text("❌ No valid pool data found.")
        else:
            await update.message.reply_text(message)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get price information for a specific token."""
    if not context.args:
        await update.message.reply_text(
            "📊 KEK Terminal - Price Info\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "❌ Please provide a token address.\n"
            "Usage: /price <token_address>"
        )
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
        message = f"📊 KEK Terminal - {token_symbol} Price Info\n━━━━━━━━━━━━━━━━━━\n\n"
        
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
                
                # Format price and volume data
                base_token_price = format_price(attributes.get("base_token_price_usd"))
                volume_24h = format_volume(attributes.get("volume_usd", {}).get("h24"))
                price_change_24h = attributes.get("price_change_percentage", {}).get("h24")
                price_change = f"{float(price_change_24h):.2f}%" if price_change_24h else "N/A"
                liquidity = format_volume(attributes.get("reserve_in_usd"))
                
                # Get market cap or use FDV as fallback
                market_cap = base_token["attributes"].get("market_cap_usd")
                if not market_cap or market_cap == "null":
                    market_cap = attributes.get("fdv_usd")
                base_mcap = format_mcap(market_cap)

                message += (
                    f"🔹 {base_symbol} / {quote_symbol}\n"
                    f"💧 Liquidity: {liquidity}\n"
                    f"📊 Volume 24h: {volume_24h}\n"
                    f"📈 Price: {base_token_price}\n"
                    f"💰 Market Cap: {base_mcap}\n"
                    f"🔄 Price Change 24h: {price_change}\n\n"
                )
            except Exception as e:
                logger.error(f"Error processing pool data: {str(e)}")
                continue

        if message == f"📊 KEK Terminal - {token_symbol} Price Info\n━━━━━━━━━━━━━━━━━━\n\n":
            await update.message.reply_text("❌ No valid pool data found.")
        else:
            await update.message.reply_text(message)

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set up an alert for a token."""
    if not context.args:
        await update.message.reply_text(
            "⚡️ KEK Terminal - Trade Alerts\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "❌ Please provide the token address.\n"
            "Usage: /alert <token_address> [buy|sell] [min_amount]"
        )
        return

    token_address = context.args[0].lower()
    trade_type = context.args[1].lower() if len(context.args) > 1 else None
    min_amount = float(context.args[2]) if len(context.args) > 2 else 0

    # Remove ronin_ prefix if present
    if token_address.startswith('ronin_'):
        token_address = token_address[6:]

    # Get alert manager from bot data
    alert_manager = context.application.bot_data.get('alert_manager')
    if not alert_manager:
        await update.message.reply_text("❌ Alert system is not initialized.")
        return

    async with GeckoTerminalAPI() as api:
        # Get token info to fetch name, symbol and image URL
        token_info = await api.get_token_info(token_address)
        if not token_info or 'data' not in token_info:
            await update.message.reply_text("❌ Failed to fetch token information.")
            return

        token_data = token_info['data']['attributes']
        token_name = token_data.get('name', '')
        token_symbol = token_data.get('symbol', '')
        image_url = token_data.get('image_url')

        # Format the token display name
        ticker = f"{token_name} ({token_symbol})"

        # Get token pools to find the most liquid one
        pools_data = await api.get_token_pools(token_address)
        if not pools_data or 'data' not in pools_data or not pools_data['data']:
            await update.message.reply_text("❌ Failed to find pools for this token.")
            return

        # Find the most liquid pool
        most_liquid_pool = None
        highest_liquidity = 0
        for pool in pools_data['data']:
            liquidity = float(pool['attributes'].get('reserve_in_usd', 0))
            if liquidity > highest_liquidity:
                highest_liquidity = liquidity
                most_liquid_pool = pool

        if not most_liquid_pool:
            await update.message.reply_text("❌ No valid pool found for this token.")
            return

        pool_address = most_liquid_pool['id'].replace('ronin_', '')

        # Add the alert with image URL
        alert_manager.add_alert(
            update.effective_chat.id,
            token_address,
            ticker,
            pool_address,
            trade_type,
            min_amount,
            image_url
        )

        # Format response message
        trade_type_msg = f" ({trade_type.upper()} only)" if trade_type else ""
        min_amount_msg = f" (min. {min_amount} {token_symbol})" if min_amount > 0 else ""
        
        await update.message.reply_text(
            f"✅ Alert set for {ticker}{trade_type_msg}{min_amount_msg}\n"
            f"Token Address: {token_address}\n"
            f"Pool Address: {pool_address}"
        )

async def removealert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an alert for a token."""
    if not context.args:
        await update.message.reply_text(
            "⚡️ KEK Terminal - Remove Alert\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "❌ Please provide the token address.\n"
            "Usage: /removealert <token_address>"
        )
        return

    token_address = context.args[0].lower()
    if token_address.startswith('ronin_'):
        token_address = token_address[6:]

    chat_id = update.effective_chat.id
    alert_manager = context.bot_data.get('alert_manager')
    
    if alert_manager.remove_alert(chat_id, token_address):
        await update.message.reply_text("✅ Alert removed successfully!")
    else:
        await update.message.reply_text("❌ No active alert found for this token.")

async def activealerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active alerts in the channel."""
    chat_id = update.effective_chat.id
    alert_manager = context.bot_data.get('alert_manager')
    alerts = alert_manager.get_active_alerts(chat_id)

    if not alerts:
        await update.message.reply_text(
            "⚡️ KEK Terminal - Active Alerts\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "No active alerts in this chat."
        )
        return

    message = "⚡️ KEK Terminal - Active Alerts\n━━━━━━━━━━━━━━━━━━\n\n"
    for token_address, alert_data in alerts.items():
        message += f"• {alert_data['ticker']} (`{token_address}`)\n"

    await update.message.reply_text(message, parse_mode="Markdown") 