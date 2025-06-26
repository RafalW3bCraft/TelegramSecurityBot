"""
Webhook routes for real-time payment processing
Handles BTC and TRON/USDT-TRC20 payment confirmations
"""

import json
import logging
from flask import request, jsonify, Blueprint
from models import Payment, db
from webhook_payment_processor import webhook_processor

logger = logging.getLogger(__name__)

# Create blueprint for webhook routes
webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

@webhook_bp.route('/btc/<int:payment_id>', methods=['POST'])
def btc_webhook(payment_id):
    """Handle BTC payment webhook from BlockCypher"""
    try:
        # Verify signature if provided
        signature = request.headers.get('X-Signature')
        if signature:
            if not webhook_processor.verify_webhook_signature(request.data, signature):
                logger.warning("Invalid BTC webhook signature")
                return jsonify({"status": "error", "message": "Invalid signature"}), 401
        
        # Get payment from database
        payment = Payment.query.get(payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return jsonify({"status": "error", "message": "Payment not found"}), 404
        
        if payment.status in ['completed', 'confirmed']:
            logger.info(f"Payment {payment_id} already processed")
            return jsonify({"status": "already_processed"}), 200
        
        # Parse webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            logger.error("No webhook data received")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        # Verify and process payment
        success = webhook_processor.verify_btc_payment(payment, webhook_data)
        
        if success:
            logger.info(f"BTC payment {payment_id} verified successfully")
            return jsonify({"status": "success"}), 200
        else:
            logger.warning(f"BTC payment {payment_id} verification failed")
            return jsonify({"status": "verification_failed"}), 400
            
    except Exception as e:
        logger.error(f"Error processing BTC webhook: {e}")
        return jsonify({"status": "error", "message": "Internal error"}), 500

@webhook_bp.route('/tron/<int:payment_id>', methods=['POST'])
def tron_webhook(payment_id):
    """Handle TRON/USDT-TRC20 payment webhook"""
    try:
        # Verify signature if provided
        signature = request.headers.get('X-Signature')
        if signature:
            if not webhook_processor.verify_webhook_signature(request.data, signature):
                logger.warning("Invalid TRON webhook signature")
                return jsonify({"status": "error", "message": "Invalid signature"}), 401
        
        # Get payment from database
        payment = Payment.query.get(payment_id)
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return jsonify({"status": "error", "message": "Payment not found"}), 404
        
        if payment.status in ['completed', 'confirmed']:
            logger.info(f"Payment {payment_id} already processed")
            return jsonify({"status": "already_processed"}), 200
        
        # Parse webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            logger.error("No webhook data received")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        # Verify and process payment
        success = webhook_processor.verify_tron_payment(payment, webhook_data)
        
        if success:
            logger.info(f"TRON payment {payment_id} verified successfully")
            return jsonify({"status": "success"}), 200
        else:
            logger.warning(f"TRON payment {payment_id} verification failed")
            return jsonify({"status": "verification_failed"}), 400
            
    except Exception as e:
        logger.error(f"Error processing TRON webhook: {e}")
        return jsonify({"status": "error", "message": "Internal error"}), 500

@webhook_bp.route('/test/<int:payment_id>', methods=['POST'])
def test_webhook(payment_id):
    """Test webhook endpoint for development"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"status": "error", "message": "Payment not found"}), 404
        
        # Simulate payment confirmation for testing
        if payment.cryptocurrency == 'BTC':
            test_data = {
                "hash": "test_btc_transaction_hash",
                "outputs": [{
                    "addresses": [webhook_processor.btc_address],
                    "value": int(payment.amount_crypto * 100000000)  # Convert to satoshi
                }],
                "confirmations": 1
            }
            success = webhook_processor.verify_btc_payment(payment, test_data)
        else:
            test_data = {
                "txID": "test_tron_transaction_hash"
            }
            # For testing, we'll directly process the payment
            success = webhook_processor.process_confirmed_payment(payment)
        
        if success:
            return jsonify({"status": "test_success"}), 200
        else:
            return jsonify({"status": "test_failed"}), 400
            
    except Exception as e:
        logger.error(f"Error in test webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_bp.route('/status/<int:payment_id>', methods=['GET'])
def payment_status(payment_id):
    """Check payment status"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404
        
        return jsonify({
            "payment_id": payment.id,
            "status": payment.status,
            "cryptocurrency": payment.cryptocurrency,
            "amount": payment.amount_crypto,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at.isoformat(),
            "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        return jsonify({"error": "Internal error"}), 500