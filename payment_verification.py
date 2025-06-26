#!/usr/bin/env python3
"""
Payment verification system for manual confirmation
"""

import os
import logging
from datetime import datetime, timezone
from app import app, db
from models import Payment, User
import telegram
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class PaymentVerification:
    """Manual payment verification system"""
    
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.environ.get('ADMIN_CHAT_ID')
        
    async def notify_admin_payment(self, payment_id, user_id, amount, currency, transaction_hash=None):
        """Notify admin about new payment for verification"""
        try:
            if not self.bot_token:
                logger.error("Bot token not configured")
                return False
                
            bot = telegram.Bot(self.bot_token)
            
            with app.app_context():
                payment = Payment.query.get(payment_id)
                user = User.query.get(user_id)
                
                if not payment or not user:
                    return False
                
                notify_msg = f"🔔 New Payment Received\n\n"
                notify_msg += f"Payment ID: {payment_id}\n"
                notify_msg += f"User: {user.first_name} (@{user.username})\n"
                notify_msg += f"Amount: {amount} {currency}\n"
                notify_msg += f"Plan: {payment.purchase_type}\n"
                
                if transaction_hash:
                    notify_msg += f"TX Hash: {transaction_hash}\n"
                
                notify_msg += f"Created: {payment.created_at}\n\n"
                notify_msg += f"To approve: /approve {payment_id}\n"
                notify_msg += f"To reject: /reject {payment_id}"
                
                # Send to admin chat or fallback to logs
                if self.admin_chat_id:
                    await bot.send_message(chat_id=self.admin_chat_id, text=notify_msg)
                else:
                    logger.info(f"Payment notification: {notify_msg}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")
            return False
    
    def approve_payment(self, payment_id, admin_user_id=None):
        """Approve payment and activate subscription"""
        try:
            with app.app_context():
                payment = Payment.query.get(payment_id)
                
                if not payment:
                    return {'success': False, 'error': 'Payment not found'}
                
                if payment.status == 'confirmed':
                    return {'success': False, 'error': 'Payment already confirmed'}
                
                # Update payment status
                payment.status = 'confirmed'
                payment.confirmed_at = datetime.now(timezone.utc)
                
                # Update user quota based on plan
                user = User.query.get(payment.user_id)
                if user:
                    if 'pro' in payment.purchase_type:
                        user.individual_scans_remaining += 500
                        user.tier = 'pro'
                    elif 'business' in payment.purchase_type:
                        user.individual_scans_remaining = 999999  # Unlimited
                        user.tier = 'business'
                
                db.session.commit()
                
                logger.info(f"Payment {payment_id} approved by admin {admin_user_id}")
                
                return {
                    'success': True, 
                    'message': f'Payment approved. User quota updated.',
                    'user_id': user.telegram_id if user else None
                }
                
        except Exception as e:
            logger.error(f"Error approving payment: {e}")
            return {'success': False, 'error': str(e)}
    
    def reject_payment(self, payment_id, reason=None, admin_user_id=None):
        """Reject payment"""
        try:
            with app.app_context():
                payment = Payment.query.get(payment_id)
                
                if not payment:
                    return {'success': False, 'error': 'Payment not found'}
                
                payment.status = 'rejected'
                
                db.session.commit()
                
                logger.info(f"Payment {payment_id} rejected by admin {admin_user_id}. Reason: {reason}")
                
                return {'success': True, 'message': 'Payment rejected'}
                
        except Exception as e:
            logger.error(f"Error rejecting payment: {e}")
            return {'success': False, 'error': str(e)}
    
    async def notify_user_payment_status(self, payment_id, approved=True):
        """Notify user about payment status"""
        try:
            if not self.bot_token:
                return False
                
            bot = telegram.Bot(self.bot_token)
            
            with app.app_context():
                payment = Payment.query.get(payment_id)
                user = User.query.get(payment.user_id)
                
                if not payment or not user:
                    return False
                
                if approved:
                    msg = f"✅ Payment Confirmed!\n\n"
                    msg += f"Your {payment.purchase_type} subscription is now active.\n"
                    msg += f"Scans remaining: {user.individual_scans_remaining}\n\n"
                    msg += f"Thank you for upgrading!"
                else:
                    msg = f"❌ Payment Rejected\n\n"
                    msg += f"Your payment for {payment.purchase_type} was not confirmed.\n"
                    msg += f"Please contact support for assistance."
                
                await bot.send_message(chat_id=user.telegram_id, text=msg)
                return True
                
        except Exception as e:
            logger.error(f"Error notifying user: {e}")
            return False
    
    def get_pending_payments(self):
        """Get all pending payments for admin review"""
        try:
            with app.app_context():
                payments = Payment.query.filter_by(status='pending').order_by(Payment.created_at.desc()).all()
                
                result = []
                for payment in payments:
                    user = User.query.get(payment.user_id)
                    result.append({
                        'id': payment.id,
                        'user_name': user.first_name if user else 'Unknown',
                        'username': user.username if user else 'N/A',
                        'amount': payment.amount_usd,
                        'currency': payment.cryptocurrency or 'USD',
                        'plan': payment.purchase_type,
                        'created': payment.created_at,
                        'transaction_id': payment.transaction_id
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting pending payments: {e}")
            return []

# Admin command handlers for bot
async def handle_approve_command(update, context):
    """Handle /approve command"""
    if not context.args:
        await update.message.reply_text("Usage: /approve <payment_id>")
        return
    
    try:
        payment_id = int(context.args[0])
        verifier = PaymentVerification()
        result = verifier.approve_payment(payment_id, update.effective_user.id)
        
        if result['success']:
            await update.message.reply_text(f"✅ {result['message']}")
            # Notify user
            await verifier.notify_user_payment_status(payment_id, approved=True)
        else:
            await update.message.reply_text(f"❌ {result['error']}")
            
    except ValueError:
        await update.message.reply_text("Invalid payment ID")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_reject_command(update, context):
    """Handle /reject command"""
    if not context.args:
        await update.message.reply_text("Usage: /reject <payment_id> [reason]")
        return
    
    try:
        payment_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else None
        
        verifier = PaymentVerification()
        result = verifier.reject_payment(payment_id, reason, update.effective_user.id)
        
        if result['success']:
            await update.message.reply_text(f"❌ {result['message']}")
            # Notify user
            await verifier.notify_user_payment_status(payment_id, approved=False)
        else:
            await update.message.reply_text(f"❌ {result['error']}")
            
    except ValueError:
        await update.message.reply_text("Invalid payment ID")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_pending_command(update, context):
    """Handle /pending command to show pending payments"""
    try:
        verifier = PaymentVerification()
        pending = verifier.get_pending_payments()
        
        if not pending:
            await update.message.reply_text("No pending payments")
            return
        
        msg = "📋 Pending Payments:\n\n"
        for payment in pending[:10]:  # Show last 10
            msg += f"ID: {payment['id']}\n"
            msg += f"User: {payment['user_name']} (@{payment['username']})\n"
            msg += f"Amount: ${payment['amount']} {payment['currency']}\n"
            msg += f"Plan: {payment['plan']}\n"
            msg += f"Date: {payment['created'].strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await update.message.reply_text(msg)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")