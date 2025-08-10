import os
import logging
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forex_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration class for reading environment variables
class Config:
    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.forex_api_key = os.getenv('FOREX_API_KEY')
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
    def validate(self):
        """Validate that all required config values are present"""
        missing = []
        if not self.telegram_bot_token:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not self.telegram_chat_id:
            missing.append('TELEGRAM_CHAT_ID')
        if not self.forex_api_key:
            missing.append('FOREX_API_KEY')
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Initialize config
config = Config()

# FastAPI app initialization
app = FastAPI(
    title="AI Forex Bot API",
    description="FastAPI endpoints for AI-powered forex trading bot with Telegram alerts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ForexSignal(BaseModel):
    pair: str
    action: str  # BUY, SELL, HOLD
    price: float
    confidence: float
    timestamp: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class TelegramAlert(BaseModel):
    message: str
    priority: Optional[str] = "normal"  # low, normal, high, urgent

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str

# Telegram notification service
class TelegramService:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
    
    def format_forex_signal(self, signal: ForexSignal) -> str:
        """Format forex signal for Telegram message"""
        emoji = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "🟡"
        
        message = f"{emoji} <b>FOREX SIGNAL</b> {emoji}\n\n"
        message += f"📈 <b>Pair:</b> {signal.pair}\n"
        message += f"⚡ <b>Action:</b> {signal.action}\n"
        message += f"💰 <b>Price:</b> {signal.price}\n"
        message += f"🎯 <b>Confidence:</b> {signal.confidence:.2%}\n"
        
        if signal.stop_loss:
            message += f"🛑 <b>Stop Loss:</b> {signal.stop_loss}\n"
        if signal.take_profit:
            message += f"🎯 <b>Take Profit:</b> {signal.take_profit}\n"
        
        message += f"⏰ <b>Time:</b> {signal.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return message

# Initialize Telegram service
telegram_service = None
if config.telegram_bot_token and config.telegram_chat_id:
    telegram_service = TelegramService(config.telegram_bot_token, config.telegram_chat_id)

# Background task for sending alerts
async def send_telegram_alert(message: str):
    """Background task to send Telegram alerts"""
    if telegram_service:
        await telegram_service.send_message(message)
    else:
        logger.warning("Telegram service not configured, alert not sent")

# API Endpoints
@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Detailed health check"""
    logger.info("Detailed health check requested")
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/forex/signal")
async def create_forex_signal(signal: ForexSignal, background_tasks: BackgroundTasks):
    """Create and process a new forex signal"""
    try:
        logger.info(f"Received forex signal: {signal.pair} - {signal.action} at {signal.price}")
        
        # Add timestamp if not provided
        if not signal.timestamp:
            signal.timestamp = datetime.now().isoformat()
        
        # Format and send Telegram alert
        if telegram_service:
            alert_message = telegram_service.format_forex_signal(signal)
            background_tasks.add_task(send_telegram_alert, alert_message)
        
        # Log the signal
        logger.info(f"Forex signal processed: {signal.dict()}")
        
        return {
            "status": "success",
            "message": "Forex signal processed successfully",
            "signal_id": f"{signal.pair}_{int(datetime.now().timestamp())}",
            "telegram_alert_sent": telegram_service is not None
        }
        
    except Exception as e:
        logger.error(f"Error processing forex signal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process signal: {str(e)}")

@app.post("/alerts/telegram")
async def send_custom_alert(alert: TelegramAlert, background_tasks: BackgroundTasks):
    """Send custom Telegram alert"""
    try:
        logger.info(f"Custom alert requested: {alert.priority} priority")
        
        if not telegram_service:
            raise HTTPException(status_code=503, detail="Telegram service not configured")
        
        # Format message based on priority
        priority_emoji = {
            "low": "ℹ️",
            "normal": "📝",
            "high": "⚠️",
            "urgent": "🚨"
        }
        
        emoji = priority_emoji.get(alert.priority, "📝")
        formatted_message = f"{emoji} <b>ALERT</b> {emoji}\n\n{alert.message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        background_tasks.add_task(send_telegram_alert, formatted_message)
        
        logger.info("Custom alert queued for sending")
        
        return {
            "status": "success",
            "message": "Alert queued for sending",
            "priority": alert.priority
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending custom alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")

@app.get("/config/status")
async def get_config_status():
    """Get configuration status"""
    try:
        logger.info("Configuration status requested")
        
        return {
            "telegram_configured": bool(config.telegram_bot_token and config.telegram_chat_id),
            "forex_api_configured": bool(config.forex_api_key),
            "debug_mode": config.debug_mode,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting config status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get config status: {str(e)}")

@app.get("/logs/recent")
async def get_recent_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        logger.info(f"Recent logs requested: {lines} lines")
        
        log_file = "forex_bot.log"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "Log file not found"}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(recent_lines),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting AI Forex Bot API...")
    
    try:
        # Validate configuration (but don't fail if optional configs are missing)
        if config.telegram_bot_token and config.telegram_chat_id:
            logger.info("Telegram service configured")
        else:
            logger.warning("Telegram service not configured - alerts will not be sent")
        
        if config.forex_api_key:
            logger.info("Forex API configured")
        else:
            logger.warning("Forex API not configured")
        
        # Send startup notification
        if telegram_service:
            startup_message = "🚀 <b>AI Forex Bot Started</b> 🚀\n\nThe forex bot API is now running and ready to process signals."
            await telegram_service.send_message(startup_message)
        
        logger.info("AI Forex Bot API started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down AI Forex Bot API...")
    
    # Send shutdown notification
    if telegram_service:
        shutdown_message = "🛑 <b>AI Forex Bot Stopped</b> 🛑\n\nThe forex bot API has been shut down."
        await telegram_service.send_message(shutdown_message)
    
    logger.info("AI Forex Bot API shut down successfully")

if __name__ == "__main__":
    import uvicorn
    
    # Validate critical configuration on direct run
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Set the required environment variables and restart the application")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug_mode,
        log_level="info" if not config.debug_mode else "debug"
    )
