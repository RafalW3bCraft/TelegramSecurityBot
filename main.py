#!/usr/bin/env python3
"""
Main entry point for the Security Bot application
Starts Flask web server, Telegram bot, and payment monitoring
"""

import os
import logging
import threading
import time
import asyncio
from dotenv import load_dotenv

# Load environment variables before importing app
load_dotenv()

from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_telegram_bot():
    """Start the Telegram bot in a separate thread"""
    try:
        from bot_runner import start_security_bot
        start_security_bot()
        logger.info("Telegram bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        import traceback
        traceback.print_exc()

def start_payment_monitor():
    """Start the payment monitoring service"""
    try:
        from payment_monitor import payment_monitor
        logger.info("Starting payment monitoring service...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(payment_monitor.start_monitoring())
    except Exception as e:
        logger.error(f"Error starting payment monitor: {e}")

def start_flask_app():
    """Start the Flask web application"""
    try:
        # Import routes to register them
        import routes
        logger.info("Routes imported successfully")
        
        # Start bot in separate thread if token is available
        bot_token = os.environ.get('BOT_TOKEN')
        if bot_token:
            bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
            bot_thread.start()
            logger.info("Bot thread started")
            
            # Start payment monitoring thread
            monitor_thread = threading.Thread(target=start_payment_monitor, daemon=True)
            monitor_thread.start()
            logger.info("Payment monitor thread started")
        else:
            logger.warning("BOT_TOKEN not found - bot will not start")
        
        # Give services time to start
        time.sleep(3)
        
        # Start Flask app
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"Failed to start Flask app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Starting Security Bot application with payment monitoring...")
    
    # Start Flask app (this will also start the bot and payment monitor)
    start_flask_app()
