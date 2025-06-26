"""
Background payment monitoring service for polling-based verification
Complements webhook system for comprehensive payment tracking
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from models import Payment, db
from webhook_payment_processor import webhook_processor
from app import app

logger = logging.getLogger(__name__)

class PaymentMonitor:
    """Background service to monitor pending payments"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 300  # 5 minutes
    
    async def start_monitoring(self):
        """Start the payment monitoring service"""
        self.running = True
        logger.info("Payment monitoring service started")
        
        while self.running:
            try:
                await self.check_pending_payments()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in payment monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_monitoring(self):
        """Stop the payment monitoring service"""
        self.running = False
        logger.info("Payment monitoring service stopped")
    
    async def check_pending_payments(self):
        """Check all pending payments for confirmation"""
        try:
            with app.app_context():
                # Get pending payments older than 5 minutes
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
                
                pending_payments = Payment.query.filter(
                    Payment.status == 'pending',
                    Payment.created_at <= cutoff_time,
                    Payment.payment_method == 'crypto'
                ).all()
                
                logger.info(f"Checking {len(pending_payments)} pending payments")
                
                for payment in pending_payments:
                    await self.verify_payment(payment)
                    
        except Exception as e:
            logger.error(f"Error checking pending payments: {e}")
    
    async def verify_payment(self, payment):
        """Verify individual payment by checking blockchain"""
        try:
            if payment.cryptocurrency == 'BTC':
                await self.verify_btc_payment(payment)
            elif payment.cryptocurrency in ['TRX', 'USDT']:
                await self.verify_tron_payment(payment)
            
        except Exception as e:
            logger.error(f"Error verifying payment {payment.id}: {e}")
    
    async def verify_btc_payment(self, payment):
        """Verify BTC payment by checking blockchain"""
        try:
            import requests
            
            # Check transactions to our address
            url = f"https://blockstream.info/api/address/{payment.payment_address}/txs"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                return
            
            transactions = response.json()
            
            for tx in transactions:
                # Check if transaction is recent (within payment window)
                tx_time = datetime.fromtimestamp(tx.get('status', {}).get('block_time', 0), timezone.utc)
                if tx_time < payment.created_at:
                    continue
                
                # Check outputs for payment to our address
                for output in tx.get('vout', []):
                    if output.get('scriptpubkey_address') == payment.payment_address:
                        amount_btc = output.get('value', 0) / 100000000
                        
                        # Check if amount matches (with tolerance)
                        if abs(amount_btc - payment.amount_crypto) <= 0.00001:
                            # Payment found - update and process
                            payment.transaction_id = tx['txid']
                            payment.status = 'confirmed'
                            payment.confirmed_at = datetime.now(timezone.utc)
                            db.session.commit()
                            
                            # Process the payment
                            webhook_processor.process_confirmed_payment(payment)
                            logger.info(f"BTC payment {payment.id} verified and processed")
                            return
                            
        except Exception as e:
            logger.error(f"Error verifying BTC payment {payment.id}: {e}")
    
    async def verify_tron_payment(self, payment):
        """Verify TRON/USDT payment by checking blockchain"""
        try:
            import requests
            
            # Check TRON address transactions
            if payment.cryptocurrency == 'TRX':
                url = f"https://api.trongrid.io/v1/accounts/{payment.payment_address}/transactions"
            else:  # USDT
                url = f"https://api.trongrid.io/v1/accounts/{payment.payment_address}/transactions/trc20"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                return
            
            data = response.json()
            transactions = data.get('data', [])
            
            for tx in transactions:
                # Check transaction timestamp
                tx_time = datetime.fromtimestamp(tx.get('block_timestamp', 0) / 1000, timezone.utc)
                if tx_time < payment.created_at:
                    continue
                
                # For TRX transfers
                if payment.cryptocurrency == 'TRX':
                    raw_data = tx.get('raw_data', {})
                    contracts = raw_data.get('contract', [])
                    
                    for contract in contracts:
                        if contract.get('type') == 'TransferContract':
                            parameter = contract.get('parameter', {}).get('value', {})
                            amount = parameter.get('amount', 0) / 1000000  # Convert from sun
                            
                            if abs(amount - payment.amount_crypto) <= 0.1:
                                payment.transaction_id = tx['txID']
                                payment.status = 'confirmed'
                                payment.confirmed_at = datetime.now(timezone.utc)
                                db.session.commit()
                                
                                webhook_processor.process_confirmed_payment(payment)
                                logger.info(f"TRX payment {payment.id} verified and processed")
                                return
                
                # For USDT transfers
                elif payment.cryptocurrency == 'USDT':
                    token_info = tx.get('token_info', {})
                    if token_info.get('symbol') == 'USDT':
                        amount = float(tx.get('value', 0)) / (10 ** token_info.get('decimals', 6))
                        
                        if abs(amount - payment.amount_crypto) <= 0.01:
                            payment.transaction_id = tx['transaction_id']
                            payment.status = 'confirmed'
                            payment.confirmed_at = datetime.now(timezone.utc)
                            db.session.commit()
                            
                            webhook_processor.process_confirmed_payment(payment)
                            logger.info(f"USDT payment {payment.id} verified and processed")
                            return
                            
        except Exception as e:
            logger.error(f"Error verifying TRON payment {payment.id}: {e}")

# Global monitor instance
payment_monitor = PaymentMonitor()