#!/usr/bin/env python3
"""
Consolidated Telegram bot with all functionality
Merged from bot_runner.py, telegram_bot_daemon.py, and bot_integration.py
"""

import os
import asyncio
import logging
import re
import threading
import signal
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global bot instance management
_bot_thread = None
_bot_running = False

class SecurityBotRunner:
    def __init__(self):
        self.application = None
        self.running = False
        
    async def start_command(self, update: Update, context):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        try:
            from app import app as flask_app, db
            from models import get_or_create_user, get_or_create_group
            
            with flask_app.app_context():
                # Register user
                db_user = get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                
                # Register group if in group chat
                if chat.type in ['group', 'supergroup']:
                    db_group = get_or_create_group(
                        group_id=chat.id,
                        name=chat.title,
                        group_type=chat.type
                    )
                    logger.info(f"Group registered: {chat.title} ({chat.id})")
                
                db.session.commit()
                logger.info(f"User registered: {user.first_name} ({user.id})")
                
        except Exception as e:
            logger.error(f"Database error in start command: {e}")
        
        welcome_msg = "🛡️ Security Bot Active!\n\n"
        welcome_msg += "I automatically scan URLs for threats:\n"
        welcome_msg += "• Malware detection\n"
        welcome_msg += "• Phishing protection\n" 
        welcome_msg += "• Scam prevention\n\n"
        welcome_msg += "Commands:\n"
        welcome_msg += "/help - Show all commands\n"
        welcome_msg += "/status - Check quota\n"
        welcome_msg += "/subscribe - View & buy plans\n"
        welcome_msg += "/scan <url> - Manual scan\n"
        welcome_msg += "/scan_all - Full group analysis\n"
        welcome_msg += "/pricing - View pricing\n\n"
        welcome_msg += "💰 We accept BTC, TRX, USDT & PayPal\n"
        welcome_msg += "Protection is now enabled!"
        
        await update.message.reply_text(welcome_msg)
    
    async def help_command(self, update: Update, context):
        """Handle /help command"""
        help_msg = "🛡️ Security Bot Help\n\n"
        help_msg += "Commands:\n"
        help_msg += "/start - Activate protection\n"
        help_msg += "/help - Show this help\n"
        help_msg += "/status - Check scan quota\n"
        help_msg += "/subscribe - View subscription plans\n"
        help_msg += "/scan <url> - Manual URL scan\n"
        help_msg += "/scan_all - Scan all group content\n"
        help_msg += "/pricing - View pricing plans\n"
        help_msg += "/stats - Bot statistics\n\n"
        help_msg += "Features:\n"
        help_msg += "✓ Real-time URL scanning\n"
        help_msg += "✓ Malware detection\n"
        help_msg += "✓ Phishing protection\n"
        help_msg += "✓ Scam prevention\n"
        help_msg += "✓ Subscription management\n\n"
        help_msg += "I automatically scan all URLs posted in chats."
        
        await update.message.reply_text(help_msg)
    
    async def status_command(self, update: Update, context):
        """Handle /status command"""
        user = update.effective_user
        
        try:
            from app import app as flask_app
            from models import get_or_create_user
            
            with flask_app.app_context():
                db_user = get_or_create_user(telegram_id=user.id)
                credit_summary = db_user.get_credit_summary()
                
                status_msg = f"📊 Security Status\n\n"
                status_msg += f"🔍 Credits Remaining: {credit_summary['remaining']}\n"
                status_msg += f"💰 Credits Purchased: {credit_summary['purchased']}\n"
                status_msg += f"📊 Credits Used: {credit_summary['used']}\n\n"
                status_msg += f"User ID: {user.id}\n"
                status_msg += f"Username: @{user.username or 'Not set'}\n"
                status_msg += f"Member since: {db_user.created_at.strftime('%Y-%m-%d')}\n\n"
                
                if credit_summary['remaining'] > 0:
                    status_msg += f"✅ You can perform {credit_summary['remaining']} more URL scans"
                else:
                    status_msg += f"❌ No credits remaining - use /subscribe to purchase more"
                
                await update.message.reply_text(status_msg)
                
        except Exception as e:
            logger.error(f"Status error: {e}")
            await update.message.reply_text("Unable to retrieve status.")
    
    async def subscribe_command(self, update: Update, context):
        """Enhanced /subscribe command with comprehensive payment processing"""
        user = update.effective_user
        
        # Check if user provided a plan argument
        plan = None
        if context.args:
            plan = context.args[0].lower()
        
        if not plan:
            # Enhanced credit-based subscription plans with industry features
            subscribe_msg = "🛡️ ADVANCED SECURITY CREDIT PACKAGES\n\n"
            subscribe_msg += "💳 ENTERPRISE CREDIT SYSTEM:\n"
            subscribe_msg += "• Credits never expire - lifetime access\n"
            subscribe_msg += "• Pay-per-scan model - maximum efficiency\n"
            subscribe_msg += "• VirusTotal + URLhaus integration included\n"
            subscribe_msg += "• Real-time threat intelligence updates\n\n"
            
            subscribe_msg += "📦 PROFESSIONAL PACKAGES:\n\n"
            subscribe_msg += "🥉 STARTER SECURITY PACK - $5:\n"
            subscribe_msg += "• 100 enhanced threat scans\n"
            subscribe_msg += "• VirusTotal API integration\n"
            subscribe_msg += "• URLhaus malware database access\n"
            subscribe_msg += "• Pattern-based threat detection\n"
            subscribe_msg += "• Basic auto-blocking protection\n"
            subscribe_msg += "• Email support\n\n"
            
            subscribe_msg += "🥈 STANDARD PROTECTION PACK - $15:\n"
            subscribe_msg += "• 350 comprehensive threat scans\n"
            subscribe_msg += "• Advanced VirusTotal analysis\n"
            subscribe_msg += "• Enhanced URLhaus lookups\n"
            subscribe_msg += "• Multi-engine threat correlation\n"
            subscribe_msg += "• Real-time group protection\n"
            subscribe_msg += "• Advanced auto-blocking\n"
            subscribe_msg += "• Priority email support\n\n"
            
            subscribe_msg += "🥇 PREMIUM SECURITY PACK - $35:\n"
            subscribe_msg += "• 1000 enterprise-grade scans\n"
            subscribe_msg += "• Full threat intelligence suite\n"
            subscribe_msg += "• Malware family identification\n"
            subscribe_msg += "• Custom threat pattern rules\n"
            subscribe_msg += "• Advanced behavioral analysis\n"
            subscribe_msg += "• Instant threat notifications\n"
            subscribe_msg += "• 24/7 priority support\n\n"
            
            subscribe_msg += "💎 ENTERPRISE PROTECTION PACK - $75:\n"
            subscribe_msg += "• 3000 unlimited threat scans\n"
            subscribe_msg += "• Complete API integration access\n"
            subscribe_msg += "• Custom threat intelligence feeds\n"
            subscribe_msg += "• White-label integrations\n"
            subscribe_msg += "• Advanced reporting and analytics\n"
            subscribe_msg += "• Dedicated security manager\n"
            subscribe_msg += "• Enterprise SLA guarantee\n\n"
            
            subscribe_msg += "💰 SECURE PAYMENT OPTIONS:\n"
            subscribe_msg += "• Bitcoin (BTC) - Anonymous & Secure\n"
            subscribe_msg += "• Tron (TRX) - Fast & Low-Cost\n" 
            subscribe_msg += "• USDT (TRC20) - Stable & Reliable\n"
            subscribe_msg += "• PayPal - Instant & Protected\n\n"
            subscribe_msg += "📝 CRYPTO PAYMENTS (Auto-Verified):\n"
            subscribe_msg += "/subscribe starter\n"
            subscribe_msg += "/subscribe standard\n"
            subscribe_msg += "/subscribe premium\n"
            subscribe_msg += "/subscribe enterprise\n\n"
            subscribe_msg += "💳 PAYPAL INSTANT CHECKOUT:\n"
            subscribe_msg += "/subscribe starter paypal\n"
            subscribe_msg += "/subscribe standard paypal\n"
            subscribe_msg += "/subscribe premium paypal\n"
            subscribe_msg += "/subscribe enterprise paypal\n\n"
            subscribe_msg += "🔒 All payments secured with enterprise-grade encryption"
            
            await update.message.reply_text(subscribe_msg)
            return
        
        # Handle specific credit package purchase
        credit_packages = {
            'starter': {'price': 5, 'name': 'Starter Pack', 'credits': 100},
            'standard': {'price': 15, 'name': 'Standard Pack', 'credits': 350},
            'premium': {'price': 35, 'name': 'Premium Pack', 'credits': 1000},
            'enterprise': {'price': 75, 'name': 'Enterprise Pack', 'credits': 3000}
        }
        
        # Check for PayPal payment method
        payment_method = 'crypto'  # Default
        if len(context.args) > 1 and context.args[1].lower() == 'paypal':
            payment_method = 'paypal'
        
        if plan not in credit_packages:
            await update.message.reply_text(
                "Invalid package. Available packages: starter, standard, premium, enterprise\n"
                "Use: /subscribe starter or /subscribe starter paypal"
            )
            return
        
        selected_package = credit_packages[plan]
        
        try:
            from app import app as flask_app, db
            from models import get_or_create_user, Payment
            from payment_processor import PaymentProcessor
            import os
            
            with flask_app.app_context():
                db_user = get_or_create_user(telegram_id=user.id)
                
                # Create payment processor
                payment_processor = PaymentProcessor()
                
                usd_amount = selected_package['price']
                
                if payment_method == 'paypal':
                    # PayPal checkout flow
                    payment_msg = f"💰 PayPal Checkout - {selected_package['name']}\n"
                    payment_msg += f"Credits: {selected_package['credits']} URL scans\n"
                    payment_msg += f"Amount: ${usd_amount} USD\n"
                    payment_msg += f"Cost per scan: ${usd_amount/selected_package['credits']:.3f}\n\n"
                    
                    # Create PayPal payment record
                    payment_record = Payment(
                        user_id=db_user.id,
                        payment_method='paypal',
                        amount_usd=usd_amount,
                        purchase_type=f'{plan}_credits',
                        quantity=selected_package['credits'],
                        status='pending'
                    )
                    db.session.add(payment_record)
                    db.session.commit()
                    
                    # Generate PayPal checkout URL
                    base_url = os.environ.get('RENDER_URL', os.environ.get('REPLIT_URL', 'https://localhost:5000'))
                    paypal_url = f"{base_url}/paypal/checkout/{payment_record.id}"
                    
                    payment_msg += "💳 PayPal Payment:\n\n"
                    payment_msg += f"🔗 Checkout Link:\n{paypal_url}\n\n"
                    payment_msg += "📝 Instructions:\n"
                    payment_msg += "1. Click the checkout link above\n"
                    payment_msg += "2. Complete payment on PayPal\n"
                    payment_msg += "3. Credits activate automatically\n"
                    payment_msg += "4. Return here for confirmation\n\n"
                    payment_msg += f"🆔 Payment ID: {payment_record.id}\n"
                    payment_msg += "⏰ Link expires in 1 hour"
                    
                else:
                    # Enhanced crypto payment flow with real-time verification
                    from webhook_payment_processor import webhook_processor
                    
                    rates = payment_processor.get_crypto_rates()
                    
                    # Calculate amounts
                    btc_amount = usd_amount / rates.get('bitcoin', 50000) if rates else 0.0001
                    trx_amount = usd_amount / rates.get('tron', 0.1) if rates else 50
                    usdt_amount = usd_amount  # USDT is pegged to USD
                    
                    # Get wallet addresses from environment
                    btc_wallet = os.environ.get('BTC_WALLET_ADDRESS', '')
                    trx_wallet = os.environ.get('TRX_WALLET_ADDRESS', '')
                    usdt_wallet = os.environ.get('USDT_TRC20_WALLET_ADDRESS', '')
                    
                    payment_msg = f"💰 Payment for {selected_package['name']}\n"
                    payment_msg += f"Credits: {selected_package['credits']} URL scans\n"
                    payment_msg += f"Amount: ${usd_amount}\n"
                    payment_msg += f"Cost per scan: ${usd_amount/selected_package['credits']:.3f}\n\n"
                    
                    payment_msg += "💎 Cryptocurrency Payments (Auto-Verified):\n\n"
                    
                    # Create payment records for each cryptocurrency option
                    payment_options = []
                    
                    if btc_wallet:
                        btc_payment = Payment(
                            user_id=db_user.id,
                            payment_method='crypto',
                            cryptocurrency='BTC',
                            amount_usd=usd_amount,
                            amount_crypto=btc_amount,
                            payment_address=btc_wallet,
                            purchase_type=f'{plan}_credits',
                            quantity=selected_package['credits'],
                            status='pending'
                        )
                        db.session.add(btc_payment)
                        db.session.flush()  # Get the ID
                        
                        # Setup webhook monitoring
                        webhook_processor.start_payment_monitoring(btc_payment)
                        
                        payment_msg += f"₿ Bitcoin (BTC) - Auto-Verified:\n"
                        payment_msg += f"Amount: {btc_amount:.8f} BTC\n"
                        payment_msg += f"Address: `{btc_wallet}`\n"
                        payment_msg += f"Payment ID: {btc_payment.id}\n\n"
                        payment_options.append(btc_payment)
                    
                    if trx_wallet:
                        trx_payment = Payment(
                            user_id=db_user.id,
                            payment_method='crypto',
                            cryptocurrency='TRX',
                            amount_usd=usd_amount,
                            amount_crypto=trx_amount,
                            payment_address=trx_wallet,
                            purchase_type=f'{plan}_credits',
                            quantity=selected_package['credits'],
                            status='pending'
                        )
                        db.session.add(trx_payment)
                        db.session.flush()
                        
                        webhook_processor.start_payment_monitoring(trx_payment)
                        
                        payment_msg += f"⚡ Tron (TRX) - Auto-Verified:\n"
                        payment_msg += f"Amount: {trx_amount:.2f} TRX\n"
                        payment_msg += f"Address: `{trx_wallet}`\n"
                        payment_msg += f"Payment ID: {trx_payment.id}\n\n"
                        payment_options.append(trx_payment)
                    
                    if usdt_wallet:
                        usdt_payment = Payment(
                            user_id=db_user.id,
                            payment_method='crypto',
                            cryptocurrency='USDT',
                            amount_usd=usd_amount,
                            amount_crypto=usdt_amount,
                            payment_address=usdt_wallet,
                            purchase_type=f'{plan}_credits',
                            quantity=selected_package['credits'],
                            status='pending'
                        )
                        db.session.add(usdt_payment)
                        db.session.flush()
                        
                        webhook_processor.start_payment_monitoring(usdt_payment)
                        
                        payment_msg += f"💵 USDT (TRC20) - Auto-Verified:\n"
                        payment_msg += f"Amount: {usdt_amount:.2f} USDT\n"
                        payment_msg += f"Address: `{usdt_wallet}`\n"
                        payment_msg += f"Payment ID: {usdt_payment.id}\n\n"
                        payment_options.append(usdt_payment)
                    
                    db.session.commit()
                    
                    # Enhanced payment instructions
                    payment_msg += "🚀 AUTOMATIC VERIFICATION:\n"
                    payment_msg += "• Send payment to any address above\n"
                    payment_msg += "• Credits activate automatically\n"
                    payment_msg += "• Real-time transaction monitoring\n"
                    payment_msg += "• No manual verification needed\n\n"
                    
                    payment_msg += "📝 Instructions:\n"
                    payment_msg += "1. Choose your preferred cryptocurrency\n"
                    payment_msg += "2. Send EXACT amount to the address\n"
                    payment_msg += "3. Wait for blockchain confirmation\n"
                    payment_msg += "4. Credits activate automatically\n\n"
                    
                    payment_msg += "⚠️ Important:\n"
                    payment_msg += "• Send exact amount shown\n"
                    payment_msg += "• Use correct network (TRC20 for USDT)\n"
                    payment_msg += "• Payment monitored in real-time\n"
                    payment_msg += "• Confirmation typically within 10-30 minutes\n\n"
                    
                    # Add status check instructions
                    base_url = os.environ.get('RENDER_URL', os.environ.get('REPLIT_URL', 'https://localhost:5000'))
                    if payment_options:
                        payment_msg += f"📊 Check Payment Status:\n"
                        for payment in payment_options:
                            payment_msg += f"{payment.cryptocurrency}: {base_url}/webhook/status/{payment.id}\n"
                
                # Notify admin about new payment
                try:
                    from payment_verification import PaymentVerification
                    verifier = PaymentVerification()
                    await verifier.notify_admin_payment(
                        payment_record.id, 
                        db_user.id, 
                        usd_amount, 
                        'USD'
                    )
                except Exception as e:
                    logger.error(f"Error notifying admin: {e}")
                
                await update.message.reply_text(payment_msg, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Subscribe command error: {e}")
            await update.message.reply_text(
                "Error processing subscription request. Please try again or contact support."
            )
    
    async def scan_command(self, update: Update, context):
        """Enhanced /scan command with comprehensive VirusTotal and URLhaus analysis"""
        if not context.args:
            await update.message.reply_text(
                "🔍 Advanced Security Scanner\n\n"
                "Analyze URLs using VirusTotal and URLhaus threat intelligence:\n"
                "Usage: /scan https://example.com\n\n"
                "Features:\n"
                "• Real-time VirusTotal scanning\n"
                "• URLhaus malware database lookup\n"
                "• Pattern-based threat detection\n"
                "• Industry-standard risk assessment"
            )
            return
        
        url = context.args[0].strip()
        user = update.effective_user
        
        # Validate and normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            from app import app as flask_app, db
            from models import get_or_create_user, ScanLog
            from threat_intelligence import ThreatIntelligence
            
            with flask_app.app_context():
                db_user = get_or_create_user(telegram_id=user.id)
                
                # Check credits
                if db_user.scan_credits <= 0:
                    await update.message.reply_text(
                        "❌ Insufficient Credits\n\n"
                        "You need credits to perform security scans.\n"
                        "Purchase credits: /subscribe starter paypal\n"
                        "Or with crypto: /subscribe starter\n\n"
                        "Check balance: /stats"
                    )
                    return
                
                # Initialize enhanced threat intelligence
                ti = ThreatIntelligence()
                
                # Send detailed scanning progress
                scan_msg = await update.message.reply_text(
                    f"🔍 SECURITY ANALYSIS INITIATED\n\n"
                    f"Target: {url}\n"
                    f"Status: Connecting to threat databases...\n"
                    f"VirusTotal: Querying...\n"
                    f"URLhaus: Checking...\n"
                    f"Pattern Analysis: Running..."
                )
                
                # Perform comprehensive scan
                scan_result = ti.scan_url(url)
                
                # Extract enhanced results
                classification = scan_result.get('classification', 'unknown')
                confidence = scan_result.get('confidence', 0.0)
                risk_score = scan_result.get('risk_score', 0)
                threat_sources = scan_result.get('threat_sources', [])
                malware_families = scan_result.get('malware_families', [])
                threat_types = scan_result.get('threat_types', [])
                detection_ratio = scan_result.get('detection_ratio', '0/0')
                
                # Deduct credit
                db_user.use_credit()
                
                # Log comprehensive scan
                scan_log = ScanLog(
                    user_id=db_user.id,
                    domain=ti.extract_domain(url),
                    url=url,
                    scan_type='individual_enhanced',
                    scan_result=classification,
                    threat_sources=str(threat_sources),
                    confidence_score=confidence,
                    action_taken='deep_analysis'
                )
                db.session.add(scan_log)
                db.session.commit()
                
                # Generate comprehensive security report
                if classification == 'malicious':
                    status_icon = "🚨"
                    threat_level = "CRITICAL"
                    security_advice = "IMMEDIATE THREAT - DO NOT ACCESS"
                    risk_color = "🔴"
                elif classification == 'suspicious':
                    status_icon = "⚠️"
                    threat_level = "HIGH RISK"
                    security_advice = "POTENTIAL THREAT - AVOID ACCESS"
                    risk_color = "🟡"
                else:
                    status_icon = "✅"
                    threat_level = "SECURE"
                    security_advice = "SAFE TO ACCESS"
                    risk_color = "🟢"
                
                # Build detailed threat intelligence report
                report = f"{status_icon} THREAT ANALYSIS COMPLETE\n\n"
                report += f"🌐 URL: {url}\n"
                report += f"{risk_color} Status: {threat_level}\n"
                report += f"📊 Confidence: {confidence:.1f}%\n"
                report += f"⚡ Risk Score: {risk_score}/100\n"
                
                if detection_ratio != '0/0':
                    report += f"🛡️ VirusTotal: {detection_ratio} engines detected\n"
                
                if threat_sources:
                    report += f"🔍 Detection Sources: {', '.join(threat_sources)}\n"
                
                if threat_types:
                    report += f"⚠️ Threat Types: {', '.join(threat_types)}\n"
                
                if malware_families:
                    report += f"🦠 Malware Families: {', '.join(malware_families)}\n"
                
                report += f"\n🎯 Security Recommendation:\n{security_advice}\n\n"
                
                # Add technical details for suspicious/malicious URLs
                if classification in ['malicious', 'suspicious']:
                    report += "📋 TECHNICAL ANALYSIS:\n"
                    if 'VirusTotal' in threat_sources:
                        report += "• Flagged by VirusTotal antivirus engines\n"
                    if 'URLhaus' in threat_sources:
                        report += "• Listed in URLhaus malware database\n"
                    if 'Pattern Analysis' in threat_sources:
                        report += "• Matches known threat patterns\n"
                    report += "\n"
                
                report += f"💳 Scan Credits Remaining: {db_user.scan_credits}\n"
                report += f"⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}"
                
                await scan_msg.edit_text(report)
                
        except Exception as e:
            logger.error(f"Enhanced scan command error: {e}")
            # Refund credit on error
            try:
                with flask_app.app_context():
                    db_user.scan_credits += 1
                    db.session.commit()
            except:
                pass
            await update.message.reply_text(
                "❌ Scan Error\n\n"
                "Failed to analyze URL. Please verify the URL format.\n"
                "Credit has been refunded to your account."
            )
    
    async def pricing_command(self, update: Update, context):
        """Handle /pricing command"""
        pricing_msg = "💰 Security Bot Credit Pricing\n\n"
        pricing_msg += "💳 Credit System Benefits:\n"
        pricing_msg += "• Credits never expire\n"
        pricing_msg += "• Pay only for what you use\n"
        pricing_msg += "• No monthly commitments\n\n"
        
        pricing_msg += "📦 Credit Packages:\n\n"
        pricing_msg += "🥉 Starter Pack - $5:\n"
        pricing_msg += "• 100 URL scan credits\n"
        pricing_msg += "• $0.050 per scan\n\n"
        
        pricing_msg += "🥈 Standard Pack - $15:\n"
        pricing_msg += "• 350 URL scan credits\n"
        pricing_msg += "• $0.043 per scan (14% savings)\n\n"
        
        pricing_msg += "🥇 Premium Pack - $35:\n"
        pricing_msg += "• 1000 URL scan credits\n"
        pricing_msg += "• $0.035 per scan (30% savings)\n\n"
        
        pricing_msg += "💎 Enterprise Pack - $75:\n"
        pricing_msg += "• 3000 URL scan credits\n"
        pricing_msg += "• $0.025 per scan (50% savings)\n\n"
        
        pricing_msg += "💰 Payment Methods:\n"
        pricing_msg += "• Bitcoin, Tron, USDT\n"
        pricing_msg += "• Manual verification\n\n"
        pricing_msg += "Use /subscribe to purchase credits!"
        
        await update.message.reply_text(pricing_msg)
    
    async def stats_command(self, update: Update, context):
        """Handle /stats command"""
        user = update.effective_user
        
        try:
            from app import app as flask_app
            from models import get_dashboard_stats, get_or_create_user
            
            with flask_app.app_context():
                db_user = get_or_create_user(telegram_id=user.id)
                credit_summary = db_user.get_credit_summary()
                
                stats_msg = f"💳 Your Credit Balance\n\n"
                stats_msg += f"🔍 Credits Remaining: {credit_summary['remaining']}\n"
                stats_msg += f"💰 Credits Purchased: {credit_summary['purchased']}\n"
                stats_msg += f"📊 Credits Used: {credit_summary['used']}\n\n"
                
                if credit_summary['remaining'] > 0:
                    stats_msg += f"✅ You can perform {credit_summary['remaining']} more URL scans\n\n"
                else:
                    stats_msg += f"❌ No credits remaining - purchase more with /subscribe\n\n"
                
                # Global stats
                global_stats = get_dashboard_stats()
                stats_msg += f"🌐 Global Statistics\n"
                stats_msg += f"👥 Total Groups: {global_stats['total_groups']}\n"
                stats_msg += f"🔍 Total Scans: {global_stats['total_scans']}\n"
                stats_msg += f"🛡️ Threats Blocked: {global_stats['threats_blocked']}"
                
                await update.message.reply_text(stats_msg)
                
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await update.message.reply_text("Unable to retrieve statistics.")
    
    async def config_command(self, update: Update, context):
        """Handle /config command for admin configuration"""
        user = update.effective_user
        
        # Check if user is admin
        admin_user_ids = os.environ.get('ADMIN_USER_IDS', '').split(',')
        if str(user.id) not in admin_user_ids:
            await update.message.reply_text("❌ Admin access required for configuration.")
            return
        
        try:
            # Get current configuration
            auto_block_threshold = float(os.environ.get('AUTO_BLOCK_THRESHOLD', '0.70'))
            auto_block_enabled = os.environ.get('AUTO_BLOCK_ENABLED', 'True').lower() == 'true'
            
            config_msg = "⚙️ SECURITY BOT CONFIGURATION\n\n"
            config_msg += f"🛡️ Auto-Block Settings:\n"
            config_msg += f"• Status: {'✅ Enabled' if auto_block_enabled else '❌ Disabled'}\n"
            config_msg += f"• Threshold: {auto_block_threshold:.0%} confidence\n\n"
            
            config_msg += "📋 How it works:\n"
            config_msg += "• URLs with confidence ≥ threshold are automatically blocked\n"
            config_msg += "• Messages containing blocked URLs are deleted\n"
            config_msg += "• Users receive private notifications\n"
            config_msg += "• Group gets public warning\n\n"
            
            config_msg += "🔧 Configuration options:\n"
            config_msg += "• Edit .env file to change AUTO_BLOCK_THRESHOLD\n"
            config_msg += "• Set AUTO_BLOCK_ENABLED=false to disable\n"
            config_msg += "• Restart bot after changes"
            
            await update.message.reply_text(config_msg)
            
        except Exception as e:
            logger.error(f"Config command error: {e}")
            await update.message.reply_text("❌ Configuration error occurred.")
    
    async def scan_all_command(self, update: Update, context):
        """Handle /scan_all command with credit-based charging per website and auto-blocking"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Only work in groups
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ This command only works in groups.\n"
                "Use /scan <url> for individual URL scanning."
            )
            return
        
        try:
            from app import app as flask_app, db
            from models import get_or_create_user, get_or_create_group, ScanLog
            from threat_intelligence import ThreatIntelligence
            from group_scanner import GroupScanner
            import re
            
            with flask_app.app_context():
                db_user = get_or_create_user(telegram_id=user.id)
                db_group = get_or_create_group(
                    group_id=chat.id,
                    name=chat.title,
                    group_type=chat.type
                )
                
                # Check if user has scan credits
                if db_user.scan_credits <= 0:
                    await update.message.reply_text(
                        "❌ No scan credits remaining!\n\n"
                        "💳 Purchase more credits with /subscribe\n"
                        "📊 Check your balance with /stats"
                    )
                    return
                
                # Initialize scanners
                ti = ThreatIntelligence()
                scanner = GroupScanner()
                
                # Send initial status message
                status_msg = await update.message.reply_text(
                    "🔍 Starting comprehensive group scan...\n"
                    "📊 Analyzing recent activity..."
                )
                
                # Extract URLs that were actually posted in this group
                urls_to_scan = scanner.extract_urls_from_group(chat.id, days=7)
                
                # If no URLs found from real messages, inform user
                if not urls_to_scan:
                    await status_msg.edit_text(
                        "📊 Group Analysis Complete\n\n"
                        "No URLs found in recent group messages to scan.\n"
                        "The bot monitors all future messages automatically.\n\n"
                        f"Credits remaining: {db_user.scan_credits}\n"
                        "Post URLs in the group to trigger scanning."
                    )
                    return
                

                
                total_urls = len(urls_to_scan)
                
                # Check if user has enough credits (1 credit per URL)
                if db_user.scan_credits < total_urls:
                    await status_msg.edit_text(
                        f"❌ Insufficient credits!\n\n"
                        f"URLs found: {total_urls}\n"
                        f"Credits available: {db_user.scan_credits}\n"
                        f"Credits needed: {total_urls}\n\n"
                        "💳 Purchase more credits with /subscribe"
                    )
                    return
                
                # Enhanced group URL scanning with comprehensive threat analysis
                await status_msg.edit_text(
                    f"🔍 COMPREHENSIVE GROUP SECURITY SCAN\n\n"
                    f"📊 URLs to analyze: {total_urls}\n"
                    f"💳 Credit cost: {total_urls} credits\n"
                    f"🛡️ VirusTotal + URLhaus analysis\n"
                    f"⚡ Auto-blocking enabled\n\n"
                    f"Starting deep analysis..."
                )
                
                threats_blocked = 0
                suspicious_count = 0
                clean_count = 0
                scan_results = []
                malware_detected = []
                
                for i, url in enumerate(urls_to_scan):
                    # Update detailed progress
                    domain = ti.extract_domain(url)
                    progress = f"🔍 SCANNING {i+1}/{total_urls}\n\n"
                    progress += f"🌐 Current: {domain}\n"
                    progress += f"🛡️ VirusTotal: Checking...\n"
                    progress += f"🔎 URLhaus: Querying...\n"
                    progress += f"🧠 Pattern Analysis: Running...\n\n"
                    progress += f"💳 Credits: {db_user.scan_credits}"
                    await status_msg.edit_text(progress)
                    
                    # Perform comprehensive threat analysis
                    scan_result = ti.scan_url(url)
                    domain = ti.extract_domain(url)
                    confidence = scan_result.get('confidence', 0.0)
                    classification = scan_result.get('classification', 'clean')
                    risk_score = scan_result.get('risk_score', 0)
                    threat_sources = scan_result.get('threat_sources', [])
                    threat_types = scan_result.get('threat_types', [])
                    malware_families = scan_result.get('malware_families', [])
                    
                    # Deduct 1 credit per website scanned
                    db_user.use_credit()
                    
                    # Enhanced auto-blocking logic with industry standards
                    action_taken = 'analyzed'
                    
                    # Critical threat blocking (malicious or high-risk suspicious)
                    should_block = (
                        classification == 'malicious' or 
                        (classification == 'suspicious' and (confidence >= 75 or risk_score >= 60))
                    )
                    
                    if should_block:
                        threats_blocked += 1
                        action_taken = 'auto_blocked'
                        # Update group threats blocked counter
                        db_group.threats_blocked += 1
                        
                        # Determine threat level for notification
                        if classification == 'malicious':
                            threat_level = "CRITICAL MALWARE"
                            alert_emoji = "🚨"
                        else:
                            threat_level = "HIGH-RISK SUSPICIOUS"
                            alert_emoji = "⚠️"
                        
                        # Store malware details
                        if malware_families:
                            malware_detected.extend(malware_families)
                        
                        # Send detailed threat notification to group
                        try:
                            threat_alert = f"{alert_emoji} THREAT AUTOMATICALLY BLOCKED\n\n"
                            threat_alert += f"🌐 Domain: {domain}\n"
                            threat_alert += f"🚨 Level: {threat_level}\n"
                            threat_alert += f"📊 Confidence: {confidence:.1f}%\n"
                            threat_alert += f"⚡ Risk Score: {risk_score}/100\n"
                            
                            if threat_sources:
                                threat_alert += f"🔍 Sources: {', '.join(threat_sources)}\n"
                            if threat_types:
                                threat_alert += f"⚠️ Types: {', '.join(threat_types)}\n"
                            if malware_families:
                                threat_alert += f"🦠 Malware: {', '.join(malware_families)}\n"
                                
                            threat_alert += f"\n🛡️ Group protection active"
                            
                            await context.bot.send_message(
                                chat_id=chat.id,
                                text=threat_alert
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send threat alert: {e}")
                            
                    elif classification == 'suspicious':
                        suspicious_count += 1
                        action_taken = 'flagged_suspicious'
                    else:
                        clean_count += 1
                        action_taken = 'verified_safe'
                    
                    # Log comprehensive scan with enhanced details
                    scan_log = ScanLog(
                        user_id=db_user.id,
                        group_id=db_group.id,
                        domain=domain,
                        url=url,
                        scan_type='group_scan_enhanced',
                        scan_result=classification,
                        threat_sources=str(threat_sources),
                        confidence_score=confidence,
                        action_taken=action_taken,
                        message_deleted=(action_taken == 'auto_blocked')
                    )
                    db.session.add(scan_log)
                    
                    # Update group scan counter
                    db_group.total_scans_performed += 1
                    
                    # Store detailed result for final report
                    scan_results.append({
                        'url': url,
                        'domain': domain,
                        'classification': classification,
                        'confidence': confidence,
                        'risk_score': risk_score,
                        'threat_sources': threat_sources,
                        'threat_types': threat_types,
                        'malware_families': malware_families,
                        'action': action_taken
                    })
                
                # Commit all database changes
                db.session.commit()
                
                # Generate comprehensive security report
                credits_used = total_urls
                unique_malware = list(dict.fromkeys(malware_detected))
                
                final_msg = f"📊 COMPREHENSIVE SECURITY ANALYSIS COMPLETE\n\n"
                final_msg += f"🔍 Enhanced Analysis Results:\n"
                final_msg += f"• URLs analyzed: {total_urls}\n"
                final_msg += f"• 🚨 Critical threats blocked: {threats_blocked}\n"
                final_msg += f"• ⚠️ Suspicious flagged: {suspicious_count}\n"
                final_msg += f"• ✅ Verified safe: {clean_count}\n\n"
                
                if threats_blocked > 0:
                    final_msg += f"🛡️ AUTOMATIC THREAT PROTECTION ACTIVE\n"
                    final_msg += f"Blocked {threats_blocked} high-risk URLs using:\n"
                    final_msg += f"• VirusTotal threat intelligence\n"
                    final_msg += f"• URLhaus malware database\n"
                    final_msg += f"• Advanced pattern analysis\n\n"
                
                if unique_malware:
                    final_msg += f"🦠 Malware Families Detected:\n"
                    for malware in unique_malware[:5]:  # Show top 5
                        final_msg += f"• {malware.title()}\n"
                    if len(unique_malware) > 5:
                        final_msg += f"• +{len(unique_malware) - 5} more...\n"
                    final_msg += "\n"
                
                final_msg += f"💳 Credit Usage:\n"
                final_msg += f"• Credits used: {credits_used}\n"
                final_msg += f"• Credits remaining: {db_user.scan_credits}\n"
                final_msg += f"• Cost per scan: 1 credit\n\n"
                
                # Enhanced threat intelligence summary
                if threats_blocked > 0 or suspicious_count > 0:
                    final_msg += "🔍 THREAT INTELLIGENCE SUMMARY:\n"
                    threat_sources_found = set()
                    threat_types_found = set()
                    
                    for result in scan_results:
                        if result['classification'] in ['malicious', 'suspicious']:
                            threat_sources_found.update(result.get('threat_sources', []))
                            threat_types_found.update(result.get('threat_types', []))
                            
                            status_icon = "🚨" if result['action'] == 'auto_blocked' else "⚠️"
                            risk_level = f"{result['risk_score']}/100" if result.get('risk_score') else "N/A"
                            final_msg += f"{status_icon} {result['domain']} (Risk: {risk_level})\n"
                    
                    if threat_sources_found:
                        final_msg += f"\n📡 Detection Sources: {', '.join(threat_sources_found)}\n"
                    if threat_types_found:
                        final_msg += f"⚠️ Threat Categories: {', '.join(threat_types_found)}\n"
                    final_msg += "\n"
                
                final_msg += f"🛡️ Group Security Status: PROTECTED\n"
                final_msg += f"📈 Total Threats Blocked: {db_group.threats_blocked}\n"
                final_msg += f"🕐 Scan Completed: {datetime.now().strftime('%H:%M:%S')}"
                
                await status_msg.edit_text(final_msg)
                
                # Send admin summary if user is admin
                try:
                    user_member = await context.bot.get_chat_member(chat.id, user.id)
                    if user_member.status in ['administrator', 'creator'] and (threats_blocked > 0 or suspicious_count > 0):
                        admin_summary = f"📋 ADMIN SECURITY INTELLIGENCE REPORT\n\n"
                        admin_summary += f"🏢 Group: {chat.title}\n"
                        admin_summary += f"👤 Initiated by: @{user.username or user.first_name}\n"
                        admin_summary += f"🚨 Critical threats blocked: {threats_blocked}\n"
                        admin_summary += f"⚠️ Suspicious URLs flagged: {suspicious_count}\n"
                        admin_summary += f"📊 Total group protection events: {db_group.threats_blocked}\n\n"
                        
                        if unique_malware:
                            admin_summary += f"🦠 Malware families detected:\n"
                            for malware in unique_malware[:3]:
                                admin_summary += f"• {malware.title()}\n"
                            admin_summary += "\n"
                        
                        admin_summary += f"🛡️ Security Systems Used:\n"
                        admin_summary += f"• VirusTotal threat intelligence\n"
                        admin_summary += f"• URLhaus malware database\n"
                        admin_summary += f"• Advanced pattern analysis\n\n"
                        
                        admin_summary += f"🔧 Admin Commands:\n"
                        admin_summary += f"/stats - Detailed analytics\n"
                        admin_summary += f"/scan_all - Run another comprehensive scan\n"
                        admin_summary += f"/config - Advanced security settings"
                        
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=admin_summary
                        )
                except Exception as e:
                    logger.warning(f"Admin notification failed: {e}")
                
        except Exception as e:
            logger.error(f"Scan all command error: {e}")
            await update.message.reply_text(
                f"❌ Scan failed: {str(e)[:100]}...\n"
                "Please try again or contact support."
            )
    
    async def handle_message(self, update: Update, context):
        """Handle messages and scan URLs from real group activity"""
        if not update.message or not update.message.text:
            return
            
        # Skip messages from bots
        if update.effective_user.is_bot:
            return
            
        text = update.message.text
        chat = update.effective_chat
        
        # Extract URLs from message using comprehensive regex
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        if urls and chat.type in ['group', 'supergroup']:
            try:
                from app import app as flask_app, db
                from models import get_or_create_user, get_or_create_group, ScanLog
                from threat_intelligence import ThreatIntelligence
                
                with flask_app.app_context():
                    db_user = get_or_create_user(
                        telegram_id=update.effective_user.id,
                        username=update.effective_user.username,
                        first_name=update.effective_user.first_name
                    )
                    db_group = get_or_create_group(
                        group_id=chat.id,
                        name=chat.title,
                        group_type=chat.type
                    )
                    
                    # Scan all URLs in message
                    ti = ThreatIntelligence()
                    
                    for url in urls:
                        scan_result = ti.scan_url(url)
                        domain = ti.extract_domain(url)
                        
                        # Log the automatic scan from real group message
                        scan_log = ScanLog(
                            user_id=db_user.id,
                            group_id=db_group.id,
                            domain=domain,
                            url=url,
                            scan_type='group_message',  # Real message scan
                            scan_result=scan_result['classification'],
                            threat_sources=str(scan_result.get('sources', [])),
                            confidence_score=scan_result.get('confidence', 0.0),
                            action_taken='real_time_scan'
                        )
                        db.session.add(scan_log)
                        
                        # Update group stats
                        db_group.total_scans_performed += 1
                        db_group.last_active = datetime.now(timezone.utc)
                        
                        # Real-time threat detection and blocking
                        classification = scan_result['classification']
                        confidence = scan_result.get('confidence', 0.0)
                        
                        # Auto-block malicious or high-confidence suspicious URLs
                        should_block = (classification == 'malicious' or 
                                      (classification == 'suspicious' and confidence > 0.70))
                        
                        if should_block:
                            # Block the threat
                            db_group.threats_blocked += 1
                            scan_log.action_taken = 'auto_blocked'
                            scan_log.message_deleted = True
                            
                            # Send threat alert
                            threat_level = "CRITICAL" if classification == 'malicious' else "HIGH"
                            alert_msg = f"🚨 THREAT BLOCKED!\n\n"
                            alert_msg += f"Dangerous URL detected in real-time:\n"
                            alert_msg += f"Domain: {domain}\n"
                            alert_msg += f"Threat Level: {threat_level}\n"
                            alert_msg += f"Classification: {classification.upper()}\n"
                            alert_msg += f"Confidence: {confidence:.0%}"
                            
                            try:
                                await update.message.reply_text(alert_msg)
                            except Exception:
                                pass
                        
                        elif classification == 'suspicious':
                            # Warning for suspicious content
                            warning_msg = f"⚠️ Suspicious URL detected:\n"
                            warning_msg += f"Domain: {domain}\n"
                            warning_msg += f"Confidence: {confidence:.0%}\n"
                            warning_msg += f"Exercise caution when clicking"
                            
                            try:
                                await update.message.reply_text(warning_msg)
                            except Exception:
                                pass
                    
                    db.session.commit()
                    
            except Exception as e:
                logger.error(f"Real-time message processing error: {e}")
        urls = re.findall(r'http[s]?://\S+', update.message.text)
        if not urls:
            return
        
        user = update.effective_user
        chat = update.effective_chat
        
        try:
            from app import app as flask_app, db
            from models import get_or_create_user, get_or_create_group, ScanLog
            from threat_intelligence import ThreatIntelligence
            
            with flask_app.app_context():
                # Get or create user
                db_user = get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                
                # Get or create group if in group chat
                db_group = None
                if chat.type in ['group', 'supergroup']:
                    db_group = get_or_create_group(
                        group_id=chat.id,
                        name=chat.title,
                        group_type=chat.type
                    )
                
                # Initialize threat intelligence
                ti = ThreatIntelligence()
                
                scan_results = []
                threats_found = 0
                
                # Scan each URL
                for url in urls:
                    try:
                        # Perform actual threat intelligence scan
                        scan_result = ti.scan_url(url)
                        
                        # Log the scan
                        scan_log = ScanLog(
                            user_id=db_user.id,
                            group_id=db_group.id if db_group else None,
                            domain=ti.extract_domain(url),
                            url=url,
                            scan_type='group' if db_group else 'individual',
                            scan_result=scan_result['classification'],
                            threat_sources=str(scan_result.get('sources', [])),
                            confidence_score=scan_result.get('confidence', 0.0),
                            action_taken='scanned',
                            message_deleted=False
                        )
                        db.session.add(scan_log)
                        
                        scan_results.append(scan_result)
                        
                        # Check threat confidence level for automatic blocking
                        confidence = scan_result.get('confidence', 0.0)
                        auto_block_threshold = float(os.environ.get('AUTO_BLOCK_THRESHOLD', '0.70'))
                        auto_block_enabled = os.environ.get('AUTO_BLOCK_ENABLED', 'True').lower() == 'true'
                        should_block = auto_block_enabled and confidence >= auto_block_threshold
                        
                        if scan_result['classification'] in ['malicious', 'suspicious', 'questionable']:
                            threats_found += 1
                            
                            # Enhanced threat notification
                            threat_level = scan_result.get('threat_level', 'unknown')
                            threat_categories = scan_result.get('threat_categories', [])
                            
                            threat_details = f"⚠️ THREAT DETECTED: {scan_result['classification'].upper()}\n"
                            threat_details += f"🎯 Threat Level: {threat_level}\n"
                            threat_details += f"🔍 URL: {url}\n"
                            
                            if threat_categories:
                                threat_details += f"📋 Types: {', '.join(threat_categories)}\n"
                                
                            threat_details += f"🛡️ Confidence: {scan_result['confidence']:.0%}\n"
                            threat_details += f"📊 Sources: {', '.join(scan_result['sources'])}"
                            
                            # AUTOMATIC BLOCKING for high-confidence threats
                            if should_block and db_group and chat.type in ['group', 'supergroup']:
                                try:
                                    # Check if bot has admin rights to delete messages
                                    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                                    if bot_member.can_delete_messages:
                                        # Delete the malicious message
                                        await context.bot.delete_message(chat.id, update.message.message_id)
                                        
                                        # Update scan log to reflect blocking action
                                        scan_log.action_taken = 'message_deleted'
                                        scan_log.message_deleted = True
                                        
                                        # Send blocking notification
                                        block_msg = f"🚫 MESSAGE BLOCKED!\n\n"
                                        block_msg += threat_details
                                        block_msg += f"\n\n🛡️ Action: Message automatically deleted"
                                        block_msg += f"\n👤 User: @{user.username or user.first_name}"
                                        
                                        # Send private notification to user
                                        try:
                                            await context.bot.send_message(
                                                chat_id=user.id,
                                                text=f"⚠️ Your message in '{chat.title}' was blocked due to malicious content.\n\n{threat_details}"
                                            )
                                        except Exception:
                                            pass  # User may have blocked the bot
                                            
                                        # Send public warning
                                        await context.bot.send_message(chat.id, block_msg)
                                        
                                        # Update group threat statistics
                                        db_group.threats_blocked = (db_group.threats_blocked or 0) + 1
                                        
                                    else:
                                        # Bot doesn't have delete permissions, just warn
                                        threat_details += f"\n\n⚠️ AUTOMATIC BLOCKING DISABLED"
                                        threat_details += f"\nBot needs 'Delete Messages' permission for automatic blocking"
                                        await update.message.reply_text(threat_details)
                                        scan_log.action_taken = 'warning_only'
                                        
                                except Exception as e:
                                    logger.error(f"Error deleting message: {e}")
                                    threat_details += f"\n\n⚠️ Failed to block message automatically"
                                    await update.message.reply_text(threat_details)
                                    scan_log.action_taken = 'block_failed'
                            else:
                                # Just send threat alert for lower confidence or private chats
                                await update.message.reply_text(threat_details)
                                scan_log.action_taken = 'warning_sent'
                            
                    except Exception as e:
                        logger.error(f"Error scanning URL {url}: {e}")
                        # Log failed scan
                        scan_log = ScanLog(
                            user_id=db_user.id,
                            group_id=db_group.id if db_group else None,
                            domain=url.split('//')[1].split('/')[0] if '//' in url else url,
                            url=url,
                            scan_type='group' if db_group else 'individual',
                            scan_result='error',
                            confidence_score=0.0,
                            action_taken='error'
                        )
                        db.session.add(scan_log)
                
                db.session.commit()
                logger.info(f"Scanned {len(urls)} URLs for user {user.id}")
                
                # Send response based on results
                if threats_found > 0:
                    threat_msg = f"⚠️ THREAT DETECTED!\n\n"
                    threat_msg += f"Found {threats_found} suspicious URL(s)\n"
                    threat_msg += f"Please be careful when clicking links!\n\n"
                    threat_msg += f"🔍 Scanned {len(urls)} URL(s)"
                    await update.message.reply_text(threat_msg)
                else:
                    safe_msg = f"✅ URLs Safe\n\n"
                    safe_msg += f"🔍 Scanned {len(urls)} URL(s)\n"
                    safe_msg += f"✅ All links appear safe\n"
                    safe_msg += f"🛡️ Protection active"
                    await update.message.reply_text(safe_msg)
                    
        except Exception as e:
            logger.error(f"Message handler error: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"🔍 Scanned {len(urls)} URL(s) - Processing completed")
    
    async def start_bot(self):
        """Start the bot with proper handlers"""
        try:
            token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if not token:
                logger.error("TELEGRAM_BOT_TOKEN not found")
                return False
            
            self.application = Application.builder().token(token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
            self.application.add_handler(CommandHandler("scan", self.scan_command))
            self.application.add_handler(CommandHandler("scan_all", self.scan_all_command))
            self.application.add_handler(CommandHandler("pricing", self.pricing_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            
            # Admin commands for payment verification
            from payment_verification import handle_approve_command, handle_reject_command, handle_pending_command
            
            self.application.add_handler(CommandHandler("approve", handle_approve_command))
            self.application.add_handler(CommandHandler("reject", handle_reject_command))
            self.application.add_handler(CommandHandler("pending", handle_pending_command))
            
            # Add admin configuration command
            self.application.add_handler(CommandHandler("config", self.config_command))
            
            # Add message handler for URL scanning
            self.application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_message
            ))
            
            # Initialize and start bot
            await self.application.initialize()
            bot_info = await self.application.bot.get_me()
            logger.info(f"Bot started: {bot_info.first_name} (@{bot_info.username})")
            
            self.running = True
            await self.application.start()
            
            # Start polling
            logger.info("Starting bot polling...")
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Bot startup error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_in_thread(self):
        """Run bot in separate thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def run():
                await self.start_bot()
                while self.running:
                    await asyncio.sleep(1)
            
            loop.run_until_complete(run())
            
        except Exception as e:
            logger.error(f"Bot thread error: {e}")

# Global bot instance
bot_runner = SecurityBotRunner()

def start_security_bot():
    """Function to start bot in thread"""
    thread = threading.Thread(target=bot_runner.run_in_thread, daemon=True)
    thread.start()
    logger.info("Security bot thread started")
    return thread