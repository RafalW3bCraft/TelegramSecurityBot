import logging
from datetime import datetime, timezone
from flask import render_template, request, jsonify, redirect, url_for
from sqlalchemy import func, desc
from app import app, db
from models import User, TelegramGroup, ScanLog, Payment, get_dashboard_stats
from security_middleware import require_api_key, require_admin_key
from group_scanner import GroupScanner
from payment_verification import PaymentVerification

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        stats = get_dashboard_stats()
        
        # Get recent logs for activity feed with user and group info
        recent_logs = ScanLog.query.join(User, ScanLog.user_id == User.id)\
            .outerjoin(TelegramGroup, ScanLog.group_id == TelegramGroup.id)\
            .order_by(desc(ScanLog.date)).limit(10).all()
        
        return render_template('index.html', 
                             total_groups=stats.get('total_groups', 0),
                             active_groups=stats.get('active_groups', 0),
                             total_scans=stats.get('total_scans', 0),
                             threats_blocked=stats.get('threats_blocked', 0),
                             recent_scans=stats.get('recent_scans', 0),
                             recent_threats=stats.get('recent_threats', 0),
                             total_users=stats.get('total_users', 0),
                             total_credits_purchased=stats.get('total_credits_purchased', 0),
                             total_credits_used=stats.get('total_credits_used', 0),
                             active_credit_users=stats.get('active_credit_users', 0),
                             tier_distribution=stats.get('tier_distribution', {}),
                             payment_stats=stats.get('payment_stats', {'total_revenue': 0, 'monthly_revenue': 0}),
                             recent_logs=recent_logs)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', 
                             total_groups=0,
                             active_groups=0,
                             total_scans=0,
                             threats_blocked=0,
                             recent_scans=0,
                             recent_threats=0,
                             total_users=0,
                             total_credits_purchased=0,
                             total_credits_used=0,
                             active_credit_users=0,
                             tier_distribution={},
                             payment_stats={'total_revenue': 0, 'monthly_revenue': 0},
                             recent_logs=[],
                             error=str(e))

