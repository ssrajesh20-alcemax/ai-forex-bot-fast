"""Configuration file for AI Forex Bot
Simple configuration that matches what core.py expects.
All sensitive information should be stored in environment variables.
"""
import os

# Trading pairs to analyze
PAIRS = [
    'EURUSD',
    'GBPUSD', 
    'USDJPY',
    'AUDUSD',
    'USDCAD',
    'NZDUSD',
    'EURGBP',
    'EURJPY'
]

# Timeframes to analyze
TIMEFRAMES = [
    '5m',
    '15m', 
    '4h'
]

# Signal generation thresholds
THRESHOLDS = {
    'buy_threshold': 2.0,    # Score >= 2.0 for BUY signal
    'sell_threshold': -2.0,  # Score <= -2.0 for SELL signal
    'min_confidence': 60.0   # Minimum confidence % to act on signal
}

# Risk management settings
RISK = {
    'atr_sl_mult': 2.0,     # Stop loss = entry +/- (2.0 * ATR)
    'atr_tp_mult': 3.0,     # Take profit = entry +/- (3.0 * ATR)
    'max_risk_percent': 2.0, # Maximum 2% risk per trade
    'min_rr_ratio': 1.5     # Minimum 1.5:1 risk-reward ratio
}

# Telegram configuration (load from environment variables)
TELEGRAM = {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'your-bot-token-here'),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID', 'your-chat-id-here'),
    'enabled': os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
}

# API configuration
API = {
    'forex_api_key': os.getenv('FOREX_API_KEY', 'your-forex-api-key'),
    'base_url': 'https://api.exchangerate-api.com/v4/latest/',
    'timeout': 30
}

# Main configuration dictionary that core.py expects
config = {
    'pairs': PAIRS,
    'timeframes': TIMEFRAMES, 
    'thresholds': THRESHOLDS,
    'risk': RISK,
    'telegram': TELEGRAM,
    'api': API
}

# Alternative variable names for backward compatibility
cfg = config  # core.py uses 'cfg'

if __name__ == '__main__':
    print('AI Forex Bot Configuration')
    print(f'Pairs: {len(PAIRS)}')
    print(f'Timeframes: {TIMEFRAMES}')
    print(f'Buy threshold: {THRESHOLDS["buy_threshold"]}')
    print(f'Sell threshold: {THRESHOLDS["sell_threshold"]}')
    print(f'ATR SL multiplier: {RISK["atr_sl_mult"]}')
    print(f'ATR TP multiplier: {RISK["atr_tp_mult"]}')
    print(f'Telegram enabled: {TELEGRAM["enabled"]}')
