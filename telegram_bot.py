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
BOT_TOKEN = "8412311785:AAG6KVmXrYZD8uFZPXg76jHJshn_MDDsEGQ"
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
        "**Step 1:** Choose a trading pair to analyze:"
    )
    
    await update.message.reply_text(
        welcome_message, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def pair_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle trading pair selection and show timeframes."""
    query = update.callback_query
    await query.answer()
    
    selected_pair = query.data.split("_")[1]
    context.user_data['selected_pair'] = selected_pair
    
    keyboard = [[InlineKeyboardButton(tf.upper(), callback_data=f"tf_{tf}") for tf in TIMEFRAMES]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"✅ **Selected Pair:** {selected_pair}\n\n"
        f"**Step 2:** Choose analysis timeframe:"
    )
    
    await query.edit_message_text(
        message, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def timeframe_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timeframe selection and perform analysis."""
    query = update.callback_query
    await query.answer()
    
    selected_tf = query.data.split("_")[1]
    selected_pair = context.user_data.get('selected_pair')
    
    # Show processing message
    processing_msg = (
        f"🔄 **Analyzing {selected_pair} on {selected_tf.upper()} timeframe**\n\n"
        f"⏳ Fetching live market data...\n"
        f"📊 Running technical analysis..."
    )
    
    await query.edit_message_text(processing_msg, parse_mode='Markdown')
    
    try:
        # Call the analysis API
        response = requests.get(
            f"{API_BASE_URL}/analyze",
            params={'pairs': selected_pair, 'tf': selected_tf},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['results'] and len(data['results']) > 0:
                result = data['results'][0]
                
                # Check if there's an error
                if 'error' in result:
                    error_msg = (
                        f"⚠️ **Analysis Issue**\n\n"
                        f"**Pair:** {selected_pair}\n"
                        f"**Error:** {result['error']}\n\n"
                        f"This usually means insufficient market data."
                    )
                    keyboard = [[InlineKeyboardButton("🔄 Try Another Pair", callback_data="restart")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        error_msg,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    # Format successful analysis
                    analysis_message = format_analysis_result(result)
                    
                    keyboard = [[InlineKeyboardButton("🔄 New Analysis", callback_data="restart")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        analysis_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
            else:
                raise Exception("No results returned from API")
                
        else:
            raise Exception(f"API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        error_msg = (
            "⏰ **Request Timeout**\n\n"
            "The analysis is taking longer than expected.\n"
            "Please try again or choose a different timeframe."
        )
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except requests.exceptions.ConnectionError:
        error_msg = (
            "🔌 **Connection Error**\n\n"
            "Cannot connect to analysis server.\n"
            "Make sure the API server is running on localhost:8000"
        )
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        error_msg = (
            "❌ **Analysis Failed**\n\n"
            f"**Error:** {str(e)}\n\n"
            "Please try again or contact support."
        )
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def format_analysis_result(result):
    """Format the analysis result for Telegram display."""
    pair = result.get('pair', 'N/A')
    direction = result.get('direction', 'HOLD')
    entry = result.get('entry', 0)
    confidence = result.get('confidence', 0)
    
    # Direction emoji and formatting
    if direction == 'BUY':
        direction_emoji = "🟢"
        signal_text = "**BUY SIGNAL**"
    elif direction == 'SELL':
        direction_emoji = "🔴"
        signal_text = "**SELL SIGNAL**"
    else:
        direction_emoji = "🟡"
        signal_text = "**HOLD POSITION**"
    
    # Build the message
    message = f"{direction_emoji} **FOREX ANALYSIS** {direction_emoji}\n\n"
    message += f"📈 **Pair:** {pair}\n"
    message += f"⚡ **Signal:** {signal_text}\n"
    message += f"💰 **Entry Price:** {entry}\n"
    message += f"🎯 **Confidence:** {confidence}%\n"
    
    # Add risk management info if available
    if result.get('stop_loss') and result.get('take_profit'):
        message += f"\n**📊 Risk Management:**\n"
        message += f"🛑 **Stop Loss:** {result['stop_loss']}\n"
        message += f"🎯 **Take Profit:** {result['take_profit']}\n"
        message += f"📏 **SL Distance:** {result.get('sl_pips', 0)} pips\n"
        message += f"📏 **TP Distance:** {result.get('tp_pips', 0)} pips\n"
        message += f"⚖️ **Risk:Reward:** 1:{result.get('rr', 0)}\n"
    
    # Add technical analysis reasons
    reasons = result.get('reasons', [])
    if reasons:
        message += f"\n**📋 Technical Analysis:**\n"
        for reason in reasons[:4]:  # Limit to 4 reasons for readability
            message += f"• {reason}\n"
    
    # Add timestamp
    message += f"\n⏰ **Analysis Time:** {datetime.now().strftime('%H:%M:%S')}"
    
    return message

async def restart_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the analysis process from the beginning."""
    query = update.callback_query
    await query.answer()
    
    # Clear stored user data
    context.user_data.clear()
    
    # Simulate the start command by recreating the interface
    keyboard = []
    for i in range(0, len(TRADING_PAIRS), 2):
        row = []
        for j in range(2):
            if i + j < len(TRADING_PAIRS):
                pair = TRADING_PAIRS[i + j]
                row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    restart_message = (
        "🔄 **Starting New Analysis**\n\n"
        "**Step 1:** Choose a trading pair to analyze:"
    )
    
    await query.edit_message_text(
        restart_message,
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