@app.route('/dashboard')
def dashboard():
    """Admin dashboard with group management"""
    try:
        # Get filter parameters
        tier_filter = request.args.get('tier', '')
        status_filter = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        
        # Build query
        query = TelegramGroup.query
        
        if tier_filter:
            query = query.filter(TelegramGroup.tier == tier_filter)
        
        if status_filter == 'active':
            query = query.filter(TelegramGroup.active == True)
        elif status_filter == 'inactive':
            query = query.filter(TelegramGroup.active == False)
        
        # Paginate results
        groups = query.order_by(desc(TelegramGroup.created_at)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Get available tiers for filter dropdown - updated for credit model
        available_tiers = ['free', 'premium', 'enterprise']
        
        return render_template('dashboard.html',
                             groups=groups,
                             available_tiers=available_tiers,
                             current_tier_filter=tier_filter,
                             current_status_filter=status_filter)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return render_template('dashboard.html', error=str(e))

@app.route('/api/realtime-stats')
def realtime_stats():
    """API endpoint for real-time dashboard statistics"""
    try:
        stats = get_dashboard_stats()
        return jsonify({
            'status': 'success',
            'stats': {
                'total_groups': stats['total_groups'],
                'active_groups': stats['active_groups'],
                'total_scans': stats['total_scans'],
                'threats_blocked': stats['threats_blocked'],
                'total_users': stats['total_users'],
                'total_credits_purchased': stats['total_credits_purchased'],
                'total_credits_used': stats['total_credits_used'],
                'active_credit_users': stats['active_credit_users']
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting realtime stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scan-url', methods=['POST'])
@require_api_key
def scan_url_api():
    """API endpoint for URL scanning"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL required'}), 400
        
        url = data['url']
        user_id = data.get('user_id')
        group_id = data.get('group_id')
        scan_type = data.get('scan_type', 'individual')
        
        # Import threat intelligence
        from threat_intelligence import ThreatIntelligence
        ti = ThreatIntelligence()
        
        # Perform scan
        result = ti.scan_url(url)
        
        # Log the scan
        if user_id:
            scan_log = ScanLog(
                user_id=user_id,
                group_id=group_id,
                domain=ti.extract_domain(url),
                url=url,
                scan_type=scan_type,
                scan_result=result['classification'],
                threat_sources=str(result.get('sources', [])),
                confidence_score=result.get('confidence', 0.0)
            )
            db.session.add(scan_log)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error scanning URL: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user-stats/<int:telegram_id>')
@require_api_key
def user_stats(telegram_id):
    """Get user statistics and quota information"""
    try:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user scan statistics
        total_scans = ScanLog.query.filter_by(user_id=user.id).count()
        threats_found = ScanLog.query.filter_by(user_id=user.id).filter(
            ScanLog.scan_result.in_(['suspicious', 'malicious'])
        ).count()
        
        credit_summary = user.get_credit_summary()
        
        return jsonify({
            'status': 'success',
            'user': {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'scan_credits': user.scan_credits,
                'total_credits_purchased': user.total_credits_purchased,
                'total_credits_used': user.total_credits_used,
                'credit_summary': credit_summary,
                'total_scans': total_scans,
                'threats_found': threats_found,
                'created_at': user.created_at.isoformat(),
                'last_active': user.last_active.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/payment-status/<int:payment_id>')
@require_api_key
def payment_status(payment_id):
    """Check payment status"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        return jsonify({
            'status': 'success',
            'payment': {
                'id': payment.id,
                'status': payment.status,
                'amount_usd': payment.amount_usd,
                'cryptocurrency': payment.cryptocurrency,
                'payment_address': payment.payment_address,
                'created_at': payment.created_at.isoformat(),
                'confirmed_at': payment.confirmed_at.isoformat() if payment.confirmed_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/system-health')
@require_api_key
def system_health():
    """System health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Get system statistics
        stats = get_dashboard_stats()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/health')
def health():
    """Simple health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('index.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    db.session.rollback()
    return render_template('index.html', error='Internal server error'), 500

# Register additional error handlers
@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    return jsonify({'error': 'Access forbidden'}), 403

@app.errorhandler(429)
def ratelimit_handler(error):
    """Handle rate limit exceeded"""
    return jsonify({'error': 'Rate limit exceeded', 'retry_after': 60}), 429

# Context processors for templates
@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def moment():
        return datetime.now(timezone.utc)
    
    return dict(moment=moment)

# Admin routes merged from admin_routes.py
@app.route('/admin/groups')
@require_admin_key
def admin_groups():
    """Admin view of all groups"""
    try:
        groups = TelegramGroup.query.order_by(TelegramGroup.last_active.desc()).all()
        
        group_data = []
        for group in groups:
            recent_scans = ScanLog.query.filter_by(group_id=group.id).count()
            threats_found = ScanLog.query.filter(
                ScanLog.group_id == group.id,
                ScanLog.scan_result.in_(['malicious', 'suspicious'])
            ).count()
            
            group_data.append({
                'id': group.id,
                'name': group.name,
                'group_id': group.group_id,
                'type': group.type,
                'tier': group.tier,
                'active': group.active,
                'total_scans': recent_scans,
                'threats_blocked': threats_found,
                'last_active': group.last_active,
                'created_at': group.created_at
            })
        
        return jsonify({
            'success': True,
            'groups': group_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching admin groups: {e}")
        return jsonify({'error': 'Failed to fetch groups'}), 500

@app.route('/api/timeline-data')
def api_timeline_data():
    """Get real timeline data for dashboard charts"""
    try:
        from datetime import datetime, timedelta
        
        # Get scan activity for last 24 hours
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        # Query real scan logs grouped by hour
        hourly_scans = []
        for i in range(24):
            hour_start = start_time + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            
            count = ScanLog.query.filter(
                ScanLog.date >= hour_start,
                ScanLog.date < hour_end
            ).count()
            
            hourly_scans.append(count)
        
        return jsonify({
            'timeline': hourly_scans,
            'labels': [f"{(datetime.now().hour - i) % 24:02d}:00" for i in range(23, -1, -1)]
        })
    except Exception as e:
        logger.error(f"Timeline data error: {e}")
        return jsonify({'timeline': [0] * 24, 'labels': []})

@app.route('/api/real-time-stats')
def api_real_time_stats():
    """Get real-time statistics for dashboard"""
    try:
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Real-time stats error: {e}")
        return jsonify({})

@app.route('/admin/groups/<int:group_id>/report')
@require_admin_key
def group_report(group_id):
    """Get detailed group security report"""
    try:
        scanner = GroupScanner()
        report = scanner.generate_group_report(group_id, days=30)
        
        if 'error' in report:
            return jsonify({'error': report['error']}), 404
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error generating group report: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500

@app.route('/admin/analytics')
@require_admin_key  
def admin_analytics():
    """Advanced analytics dashboard"""
    try:
        stats = get_dashboard_stats()
        
        # Additional analytics data
        scanner = GroupScanner()
        
        analytics_data = {
            'basic_stats': stats,
            'threat_trends': [],
            'top_threat_groups': [],
            'payment_summary': []
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        return jsonify({'error': 'Failed to fetch analytics'}), 500

# Admin payment commands
@app.route('/admin/payments/pending')
@require_admin_key
def admin_pending_payments():
    """Get pending payments for admin review"""
    try:
        pv = PaymentVerification()
        pending_payments = pv.get_pending_payments()
        
        return jsonify({
            'success': True,
            'payments': pending_payments
        })
        
    except Exception as e:
        logger.error(f"Error fetching pending payments: {e}")
        return jsonify({'error': 'Failed to fetch pending payments'}), 500

@app.route('/admin/payments/<int:payment_id>/approve', methods=['POST'])
@require_admin_key
def admin_approve_payment(payment_id):
    """Approve payment"""
    try:
        pv = PaymentVerification()
        success = pv.approve_payment(payment_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Payment approved'})
        else:
            return jsonify({'error': 'Failed to approve payment'}), 400
            
    except Exception as e:
        logger.error(f"Error approving payment: {e}")
        return jsonify({'error': 'Failed to approve payment'}), 500

@app.route('/admin/payments/<int:payment_id>/reject', methods=['POST'])
@require_admin_key
def admin_reject_payment(payment_id):
    """Reject payment"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        pv = PaymentVerification()
        success = pv.reject_payment(payment_id, reason)
        
        if success:
            return jsonify({'success': True, 'message': 'Payment rejected'})
        else:
            return jsonify({'error': 'Failed to reject payment'}), 400
            
    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        return jsonify({'error': 'Failed to reject payment'}), 500

@app.route('/paypal/checkout/<int:payment_id>')
def paypal_checkout(payment_id):
    """PayPal checkout page - creates PayPal order and redirects"""
    try:
        from paypal_integration import PayPalIntegration
        
        # Get payment record
        payment = Payment.query.get(payment_id)
        if not payment:
            return render_template('paypal_error.html', 
                                 error='Payment record not found'), 404
        
        if payment.status != 'pending':
            return render_template('paypal_error.html', 
                                 error='Payment already processed'), 400
        
        # Initialize PayPal integration
        paypal = PayPalIntegration()
        
        # Create PayPal order
        base_url = request.url_root.rstrip('/')
        success_url = f"{base_url}/paypal/success/{payment_id}"
        cancel_url = f"{base_url}/paypal/cancel/{payment_id}"
        
        description = f"Security Bot Credits - {payment.purchase_type}"
        
        order_result = paypal.create_payment_order(
            payment_id=payment.id,
            amount=payment.amount_usd,
            description=description,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if order_result.get('success'):
            # Store PayPal order ID
            payment.transaction_id = order_result['order_id']
            db.session.commit()
            
            # Redirect to PayPal approval URL
            return redirect(order_result['approval_url'])
        else:
            return render_template('paypal_error.html', 
                                 error=order_result.get('error', 'PayPal order creation failed'))
            
    except Exception as e:
        logger.error(f"PayPal checkout error: {e}")
        return render_template('paypal_error.html', error=str(e))

@app.route('/paypal/success/<int:payment_id>')
def paypal_success(payment_id):
    """PayPal payment success callback"""
    try:
        from paypal_integration import process_paypal_payment_success
        
        # Get PayPal order ID from query params
        order_id = request.args.get('token')  # PayPal returns order ID as 'token'
        
        if not order_id:
            return render_template('paypal_error.html', 
                                 error='Missing PayPal order ID'), 400
        
        # Process the payment
        result = process_paypal_payment_success(payment_id, order_id)
        
        if result.get('success'):
            return render_template('paypal_success.html', 
                                 payment_id=payment_id,
                                 credits_added=result.get('credits_added'),
                                 transaction_id=result.get('transaction_id'),
                                 message=result.get('message'))
        else:
            return render_template('paypal_error.html', 
                                 error=result.get('error', 'Payment processing failed'))
            
    except Exception as e:
        logger.error(f"PayPal success processing error: {e}")
        return render_template('paypal_error.html', error=str(e))

@app.route('/paypal/cancel/<int:payment_id>')
def paypal_cancel(payment_id):
    """PayPal payment cancelled"""
    try:
        # Update payment status to cancelled
        payment = Payment.query.get(payment_id)
        if payment and payment.status == 'pending':
            payment.status = 'cancelled'
            db.session.commit()
        
        return render_template('paypal_cancel.html', payment_id=payment_id)
        
    except Exception as e:
        logger.error(f"PayPal cancel error: {e}")
        return render_template('paypal_cancel.html', payment_id=payment_id, error=str(e))
        
        # Update payment status
        payment.status = 'confirmed'
        payment.confirmed_at = datetime.now(timezone.utc)
        
        # Add credits to user
        user = User.query.get(payment.user_id)
        if user and payment.purchase_type.endswith('_credits'):
            user.add_credits(payment.quantity)
        
        db.session.commit()
        
        return render_template('paypal_success.html', 
                             payment=payment,
                             user=user)
        
    except Exception as e:
        logger.error(f"PayPal success error: {e}")
        return render_template('paypal_error.html', 
                             error='Error processing successful payment')

    return dict(moment=moment)

logger.info("Routes registered successfully")
