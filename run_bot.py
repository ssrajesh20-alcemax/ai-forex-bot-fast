"""
AI Forex Bot Launcher
Starts both the FastAPI analysis server and Telegram bot in one terminal
"""

import subprocess
import sys
import time
import signal
import os
from threading import Thread

def run_api_server():
    """Run the FastAPI server."""
    print("🚀 Starting FastAPI Analysis Server...")
    try:
        # Run uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ API Server failed: {e}")
    except KeyboardInterrupt:
        print("🛑 API Server stopped by user")

def run_telegram_bot():
    """Run the Telegram bot."""
    print("🤖 Starting Telegram Bot...")
    # Wait a few seconds for API server to start
    time.sleep(3)
    
    try:
        # Run telegram bot
        subprocess.run([sys.executable, "telegram_bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Telegram Bot failed: {e}")
    except KeyboardInterrupt:
        print("🛑 Telegram Bot stopped by user")

def main():
    """Main launcher function."""
    print("=" * 60)
    print("🚀 AI Forex Bot - Complete System Launcher")
    print("=" * 60)
    print("📡 Starting FastAPI Analysis Server on http://127.0.0.1:8000")
    print("🤖 Starting Telegram Bot (@alce_trade_bot)")
    print("=" * 60)
    print()
    
    # Check if required files exist
    if not os.path.exists("api.py"):
        print("❌ Error: api.py not found!")
        print("Make sure you're running this from the correct directory.")
        sys.exit(1)
        
    if not os.path.exists("telegram_bot.py"):
        print("❌ Error: telegram_bot.py not found!")
        print("Make sure telegram_bot.py is in the same directory.")
        sys.exit(1)
    
    # Create processes list to track
    processes = []
    
    try:
        # Start FastAPI server
        print("🚀 Launching FastAPI server...")
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
        ])
        processes.append(("FastAPI Server", api_process))
        
        # Wait for server to start
        print("⏳ Waiting for API server to initialize...")
        time.sleep(5)
        
        # Start Telegram bot
        print("🤖 Launching Telegram bot...")
        bot_process = subprocess.Popen([sys.executable, "telegram_bot.py"])
        processes.append(("Telegram Bot", bot_process))
        
        print()
        print("✅ Both services are now running!")
        print("📱 Go to @alce_trade_bot on Telegram and type /start")
        print("🌐 API documentation: http://127.0.0.1:8000/docs")
        print()
        print("Press Ctrl+C to stop both services...")
        
        # Wait for processes to complete or user interrupt
        try:
            while True:
                # Check if any process has terminated
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️ {name} has stopped unexpectedly!")
                        return
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user...")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        
    finally:
        # Clean up processes
        print("🧹 Stopping all services...")
        for name, process in processes:
            if process.poll() is None:  # Process is still running
                print(f"🛑 Stopping {name}...")
                try:
                    process.terminate()
                    # Wait a bit for graceful shutdown
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Force killing {name}...")
                    process.kill()
                except Exception as e:
                    print(f"⚠️ Error stopping {name}: {e}")
        
        print("✅ All services stopped.")
        print("👋 Thank you for using AI Forex Bot!")

if __name__ == "__main__":
    main()
