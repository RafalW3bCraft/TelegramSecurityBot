import os
import json
import logging
import hashlib
import qrcode
import requests
import io
import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO
from base64 import b64encode
from models import Payment, User, db
from core import get_config

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """Handle cryptocurrency payments and verification"""
    
    def __init__(self):
        self.btc_address = get_config('btc_address')
        self.trx_address = get_config('trx_address')
        self.usdt_trc20_address = get_config('usdt_trc20_address')
        
        # Cryptocurrency API endpoints
        self.btc_api_url = "https://blockstream.info/api"
        self.trx_api_url = "https://api.trongrid.io"
        
        # Exchange rate APIs
        self.exchange_api_url = "https://api.coingecko.com/api/v3/simple/price"
    
    def get_crypto_prices(self):
        """Get current cryptocurrency prices from CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,tron,tether',
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'bitcoin': data.get('bitcoin', {}).get('usd', 50000),
                'tron': data.get('tron', {}).get('usd', 0.1),
                'tether': data.get('tether', {}).get('usd', 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching crypto prices: {e}")
            # Return fallback prices
            return {
                'bitcoin': 50000,
                'tron': 0.1,
                'tether': 1.0
            }
    
    def calculate_crypto_amounts(self, usd_amount):
        """Calculate cryptocurrency amounts for given USD amount"""
        try:
            prices = self.get_crypto_prices()
            return {
                'BTC': usd_amount / prices['bitcoin'],
                'TRX': usd_amount / prices['tron'],
                'USDT': usd_amount / prices['tether']
            }
        except Exception as e:
            logger.error(f"Error calculating crypto amounts: {e}")
            return {
                'BTC': usd_amount / 50000,
                'TRX': usd_amount / 0.1,
                'USDT': usd_amount / 1.0
            }
    
    def generate_qr_code(self, address, amount, currency):
        """Generate QR code for cryptocurrency payment"""
        try:
            # Create payment URI
            if currency == 'BTC':
                payment_uri = f"bitcoin:{address}?amount={amount}"
            elif currency == 'TRX':
                payment_uri = f"tron:{address}?amount={amount}"
            elif currency == 'USDT':
                payment_uri = f"tron:{address}?amount={amount}&token=USDT"
            else:
                payment_uri = f"{address}"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(payment_uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def get_crypto_rates(self):
        """Get current cryptocurrency exchange rates"""
        try:
            params = {
                'ids': 'bitcoin,tron,tether',
                'vs_currencies': 'usd'
            }
            
            response = requests.get(self.exchange_api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'BTC': data.get('bitcoin', {}).get('usd', 50000),  # Fallback price
                'TRX': data.get('tron', {}).get('usd', 0.08),
                'USDT': data.get('tether', {}).get('usd', 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching crypto rates: {e}")
            # Return fallback rates
            return {
                'BTC': 50000,
                'TRX': 0.08,
                'USDT': 1.0
            }
    
    def create_payment(self, user_id, amount_usd, cryptocurrency, purchase_type, quantity):
        """Create a new payment request"""
        try:
            # Get current exchange rates
            rates = self.get_crypto_rates()
            
            if cryptocurrency not in rates:
                raise ValueError(f"Unsupported cryptocurrency: {cryptocurrency}")
            
            # Calculate crypto amount
            crypto_rate = rates[cryptocurrency]
            amount_crypto = amount_usd / crypto_rate
            
            # Get wallet address
            wallet_addresses = {
                'BTC': self.btc_address,
                'TRX': self.trx_address,
                'USDT': self.usdt_trc20_address
            }
            
            payment_address = wallet_addresses.get(cryptocurrency)
            if not payment_address:
                raise ValueError(f"No wallet address configured for {cryptocurrency}")
            
            # Create payment record
            payment = Payment(
                user_id=user_id,
                payment_method='crypto',
                cryptocurrency=cryptocurrency,
                amount_usd=amount_usd,
                amount_crypto=amount_crypto,
                payment_address=payment_address,
                purchase_type=purchase_type,
                quantity=quantity,
                status='pending',
                expires_at=datetime.now(timezone.utc) + timedelta(hours=2)  # 2 hour expiry
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # Generate QR code
            qr_code_data = self._generate_qr_code(payment_address, amount_crypto, cryptocurrency)
            
            return payment
            
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise
    
    def _generate_qr_code(self, address, amount, cryptocurrency):
        """Generate QR code for payment"""
        try:
            # Create payment URI
            if cryptocurrency == 'BTC':
                uri = f"bitcoin:{address}?amount={amount:.8f}"
            elif cryptocurrency == 'TRX':
                uri = f"tron:{address}?amount={amount:.6f}"
            elif cryptocurrency == 'USDT':
                uri = f"tron:{address}?amount={amount:.6f}&token=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
            else:
                uri = f"{cryptocurrency.lower()}:{address}?amount={amount}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def verify_btc_payment(self, payment):
        """Verify Bitcoin payment"""
        try:
            address = payment.payment_address
            expected_amount = payment.amount_crypto
            created_timestamp = int(payment.created_at.timestamp())
            
            # Get address transactions
            url = f"{self.btc_api_url}/address/{address}/txs"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            transactions = response.json()
            
            for tx in transactions:
                # Check if transaction is after payment creation
                if tx.get('status', {}).get('block_time', 0) < created_timestamp:
                    continue
                
                # Check outputs for our address
                for output in tx.get('vout', []):
                    if output.get('scriptpubkey_address') == address:
                        received_amount = output.get('value', 0) / 100000000  # Convert satoshis to BTC
                        
                        # Check if amount matches (with small tolerance)
                        if abs(received_amount - expected_amount) < 0.00001:
                            return {
                                'confirmed': True,
                                'transaction_id': tx.get('txid'),
                                'amount': received_amount,
                                'confirmations': tx.get('status', {}).get('confirmed', False)
                            }
            
            return {'confirmed': False}
            
        except Exception as e:
            logger.error(f"Error verifying BTC payment: {e}")
            return {'confirmed': False, 'error': str(e)}
    
    def verify_trx_payment(self, payment):
        """Verify Tron/USDT-TRC20 payment"""
        try:
            address = payment.payment_address
            expected_amount = payment.amount_crypto
            created_timestamp = int(payment.created_at.timestamp() * 1000)  # TRX uses milliseconds
            
            # Get account transactions
            url = f"{self.trx_api_url}/v1/accounts/{address}/transactions"
            params = {
                'limit': 20,
                'order_by': 'block_timestamp,desc'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            transactions = data.get('data', [])
            
            for tx in transactions:
                # Check if transaction is after payment creation
                if tx.get('block_timestamp', 0) < created_timestamp:
                    continue
                
                # Check transaction type and amount
                if payment.cryptocurrency == 'TRX':
                    # Check TRX transfers
                    for contract in tx.get('raw_data', {}).get('contract', []):
                        if contract.get('type') == 'TransferContract':
                            value = contract.get('parameter', {}).get('value', {})
                            if value.get('to_address') == address:
                                received_amount = value.get('amount', 0) / 1000000  # Convert sun to TRX
                                
                                if abs(received_amount - expected_amount) < 0.01:
                                    return {
                                        'confirmed': True,
                                        'transaction_id': tx.get('txID'),
                                        'amount': received_amount
                                    }
                
                elif payment.cryptocurrency == 'USDT':
                    # Check USDT-TRC20 transfers
                    for contract in tx.get('raw_data', {}).get('contract', []):
                        if contract.get('type') == 'TriggerSmartContract':
                            # This is a simplified check - in production you'd need to decode the contract call
                            pass
            
            return {'confirmed': False}
            
        except Exception as e:
            logger.error(f"Error verifying TRX payment: {e}")
            return {'confirmed': False, 'error': str(e)}
    
    def process_confirmed_payment(self, payment):
        """Process a confirmed payment and update user credits"""
        try:
            if payment.status == 'confirmed':
                return True
            
            from models import User
            
            # Update payment status
            payment.status = 'confirmed'
            payment.confirmed_at = datetime.now(timezone.utc)
            
            # Update user credits based on purchase type
            user = User.query.get(payment.user_id)
            if not user:
                logger.error(f"User not found for payment {payment.id}")
                return False
            
            if payment.purchase_type.endswith('_credits'):
                credits_to_add = payment.quantity
                user.add_credits(credits_to_add)
                logger.info(f"Added {credits_to_add} credits to user {user.telegram_id}")
            
            db.session.commit()
            
            logger.info(f"Payment {payment.id} confirmed and credits updated for user {user.telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing confirmed payment: {e}")
            db.session.rollback()
            return False
    
    def check_pending_payments(self):
        """Check all pending payments for confirmation"""
        try:
            # Get all pending payments that haven't expired
            pending_payments = Payment.query.filter(
                Payment.status == 'pending',
                Payment.expires_at > datetime.now(timezone.utc)
            ).all()
            
            for payment in pending_payments:
                if payment.cryptocurrency == 'BTC':
                    result = self.verify_btc_payment(payment)
                elif payment.cryptocurrency in ['TRX', 'USDT']:
                    result = self.verify_trx_payment(payment)
                else:
                    continue
                
                if result.get('confirmed'):
                    payment.transaction_id = result.get('transaction_id')
                    self.process_confirmed_payment(payment)
            
            # Mark expired payments as failed
            expired_payments = Payment.query.filter(
                Payment.status == 'pending',
                Payment.expires_at <= datetime.now(timezone.utc)
            ).all()
            
            for payment in expired_payments:
                payment.status = 'failed'
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error checking pending payments: {e}")
            db.session.rollback()
    
    def get_payment_stats(self):
        """Get payment statistics"""
        try:
            total_payments = Payment.query.filter_by(status='confirmed').count()
            total_revenue = db.session.query(db.func.sum(Payment.amount_usd)).filter_by(status='confirmed').scalar() or 0
            
            # Monthly revenue
            current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_revenue = db.session.query(db.func.sum(Payment.amount_usd)).filter(
                Payment.status == 'confirmed',
                Payment.confirmed_at >= current_month
            ).scalar() or 0
            
            return {
                'total_payments': total_payments,
                'total_revenue': total_revenue,
                'monthly_revenue': monthly_revenue
            }
            
        except Exception as e:
            logger.error(f"Error getting payment stats: {e}")
            return {
                'total_payments': 0,
                'total_revenue': 0,
                'monthly_revenue': 0
            }

# Create payment processor instance
payment_processor = PaymentProcessor()

logger.info("Payment processor initialized successfully")
