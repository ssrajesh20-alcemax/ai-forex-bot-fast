# Telegram Bot for AI Forex Analysis
# This bot connects to the localhost:8000 analysis API
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "YourTelegramBotToken"
API_BASE_URL = "http://127.0.0.1:8000"

# Trading pairs and timeframes
TRADING_PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP', 'EURJPY']
TIMEFRAMES = ['5m', '15m', '4h']

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with trading pair selection."""
    keyboard = []
    for i in range(0, len(TRADING_PAIRS), 2):
        row = []
        for j in range(2):
            if i + j < len(TRADING_PAIRS):
                pair = TRADING_PAIRS[i + j]
                row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "🚀 **Welcome to AI Forex Bot!** 🚀\n\n"
        "Get professional forex analysis with:\n"
        "📈 Technical indicators (RSI, MACD, EMA)\n"
        "📊 Pattern recognition (double tops/bottoms)\n"
        "🎯 Calculated Stop Loss & Take Profit\n"
        "⚡ Risk/Reward ratios\n\n"
        "**Select a trading pair to begin:**"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def pair_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle trading pair selection and show timeframe options."""
    query = update.callback_query
    await query.answer()
    
    # Extract selected pair
    selected_pair = query.data.replace('pair_', '')
    context.user_data['selected_pair'] = selected_pair
    
    # Create timeframe selection keyboard
    keyboard = []
    for i in range(0, len(TIMEFRAMES), 3):
        row = []
        for j in range(3):
            if i + j < len(TIMEFRAMES):
                tf = TIMEFRAMES[i + j]
                row.append(InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📊 **{selected_pair}** selected!\n\n"
        f"📈 Choose your analysis timeframe:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def timeframe_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timeframe selection and get analysis."""
    query = update.callback_query
    await query.answer()
    
    # Extract selected timeframe
    selected_timeframe = query.data.replace('tf_', '')
    selected_pair = context.user_data.get('selected_pair')
    
    if not selected_pair:
        await query.edit_message_text(
            "❌ Error: Trading pair not found. Please restart with /start",
            parse_mode='Markdown'
        )
        return
    
    # Show loading message
    await query.edit_message_text(
        f"⏳ **Analyzing {selected_pair} on {selected_timeframe} timeframe...**\n\n"
        f"🔍 Gathering market data...\n"
        f"📊 Processing technical indicators...\n"
        f"🧠 Running AI analysis...",
        parse_mode='Markdown'
    )
    
    try:
        # Make API call to get analysis
        response = requests.get(
            f"{API_BASE_URL}/analyze/{selected_pair}/{selected_timeframe}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            analysis_message = format_analysis_response(data)
            
            # Create restart button
            keyboard = [[InlineKeyboardButton("🔄 New Analysis", callback_data="restart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                analysis_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            error_message = (
                f"❌ **Analysis Failed**\n\n"
                f"Status Code: {response.status_code}\n"
                f"Please ensure the analysis API is running on {API_BASE_URL}"
            )
            
            keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="restart")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
    except requests.exceptions.RequestException as e:
        error_message = (
            f"❌ **Connection Error**\n\n"
            f"Cannot reach analysis API at {API_BASE_URL}\n"
            f"Error: {str(e)}\n\n"
            f"Please ensure the API server is running."
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def format_analysis_response(data):
    """Format the analysis response for Telegram display."""
    try:
        # Basic information
        pair = data.get('pair', 'N/A')
        timeframe = data.get('timeframe', 'N/A')
        current_price = data.get('current_price', 0)
        timestamp = data.get('timestamp', '')
        
        # Analysis results
        analysis = data.get('analysis', {})
        direction = analysis.get('direction', 'HOLD')
        confidence = analysis.get('confidence', 0)
        
        # Technical indicators
        indicators = analysis.get('indicators', {})
        rsi = indicators.get('rsi', {}).get('value', 0)
        rsi_signal = indicators.get('rsi', {}).get('signal', 'NEUTRAL')
        
        macd = indicators.get('macd', {})
        macd_signal = macd.get('signal', 'NEUTRAL')
        macd_histogram = macd.get('histogram', 0)
        
        ema = indicators.get('ema', {})
        ema_signal = ema.get('signal', 'NEUTRAL')
        
        # Price levels
        levels = analysis.get('levels', {})
        support = levels.get('support', current_price)
        resistance = levels.get('resistance', current_price)
        
        # Trade suggestion (if direction is BUY or SELL)
        trade_info = ""
        if direction in ['BUY', 'SELL']:
            entry_price = analysis.get('entry_price', current_price)
            stop_loss = analysis.get('stop_loss', 0)
            take_profit = analysis.get('take_profit', 0)
            risk_reward = analysis.get('risk_reward', 0)
            
            trade_info = f"""
📋 **Trade Setup:**
🎯 Entry: {entry_price:.5f}
🛡️ Stop Loss: {stop_loss:.5f}
💰 Take Profit: {take_profit:.5f}
⚖️ Risk/Reward: 1:{risk_reward:.1f}
"""
        else:
            # Handle weak signal case - show 'No strong signal' or HOLD with reasons
            weak_signal_reasons = []
            
            # Check confidence level
            if confidence < 70:
                weak_signal_reasons.append(f"Low confidence ({confidence}%)")
            
            # Check indicator conflicts
            signals = [rsi_signal, macd_signal, ema_signal]
            if len(set(signals)) > 1:  # Multiple different signals
                weak_signal_reasons.append("Mixed indicator signals")
            
            # Check if all indicators are neutral
            if all(signal == 'NEUTRAL' for signal in signals):
                weak_signal_reasons.append("All indicators neutral")
            
            if weak_signal_reasons:
                direction = "No strong signal"
                trade_info = f"""
📋 **Recommendation: HOLD**
🔍 Reasons:
{'• ' + chr(10).join(weak_signal_reasons)}

⏳ Wait for clearer market conditions
"""
            else:
                trade_info = f"""
📋 **Recommendation: HOLD**
⏳ Current market conditions suggest waiting for better opportunities
"""
        
        # Format the complete message
        message = f"""
🎯 **{pair} Analysis - {timeframe}**
📊 Current Price: {current_price:.5f}
⏰ {timestamp}

🔍 **Market Direction: {direction}**
📈 Confidence: {confidence}%

📊 **Technical Indicators:**
• RSI ({rsi:.1f}): {rsi_signal}
• MACD: {macd_signal} (Hist: {macd_histogram:.5f})
• EMA: {ema_signal}

📍 **Key Levels:**
🔴 Resistance: {resistance:.5f}
🟢 Support: {support:.5f}
{trade_info}
💡 **Note:** This is AI-generated analysis. Always do your own research and manage risk appropriately.
"""
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting analysis response: {e}")
        return f"❌ Error formatting analysis data: {str(e)}"

async def restart_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the analysis process."""
    query = update.callback_query
    await query.answer()
    
    # Clear user data
    context.user_data.clear()
    
    # Show pair selection again
    keyboard = []
    for i in range(0, len(TRADING_PAIRS), 2):
        row = []
        for j in range(2):
            if i + j < len(TRADING_PAIRS):
                pair = TRADING_PAIRS[i + j]
                row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔄 **Starting new analysis...**\n\n"
        "📈 Select a trading pair:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button callbacks."""
    query = update.callback_query
    
    if query.data.startswith("pair_"):
        await pair_selected(update, context)
    elif query.data.startswith("tf_"):
        await timeframe_selected(update, context)
    elif query.data == "restart":
        await restart_analysis(update, context)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors gracefully."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ **An unexpected error occurred!**\n\nPlease try again with /start",
            parse_mode='Markdown'
        )

def main():
    """Start the Telegram bot."""
    logger.info("🤖 Starting AI Forex Telegram Bot...")
    logger.info(f"📡 Connecting to analysis API at {API_BASE_URL}")
    
    # Create the application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("✅ Telegram bot is ready! Users can now use /start")
    logger.info("📱 Go to @alce_trade_bot and type /start to begin!")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
