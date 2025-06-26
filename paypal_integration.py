"""
PayPal integration for credit-based subscription payments
Handles PayPal checkout, payment verification, and credit activation
"""

import os
import logging
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PayPalIntegration:
    """PayPal payment processing for credit purchases"""
    
    def __init__(self):
        # Use credentials from .env file
        self.client_id = os.environ.get('PAYPAL_CLIENT_ID')
        self.client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        self.mode = os.environ.get('PAYPAL_MODE', 'live')  # Default to live mode
        
        # PayPal API URLs
        if self.mode == 'live':
            self.base_url = 'https://api-m.paypal.com'
            self.web_url = 'https://www.paypal.com'
        else:
            self.base_url = 'https://api-m.sandbox.paypal.com'
            self.web_url = 'https://www.sandbox.paypal.com'
        
        self.access_token = None
        self.token_expires = None
    
    def get_access_token(self) -> Optional[str]:
        """Get PayPal access token"""
        if not self.client_id or not self.client_secret:
            logger.error("PayPal credentials not configured")
            return None
        
        # Check if current token is still valid
        if self.access_token and self.token_expires:
            if datetime.now(timezone.utc) < self.token_expires:
                return self.access_token
        
        try:
            url = f"{self.base_url}/v1/oauth2/token"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            
            data = 'grant_type=client_credentials'
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
                return self.access_token
            else:
                logger.error(f"PayPal token error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"PayPal authentication error: {e}")
            return None
    
    def create_payment_order(self, payment_id: int, amount: float, description: str, 
                           success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create PayPal payment order"""
        token = self.get_access_token()
        if not token:
            return {'error': 'PayPal authentication failed'}
        
        try:
            url = f"{self.base_url}/v2/checkout/orders"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'PayPal-Request-Id': f'SECBOT-{payment_id}-{int(datetime.now().timestamp())}'
            }
            
            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'reference_id': str(payment_id),
                    'amount': {
                        'currency_code': 'USD',
                        'value': f'{amount:.2f}'
                    },
                    'description': description
                }],
                'payment_source': {
                    'paypal': {
                        'experience_context': {
                            'payment_method_preference': 'IMMEDIATE_PAYMENT_REQUIRED',
                            'brand_name': 'Security Bot',
                            'locale': 'en-US',
                            'landing_page': 'LOGIN',
                            'shipping_preference': 'NO_SHIPPING',
                            'user_action': 'PAY_NOW',
                            'return_url': success_url,
                            'cancel_url': cancel_url
                        }
                    }
                }
            }
            
            response = requests.post(url, headers=headers, json=order_data)
            
            if response.status_code == 201:
                order = response.json()
                # Find the approval URL from links
                approval_url = None
                for link in order.get('links', []):
                    if link.get('rel') == 'payer-action':
                        approval_url = link.get('href')
                        break
                
                if not approval_url:
                    # Fallback to approve link
                    for link in order.get('links', []):
                        if link.get('rel') == 'approve':
                            approval_url = link.get('href')
                            break
                
                return {
                    'success': True,
                    'order_id': order['id'],
                    'approval_url': approval_url
                }
            else:
                logger.error(f"PayPal order creation error: {response.status_code} - {response.text}")
                return {'error': f'Order creation failed: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"PayPal order creation error: {e}")
            return {'error': str(e)}
    
    def capture_payment(self, order_id: str) -> Dict[str, Any]:
        """Capture PayPal payment after approval"""
        token = self.get_access_token()
        if not token:
            return {'error': 'PayPal authentication failed'}
        
        try:
            url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.post(url, headers=headers, json={})
            
            if response.status_code == 201:
                capture_data = response.json()
                return {
                    'success': True,
                    'capture_id': capture_data['id'],
                    'status': capture_data['status'],
                    'amount': capture_data['purchase_units'][0]['payments']['captures'][0]['amount']['value'],
                    'transaction_id': capture_data['purchase_units'][0]['payments']['captures'][0]['id']
                }
            else:
                logger.error(f"PayPal capture error: {response.status_code} - {response.text}")
                return {'error': f'Payment capture failed: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"PayPal capture error: {e}")
            return {'error': str(e)}
    
    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get PayPal order details"""
        token = self.get_access_token()
        if not token:
            return {'error': 'PayPal authentication failed'}
        
        try:
            url = f"{self.base_url}/v2/checkout/orders/{order_id}"
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return {'success': True, 'order': response.json()}
            else:
                logger.error(f"PayPal order details error: {response.status_code} - {response.text}")
                return {'error': f'Failed to get order details: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"PayPal order details error: {e}")
            return {'error': str(e)}

def process_paypal_payment_success(payment_id: int, order_id: str) -> Dict[str, Any]:
    """Process successful PayPal payment and activate credits"""
    try:
        from app import app as flask_app, db
        from models import Payment, User
        
        with flask_app.app_context():
            # Get payment record
            payment = Payment.query.get(payment_id)
            if not payment:
                return {'error': 'Payment record not found'}
            
            if payment.status == 'confirmed':
                return {'error': 'Payment already processed'}
            
            # Initialize PayPal integration
            paypal = PayPalIntegration()
            
            # Capture the payment
            capture_result = paypal.capture_payment(order_id)
            
            if capture_result.get('success'):
                # Update payment record
                payment.status = 'confirmed'
                payment.confirmed_at = datetime.now(timezone.utc)
                payment.transaction_id = capture_result.get('transaction_id')
                
                # Add credits to user account
                user = User.query.get(payment.user_id)
                if user:
                    user.add_credits(payment.quantity)
                    logger.info(f"Added {payment.quantity} credits to user {user.telegram_id}")
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f'Payment confirmed! {payment.quantity} credits added to your account.',
                    'credits_added': payment.quantity,
                    'transaction_id': capture_result.get('transaction_id')
                }
            else:
                payment.status = 'failed'
                db.session.commit()
                return {'error': f'Payment capture failed: {capture_result.get("error")}'}
                
    except Exception as e:
        logger.error(f"PayPal payment processing error: {e}")
        return {'error': str(e)}