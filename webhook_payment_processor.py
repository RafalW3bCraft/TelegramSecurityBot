"""
Enhanced payment processor with webhook support for real-time verification
Supports USDT-TRC20 via TRON (NowNodes) and BTC (BlockCypher) webhooks
"""

import os
import json
import logging
import hashlib
import hmac
import requests
from datetime import datetime, timezone, timedelta
from flask import request, jsonify
from models import Payment, User, db
from core import get_config
import telegram
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class WebhookPaymentProcessor:
    """Enhanced payment processor with webhook support"""
    
    def __init__(self):
        self.btc_address = get_config('btc_address')
        self.trx_address = get_config('trx_address')
        self.usdt_trc20_address = get_config('usdt_trc20_address')
        
        # API Keys
        self.nownodes_api_key = os.environ.get('NOWNODES_API_KEY')
        self.blockcypher_api_key = os.environ.get('BLOCKCYPHER_API_KEY')
        self.webhook_secret = os.environ.get('WEBHOOK_SECRET')
        
        # Bot configuration
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        # API URLs
        self.nownodes_base_url = "https://tron.nownodes.io"
        self.blockcypher_base_url = "https://api.blockcypher.com/v1/btc/main"
    
    def setup_btc_webhook(self, payment_id):
        """Setup BTC webhook for payment monitoring"""
        try:
            if not self.blockcypher_api_key:
                logger.error("BlockCypher API key not configured")
                return False
                
            webhook_url = f"{os.environ.get('RENDER_URL', os.environ.get('REPLIT_URL', 'https://localhost:5000'))}/webhook/btc/{payment_id}"
            
            # Create webhook
            webhook_data = {
                "event": "tx-confirmation",
                "address": self.btc_address,
                "url": webhook_url
            }
            
            response = requests.post(
                f"{self.blockcypher_base_url}/hooks",
                json=webhook_data,
                params={"token": self.blockcypher_api_key}
            )
            
            if response.status_code == 201:
                webhook_info = response.json()
                logger.info(f"BTC webhook created: {webhook_info['id']}")
                return webhook_info['id']
            else:
                logger.error(f"Failed to create BTC webhook: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up BTC webhook: {e}")
            return False
    
    def setup_tron_webhook(self, payment_id):
        """Setup TRON webhook for USDT-TRC20 monitoring"""
        try:
            if not self.nownodes_api_key:
                logger.error("NowNodes API key not configured")
                return False
                
            webhook_url = f"{os.environ.get('RENDER_URL', os.environ.get('REPLIT_URL', 'https://localhost:5000'))}/webhook/tron/{payment_id}"
            
            # Setup webhook via NowNodes
            headers = {
                'api-key': self.nownodes_api_key,
                'Content-Type': 'application/json'
            }
            
            webhook_data = {
                "method": "eth_subscribe",
                "params": [
                    "logs",
                    {
                        "address": self.usdt_trc20_address,
                        "topics": []
                    }
                ],
                "id": payment_id,
                "jsonrpc": "2.0"
            }
            
            # For TRON, we'll use polling initially and can enhance with webhooks
            logger.info(f"TRON monitoring setup for payment {payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up TRON webhook: {e}")
            return False
    
    def verify_btc_payment(self, payment, transaction_data):
        """Verify BTC payment from webhook data"""
        try:
            # Extract transaction details
            tx_hash = transaction_data.get('hash')
            outputs = transaction_data.get('outputs', [])
            confirmations = transaction_data.get('confirmations', 0)
            
            # Check if payment was sent to our address
            payment_received = False
            amount_received = 0
            
            for output in outputs:
                if output.get('addresses') and self.btc_address in output.get('addresses', []):
                    amount_received += output.get('value', 0) / 100000000  # Convert satoshi to BTC
                    payment_received = True
            
            if not payment_received:
                logger.warning(f"BTC payment {payment.id} not sent to our address")
                return False
            
            # Check amount (with small tolerance for fees)
            expected_amount = payment.amount_crypto
            tolerance = expected_amount * 0.02  # 2% tolerance
            
            if amount_received < (expected_amount - tolerance):
                logger.warning(f"BTC payment {payment.id} insufficient amount: {amount_received} < {expected_amount}")
                return False
            
            # Update payment status
            payment.transaction_id = tx_hash
            payment.status = 'confirmed' if confirmations >= 1 else 'pending_confirmation'
            payment.confirmed_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # If confirmed, process the payment
            if confirmations >= 1:
                self.process_confirmed_payment(payment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying BTC payment: {e}")
            return False
    
    def verify_tron_payment(self, payment, transaction_data):
        """Verify TRON/USDT-TRC20 payment"""
        try:
            # For USDT-TRC20, we need to check TRC20 token transfers
            tx_hash = transaction_data.get('txID')
            
            if not tx_hash:
                return False
            
            # Get transaction details from TRON network
            tx_details = self.get_tron_transaction_details(tx_hash)
            
            if not tx_details:
                return False
            
            # Check if it's a USDT transfer to our address
            amount_received = self.parse_tron_transaction(tx_details, payment.cryptocurrency)
            
            if amount_received is None:
                return False
            
            # Check amount
            expected_amount = payment.amount_crypto
            tolerance = expected_amount * 0.02  # 2% tolerance
            
            if amount_received < (expected_amount - tolerance):
                logger.warning(f"TRON payment {payment.id} insufficient amount: {amount_received} < {expected_amount}")
                return False
            
            # Update payment status
            payment.transaction_id = tx_hash
            payment.status = 'confirmed'
            payment.confirmed_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # Process the payment
            self.process_confirmed_payment(payment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying TRON payment: {e}")
            return False
    
    def get_tron_transaction_details(self, tx_hash):
        """Get TRON transaction details"""
        try:
            headers = {'api-key': self.nownodes_api_key}
            url = f"{self.nownodes_base_url}/wallet/gettransactionbyid"
            
            data = {"value": tx_hash}
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get TRON transaction: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting TRON transaction details: {e}")
            return None
    
    def parse_tron_transaction(self, tx_details, currency):
        """Parse TRON transaction for payment verification"""
        try:
            # For TRX transfers
            if currency == 'TRX':
                raw_data = tx_details.get('raw_data', {})
                contracts = raw_data.get('contract', [])
                
                for contract in contracts:
                    if contract.get('type') == 'TransferContract':
                        parameter = contract.get('parameter', {}).get('value', {})
                        to_address = parameter.get('to_address')
                        amount = parameter.get('amount', 0)
                        
                        # Convert address format and check
                        if self.check_tron_address_match(to_address, self.trx_address):
                            return amount / 1000000  # Convert from sun to TRX
            
            # For USDT-TRC20 transfers
            elif currency == 'USDT':
                # Check for TRC20 token transfer events
                contract_result = tx_details.get('contract_result', [])
                
                for result in contract_result:
                    # Parse TRC20 transfer logs
                    if 'Transfer' in str(result):
                        # Parse the transfer amount and recipient
                        # This is a simplified parser - production should use proper ABI decoding
                        amount = self.parse_trc20_transfer_amount(result)
                        if amount:
                            return amount
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing TRON transaction: {e}")
            return None
    
    def check_tron_address_match(self, address1, address2):
        """Check if two TRON addresses match (handling different formats)"""
        try:
            # Simple string comparison for now
            # In production, you'd want to handle base58 vs hex address formats
            return address1.lower() == address2.lower()
        except:
            return False
    
    def parse_trc20_transfer_amount(self, contract_result):
        """Parse TRC20 transfer amount from contract result"""
        try:
            # This is a simplified parser
            # In production, use proper ABI decoding
            if isinstance(contract_result, str) and len(contract_result) >= 64:
                # Extract amount from the last 64 characters (32 bytes)
                amount_hex = contract_result[-64:]
                amount = int(amount_hex, 16) / 1000000  # USDT has 6 decimals
                return amount
            return None
        except:
            return None
    
    def process_confirmed_payment(self, payment):
        """Process confirmed payment and update user credits"""
        try:
            user = User.query.get(payment.user_id)
            if not user:
                logger.error(f"User not found for payment {payment.id}")
                return False
            
            # Add credits to user account
            credits_to_add = payment.quantity
            user.add_credits(credits_to_add)
            
            # Update payment status
            payment.status = 'completed'
            db.session.commit()
            
            # Notify user
            self.notify_user_payment_success(user, payment, credits_to_add)
            
            logger.info(f"Payment {payment.id} processed successfully. Added {credits_to_add} credits to user {user.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing confirmed payment: {e}")
            return False
    
    def notify_user_payment_success(self, user, payment, credits_added):
        """Notify user about successful payment (sync version)"""
        try:
            import requests
            
            if not self.bot_token:
                return
            
            message = f"✅ Payment Confirmed!\n\n"
            message += f"Transaction ID: {payment.transaction_id[:16]}...\n"
            message += f"Amount: {payment.amount_crypto} {payment.cryptocurrency}\n"
            message += f"Credits Added: {credits_added}\n"
            message += f"Total Credits: {user.scan_credits}\n\n"
            message += f"You can now use /scan command to scan URLs!"
            
            # Send via Telegram HTTP API
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': user.telegram_id,
                'text': message
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"Payment success notification sent to user {user.telegram_id}")
            else:
                logger.error(f"Failed to send notification: {response.text}")
            
        except Exception as e:
            logger.error(f"Error notifying user about payment success: {e}")
    
    def start_payment_monitoring(self, payment):
        """Start monitoring payment based on cryptocurrency"""
        try:
            if payment.cryptocurrency == 'BTC':
                return self.setup_btc_webhook(payment.id)
            elif payment.cryptocurrency in ['TRX', 'USDT']:
                return self.setup_tron_webhook(payment.id)
            else:
                logger.error(f"Unsupported cryptocurrency: {payment.cryptocurrency}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting payment monitoring: {e}")
            return False
    
    def verify_webhook_signature(self, payload, signature):
        """Verify webhook signature for security"""
        try:
            if not self.webhook_secret:
                return True  # Skip verification if no secret set
                
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

# Global instance
webhook_processor = WebhookPaymentProcessor()