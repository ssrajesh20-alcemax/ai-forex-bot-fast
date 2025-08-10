"""Configuration file for AI Forex Bot

This file contains configuration settings for the forex trading bot.
All sensitive information (API keys, passwords, etc.) should be stored
in environment variables or a separate .env file.
"""

import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TradingConfig:
    """Configuration for trading parameters"""
    # Trading settings
    max_trade_amount: float = 1000.0  # Maximum amount per trade
    risk_percentage: float = 0.02  # Risk 2% of account per trade
    stop_loss_percentage: float = 0.01  # 1% stop loss
    take_profit_percentage: float = 0.02  # 2% take profit
    
    # Pairs to trade
    trading_pairs: List[str] = None
    
    def __post_init__(self):
        if self.trading_pairs is None:
            self.trading_pairs = [
                'EUR/USD',
                'GBP/USD',
                'USD/JPY',
                'AUD/USD',
                'USD/CAD'
            ]

@dataclass
class APIConfig:
    """Configuration for API connections"""
    # These should be loaded from environment variables
    broker_api_key: Optional[str] = None
    broker_api_secret: Optional[str] = None
    base_url: str = 'https://api.broker.com'  # Replace with actual broker API
    timeout: int = 30
    
    def __post_init__(self):
        # Load from environment variables
        self.broker_api_key = os.getenv('BROKER_API_KEY')
        self.broker_api_secret = os.getenv('BROKER_API_SECRET')

@dataclass
class AIConfig:
    """Configuration for AI/ML model settings"""
    model_path: str = 'models/forex_model.pkl'
    prediction_threshold: float = 0.7  # Confidence threshold for trades
    feature_window: int = 24  # Number of hours for feature calculation
    update_frequency: int = 3600  # Model update frequency in seconds

@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    # Database settings (use environment variables for sensitive info)
    database_url: Optional[str] = None
    table_prefix: str = 'forex_bot_'
    connection_timeout: int = 30
    
    def __post_init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///forex_bot.db')

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    log_level: str = 'INFO'
    log_file: str = 'logs/forex_bot.log'
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

@dataclass
class AppConfig:
    """Main application configuration"""
    # Environment settings
    environment: str = 'development'  # development, staging, production
    debug: bool = True
    
    # Component configurations
    trading: TradingConfig = None
    api: APIConfig = None
    ai: AIConfig = None
    database: DatabaseConfig = None
    logging: LoggingConfig = None
    
    def __post_init__(self):
        # Initialize sub-configurations if not provided
        if self.trading is None:
            self.trading = TradingConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.ai is None:
            self.ai = AIConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        
        # Adjust settings based on environment
        if self.environment == 'production':
            self.debug = False
            self.logging.log_level = 'WARNING'
        elif self.environment == 'development':
            self.debug = True
            self.logging.log_level = 'DEBUG'

# Default configuration instance
config = AppConfig()

# Helper functions
def load_config_from_env() -> AppConfig:
    """Load configuration from environment variables"""
    config = AppConfig()
    
    # Override with environment variables if they exist
    if os.getenv('ENVIRONMENT'):
        config.environment = os.getenv('ENVIRONMENT')
    
    if os.getenv('DEBUG'):
        config.debug = os.getenv('DEBUG').lower() in ('true', '1', 'yes')
    
    if os.getenv('MAX_TRADE_AMOUNT'):
        config.trading.max_trade_amount = float(os.getenv('MAX_TRADE_AMOUNT'))
    
    if os.getenv('RISK_PERCENTAGE'):
        config.trading.risk_percentage = float(os.getenv('RISK_PERCENTAGE'))
    
    return config

def validate_config(config: AppConfig) -> bool:
    """Validate configuration settings"""
    if not config.api.broker_api_key:
        print("Warning: BROKER_API_KEY not set in environment variables")
        return False
    
    if not config.api.broker_api_secret:
        print("Warning: BROKER_API_SECRET not set in environment variables")
        return False
    
    if config.trading.risk_percentage > 0.1:  # More than 10% risk
        print("Warning: Risk percentage is very high (>10%)")
        return False
    
    return True

if __name__ == '__main__':
    # Load and validate configuration
    app_config = load_config_from_env()
    if validate_config(app_config):
        print("Configuration loaded and validated successfully")
    else:
        print("Configuration validation failed")
    
    print(f"Environment: {app_config.environment}")
    print(f"Debug mode: {app_config.debug}")
    print(f"Trading pairs: {app_config.trading.trading_pairs}")
