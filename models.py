from datetime import datetime, timezone
from sqlalchemy import func
from app import db

class User(db.Model):
    """Telegram user model with subscription tracking"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    
    # Credit-based quota tracking
    scan_credits = db.Column(db.Integer, default=5)  # Free starter credits
    total_credits_purchased = db.Column(db.Integer, default=0)
    total_credits_used = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    scan_logs = db.relationship('ScanLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.telegram_id}>'
    
    def add_credits(self, credits):
        """Add credits to user account"""
        self.scan_credits += credits
        self.total_credits_purchased += credits
        db.session.commit()
    
    def use_credit(self):
        """Use one credit for scanning"""
        if self.scan_credits > 0:
            self.scan_credits -= 1
            self.total_credits_used += 1
            db.session.commit()
            return True
        return False
    
    def get_credit_summary(self):
        """Get user credit summary"""
        return {
            'remaining': self.scan_credits,
            'purchased': self.total_credits_purchased,
            'used': self.total_credits_used
        }

class TelegramGroup(db.Model):
    """Telegram group/channel model with subscription tracking"""
    __tablename__ = 'telegram_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(50))  # group, supergroup, channel
    
    # Subscription details
    tier = db.Column(db.String(50), default='free')  # free, monthly, premium, enterprise
    active = db.Column(db.Boolean, default=True)
    subscription_expires = db.Column(db.DateTime)
    
    # Statistics
    total_scans_performed = db.Column(db.Integer, default=0)
    threats_blocked = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    scan_logs = db.relationship('ScanLog', backref='group', lazy='dynamic')
    
    def __repr__(self):
        return f'<TelegramGroup {self.group_id}>'

class Payment(db.Model):
    """Payment tracking for users"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Payment details
    payment_method = db.Column(db.String(50))  # crypto, telegram_payments
    cryptocurrency = db.Column(db.String(10))  # BTC, TRX, USDT
    amount_usd = db.Column(db.Float, nullable=False)
    amount_crypto = db.Column(db.Float)
    
    # Transaction details
    transaction_id = db.Column(db.String(255))
    wallet_address = db.Column(db.String(255))
    payment_address = db.Column(db.String(255))
    
    # Enhanced fields for webhook verification
    webhook_id = db.Column(db.String(255))  # Webhook registration ID
    monitoring_started = db.Column(db.Boolean, default=False)
    
    # Purchase details
    purchase_type = db.Column(db.String(50))  # individual_scans, group_scans
    quantity = db.Column(db.Integer)
    
    # Status tracking
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, failed
    confirmed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.amount_usd} USD>'

class ScanLog(db.Model):
    """Log of all URL scans performed"""
    __tablename__ = 'scan_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('telegram_groups.id'))
    
    # Scan details
    domain = db.Column(db.String(255), nullable=False)
    url = db.Column(db.Text, nullable=False)
    scan_type = db.Column(db.String(50))  # individual, group, manual, automatic, group_analysis
    
    # Results
    scan_result = db.Column(db.String(50))  # clean, suspicious, malicious
    threat_sources = db.Column(db.Text)  # JSON array of sources that flagged it
    confidence_score = db.Column(db.Float)
    
    # Response details
    action_taken = db.Column(db.String(100))  # warned, deleted, blocked
    message_deleted = db.Column(db.Boolean, default=False)
    
    # Timestamps
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<ScanLog {self.id}: {self.domain} - {self.scan_result}>'

class Whitelist(db.Model):
    """Whitelisted domains that bypass scanning"""
    __tablename__ = 'whitelist'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    added_by = db.Column(db.String(255))  # admin username
    reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Whitelist {self.domain}>'

class SystemConfig(db.Model):
    """System configuration and settings"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<SystemConfig {self.key}: {self.value}>'

# Helper functions for database operations
def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None):
    """Get existing user or create new one"""
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Update user info if provided
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.last_active = datetime.now(timezone.utc)
        db.session.commit()
    
    return user

def get_or_create_group(group_id, name=None, group_type=None):
    """Get existing group or create new one"""
    group = TelegramGroup.query.filter_by(group_id=group_id).first()
    if not group:
        group = TelegramGroup(
            group_id=group_id,
            name=name,
            type=group_type
        )
        db.session.add(group)
        db.session.commit()
    else:
        # Update group info if provided
        if name:
            group.name = name
        if group_type:
            group.type = group_type
        group.last_active = datetime.now(timezone.utc)
        db.session.commit()
    
    return group

def is_domain_whitelisted(domain):
    """Check if domain is whitelisted"""
    return Whitelist.query.filter_by(domain=domain).first() is not None

def get_dashboard_stats():
    """Get statistics for dashboard"""
    total_groups = TelegramGroup.query.count()
    active_groups = TelegramGroup.query.filter_by(active=True).count()
    total_scans = ScanLog.query.count()
    threats_blocked = ScanLog.query.filter(ScanLog.scan_result.in_(['suspicious', 'malicious'])).count()
    
    # Recent activity (last 24 hours)
    yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    recent_scans = ScanLog.query.filter(ScanLog.date >= yesterday).count()
    recent_threats = ScanLog.query.filter(
        ScanLog.date >= yesterday,
        ScanLog.scan_result.in_(['suspicious', 'malicious'])
    ).count()
    
    # Credit system stats
    total_users = User.query.count()
    total_credits_purchased = db.session.query(func.sum(User.total_credits_purchased)).scalar() or 0
    total_credits_used = db.session.query(func.sum(User.total_credits_used)).scalar() or 0
    active_credit_users = User.query.filter(User.scan_credits > 0).count()
    
    # Tier distribution (keeping for compatibility)
    tier_distribution = {'free': 0, 'monthly': 0, 'premium': 0, 'enterprise': 0}
    tiers = db.session.query(TelegramGroup.tier, func.count(TelegramGroup.id)).group_by(TelegramGroup.tier).all()
    for tier, count in tiers:
        tier_key = tier if tier else 'free'
        if tier_key in tier_distribution:
            tier_distribution[tier_key] = count
        else:
            tier_distribution['free'] += count
    
    # Payment statistics
    total_revenue = db.session.query(func.sum(Payment.amount_usd)).filter_by(status='confirmed').scalar() or 0
    monthly_revenue = db.session.query(func.sum(Payment.amount_usd)).filter(
        Payment.status == 'confirmed',
        Payment.confirmed_at >= datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ).scalar() or 0
    
    return {
        'total_groups': total_groups,
        'active_groups': active_groups,
        'total_scans': total_scans,
        'threats_blocked': threats_blocked,
        'recent_scans': recent_scans,
        'recent_threats': recent_threats,
        'total_users': total_users,
        'total_credits_purchased': total_credits_purchased,
        'total_credits_used': total_credits_used,
        'active_credit_users': active_credit_users,
        'tier_distribution': tier_distribution,
        'payment_stats': {
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue
        }
    }
