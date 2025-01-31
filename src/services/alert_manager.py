import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.gecko.api import GeckoTerminalAPI

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        # Structure: {chat_id: {token_address: {'ticker': str, 'pool_address': str, 'last_trade_id': str, 'last_check': timestamp, 'trade_type': str, 'min_amount': float, 'image_url': str, 'ref_code': str}}}
        self.alerts = {}
        
    def add_alert(self, chat_id: int, token_address: str, ticker: str, pool_address: str, trade_type: str = None, min_amount: float = 0, image_url: str = None, ref_code: str = None) -> bool:
        """Add a new alert for a token in a chat.
        trade_type: 'buy', 'sell', or None (for both)
        min_amount: minimum trade amount to report (0 for all trades)
        image_url: URL of the token's image
        ref_code: Optional referral code for the trade button
        """
        if chat_id not in self.alerts:
            self.alerts[chat_id] = {}
            
        self.alerts[chat_id][token_address] = {
            'ticker': ticker,
            'pool_address': pool_address,
            'last_trade_id': None,
            'last_check': datetime.now(),
            'trade_type': trade_type.lower() if trade_type else None,
            'min_amount': float(min_amount),
            'image_url': image_url,
            'ref_code': ref_code
        }
        return True
        
    def remove_alert(self, chat_id: int, token_address: str) -> bool:
        """Remove an alert for a token in a chat."""
        if chat_id in self.alerts and token_address in self.alerts[chat_id]:
            del self.alerts[chat_id][token_address]
            if not self.alerts[chat_id]:  # If no more alerts for this chat
                del self.alerts[chat_id]
            return True
        return False
        
    def get_active_alerts(self, chat_id: int) -> Dict:
        """Get all active alerts for a chat."""
        return self.alerts.get(chat_id, {})
        
    def get_alert(self, chat_id: int, token_address: str) -> Optional[Dict]:
        """Get specific alert details."""
        return self.alerts.get(chat_id, {}).get(token_address)
        
    async def process_alerts(self, api: GeckoTerminalAPI) -> Dict[Tuple[int, str], Dict]:
        """Process all alerts and return new trades.
        Returns: {(chat_id, token_address): trade_data}
        """
        new_trades = {}
        current_time = datetime.now()
        
        for chat_id in list(self.alerts.keys()):
            for token_address, alert_data in list(self.alerts[chat_id].items()):
                try:
                    # Check if 10 seconds have passed since last check
                    time_since_last_check = (current_time - alert_data['last_check']).total_seconds()
                    if time_since_last_check < 10:
                        continue

                    trades_data = await api.get_pool_trades(alert_data['pool_address'])
                    if not trades_data or 'data' not in trades_data or not trades_data['data']:
                        alert_data['last_check'] = current_time
                        continue
                        
                    latest_trade = trades_data['data'][0]
                    latest_trade_id = latest_trade['id']
                    
                    # Only send if this is a new trade
                    if latest_trade_id != alert_data.get('last_trade_id'):
                        # Check trade type filter
                        trade_type = latest_trade['attributes'].get('kind')
                        if alert_data['trade_type'] and trade_type != alert_data['trade_type']:
                            alert_data['last_trade_id'] = latest_trade_id
                            alert_data['last_check'] = current_time
                            continue

                        # Check minimum amount
                        is_buy = trade_type == 'buy'
                        amount = float(latest_trade['attributes'].get(
                            'to_token_amount' if is_buy else 'from_token_amount', '0'
                        ))
                        if amount < alert_data['min_amount']:
                            alert_data['last_trade_id'] = latest_trade_id
                            alert_data['last_check'] = current_time
                            continue

                        alert_data['last_trade_id'] = latest_trade_id
                        alert_data['last_check'] = current_time
                        new_trades[(chat_id, token_address)] = {
                            'trade': latest_trade,
                            'ticker': alert_data['ticker'],
                            'image_url': alert_data.get('image_url', '')  # Include image URL in trade data
                        }
                    else:
                        # Update last check time even if no new trade
                        alert_data['last_check'] = current_time
                        
                except Exception as e:
                    logger.error(f"Error processing alert for {token_address} in chat {chat_id}: {str(e)}")
                    continue
                    
        return new_trades

    def get_trade_size_label(self, amount_usd: float) -> str:
        """Get the appropriate size label based on trade amount in USD."""
        if amount_usd <= 100:  # $1 - $100
            return "🦐 Shrimp"
        elif amount_usd <= 1000:  # $101 - $1,000
            return "🐟 Fish"
        elif amount_usd <= 2000:  # $1,001 - $2,000
            return "🐬 Dolphin"
        else:  # $2,001+
            return "🐋 Whale"

    def format_trade_message(self, trade_data: Dict, ticker: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Format trade message with size labels and return message and keyboard markup."""
        trade = trade_data['trade']
        attributes = trade['attributes']
        
        # Determine if it's a buy or sell
        is_buy = attributes.get('kind') == 'buy'
        
        # Get the appropriate amount and price based on trade type
        if is_buy:
            amount = float(attributes.get('to_token_amount', '0'))
            price = float(attributes.get('price_to_in_usd', '0'))
            token_address = attributes.get('to_token_address', '')
        else:
            amount = float(attributes.get('from_token_amount', '0'))
            price = float(attributes.get('price_from_in_usd', '0'))
            token_address = attributes.get('from_token_address', '')
        
        # Calculate total value in USD
        total_value_usd = amount * price
        
        # Get size label
        size_label = self.get_trade_size_label(total_value_usd)
        
        # Format the trade type with emoji
        trade_type = "🟢 Buy" if is_buy else "🔴 Sell"
        
        # Format amount with appropriate precision
        if amount < 0.0001:
            formatted_amount = f"{amount:.8f}"
        elif amount < 0.01:
            formatted_amount = f"{amount:.6f}"
        elif amount < 1:
            formatted_amount = f"{amount:.4f}"
        else:
            formatted_amount = f"{amount:,.2f}"
        
        # Format price with appropriate precision
        if price < 0.00000001:
            formatted_price = f"${price:.12f}"
        elif price < 0.01:
            formatted_price = f"${price:.8f}"
        elif price < 1:
            formatted_price = f"${price:.6f}"
        else:
            formatted_price = f"${price:.4f}"
        
        # Format total value
        formatted_value = f"${total_value_usd:,.2f}"

        # Extract token name and symbol from ticker
        token_parts = ticker.split(' (')
        token_name = token_parts[0]
        token_symbol = token_parts[1].rstrip(')')
        
        # Escape special characters for MarkdownV2
        def escape_markdown(text):
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        token_name = escape_markdown(token_name)
        token_symbol = escape_markdown(token_symbol)
        formatted_amount = escape_markdown(formatted_amount)
        formatted_price = escape_markdown(formatted_price)
        formatted_value = escape_markdown(formatted_value)
        token_address = escape_markdown(token_address)
        
        # Build the message without image URL
        message = (
            f"{trade_type} Alert\\! 🚀\n"
            f"Token: {token_name} \\({token_symbol}\\)\n"
            f"`{token_address}`\n"
            f"Amount: {formatted_amount} {token_symbol}\n"
            f"Price: {formatted_price}\n"
            f"Total Value: {formatted_value}\n"
            f"{size_label}"
        )

        # Get referral code from trade data
        ref_code = trade_data.get('ref_code', 'XXXX')
        trade_url = f"https://t.me/ronin_kek_bot?start={ref_code}"

        # Create inline keyboard with buttons
        keyboard = [
            [
                InlineKeyboardButton("📊 Chart", url=f"https://geckoterminal.com/ronin/tokens/{token_address}"),
                InlineKeyboardButton("💰 Trade", url=trade_url)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return message, reply_markup 