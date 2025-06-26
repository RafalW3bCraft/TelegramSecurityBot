#!/usr/bin/env python3
"""
Enhanced group scanning functionality for comprehensive analysis
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from app import app, db
from models import ScanLog, TelegramGroup, User
from threat_intelligence import ThreatIntelligence

logger = logging.getLogger(__name__)

class GroupScanner:
    """Comprehensive group content analysis"""
    
    def __init__(self):
        self.ti = ThreatIntelligence()
        
        # Suspicious patterns to detect
        self.suspicious_patterns = [
            r'bit\.ly/\w+',  # Shortened URLs
            r'tinyurl\.com/\w+',
            r't\.co/\w+',
            r'goo\.gl/\w+',
            r'ow\.ly/\w+',
            r'is\.gd/\w+',
            r'buff\.ly/\w+',
            
            # Crypto scam patterns
            r'(?i)(free|give|giveaway).*(btc|bitcoin|eth|ethereum|crypto)',
            r'(?i)(double|multiply).*(bitcoin|btc|crypto)',
            r'(?i)(investment|profit|return).*(guaranteed|100%)',
            
            # Phishing patterns
            r'(?i)(verify|confirm|update).*(account|password|wallet)',
            r'(?i)(suspended|locked|blocked).*(account|wallet)',
            r'(?i)(urgent|immediate|asap).*(action|response)',
            
            # Malware patterns
            r'(?i)(download|install|update).*(urgent|required|now)',
            r'(?i)(click here|download now|install now)',
            r'\.(exe|bat|scr|pif|com|cmd)(\?|$)',
        ]
        
        # High-risk TLDs
        self.risky_tlds = [
            '.tk', '.ml', '.ga', '.cf', '.top', '.click', '.download',
            '.stream', '.science', '.work', '.party', '.accountant',
            '.loan', '.win', '.bid', '.racing', '.review', '.trade'
        ]
    
    def analyze_message_content(self, text: str) -> Dict[str, Any]:
        """Analyze message content for threats"""
        if not text:
            return {'risk_score': 0, 'patterns': [], 'urls': []}
        
        # Extract URLs
        urls = re.findall(r'http[s]?://\S+|www\.\S+', text)
        
        # Check for suspicious patterns
        detected_patterns = []
        risk_score = 0
        
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, text)
            if matches:
                detected_patterns.append({
                    'pattern': pattern,
                    'matches': matches,
                    'severity': 'high' if any(word in pattern.lower() for word in ['crypto', 'bitcoin', 'password']) else 'medium'
                })
                risk_score += 2 if 'high' in detected_patterns[-1]['severity'] else 1
        
        # Check URLs for risky TLDs
        for url in urls:
            for tld in self.risky_tlds:
                if tld in url.lower():
                    detected_patterns.append({
                        'pattern': f'risky_tld_{tld}',
                        'matches': [url],
                        'severity': 'medium'
                    })
                    risk_score += 1
                    break
        
        # Check for excessive caps or repetitive characters
        if len([c for c in text if c.isupper()]) > len(text) * 0.7:
            detected_patterns.append({
                'pattern': 'excessive_caps',
                'matches': ['EXCESSIVE CAPITALS'],
                'severity': 'low'
            })
            risk_score += 0.5
        
        return {
            'risk_score': min(risk_score, 10),  # Cap at 10
            'patterns': detected_patterns,
            'urls': urls,
            'text_length': len(text),
            'analysis_timestamp': datetime.now(timezone.utc)
        }
    
    def scan_urls_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scan multiple URLs efficiently"""
        results = []
        
        for url in urls[:10]:  # Limit to 10 URLs per batch
            try:
                scan_result = self.ti.scan_url(url)
                results.append({
                    'url': url,
                    'domain': self.ti.extract_domain(url),
                    'classification': scan_result['classification'],
                    'confidence': scan_result.get('confidence', 0),
                    'sources': scan_result.get('sources', []),
                    'scan_timestamp': datetime.now(timezone.utc)
                })
            except Exception as e:
                logger.error(f"Error scanning URL {url}: {e}")
                results.append({
                    'url': url,
                    'domain': self.ti.extract_domain(url),
                    'classification': 'error',
                    'confidence': 0,
                    'sources': [],
                    'error': str(e),
                    'scan_timestamp': datetime.now(timezone.utc)
                })
        
        return results

    def extract_urls_from_group(self, group_id: int, days: int = 3) -> List[str]:
        """Extract URLs from group messages in database"""
        try:
            from app import app as flask_app, db
            from models import ScanLog, TelegramGroup
            from datetime import datetime, timedelta, timezone
            import re
            
            with flask_app.app_context():
                # Get recent scan logs to find URLs that were posted
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=days)
                
                group = TelegramGroup.query.filter_by(group_id=group_id).first()
                if not group:
                    return []
                
                # Get recent scans from this group
                recent_scans = ScanLog.query.filter(
                    ScanLog.group_id == group.id,
                    ScanLog.date >= start_date,
                    ScanLog.scan_type.in_(['automatic', 'group_message'])
                ).order_by(ScanLog.date.desc()).limit(20).all()
                
                # Extract unique URLs
                urls = []
                seen_domains = set()
                
                for scan in recent_scans:
                    if scan.url and scan.domain:
                        # Avoid duplicate domains
                        if scan.domain not in seen_domains:
                            urls.append(scan.url)
                            seen_domains.add(scan.domain)
                
                # Return only real URLs from group message history
                # No fallback demo data - only authentic group content
                
                return urls[:10]  # Limit to 10 URLs max
                
        except Exception as e:
            logger.error(f"URL extraction error: {e}")
            return []
    
    def generate_group_report(self, group_id: int, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive group security report"""
        try:
            with app.app_context():
                # Get group info
                group = TelegramGroup.query.filter_by(group_id=group_id).first()
                if not group:
                    return {'error': 'Group not found'}
                
                # Get scan logs from last N days
                since_date = datetime.now(timezone.utc) - timedelta(days=days)
                scan_logs = ScanLog.query.filter(
                    ScanLog.group_id == group.id,
                    ScanLog.date >= since_date
                ).order_by(ScanLog.date.desc()).all()
                
                # Analyze threats
                total_scans = len(scan_logs)
                threats_found = len([log for log in scan_logs if log.scan_result in ['malicious', 'suspicious']])
                malicious_count = len([log for log in scan_logs if log.scan_result == 'malicious'])
                suspicious_count = len([log for log in scan_logs if log.scan_result == 'suspicious'])
                
                # Top threat domains
                threat_domains = {}
                for log in scan_logs:
                    if log.scan_result in ['malicious', 'suspicious']:
                        domain = log.domain
                        if domain not in threat_domains:
                            threat_domains[domain] = {'count': 0, 'classification': log.scan_result}
                        threat_domains[domain]['count'] += 1
                
                top_threats = sorted(threat_domains.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
                
                # Recent activity
                recent_activity = []
                for log in scan_logs[:10]:  # Last 10 scans
                    recent_activity.append({
                        'url': log.url,
                        'domain': log.domain,
                        'classification': log.scan_result,
                        'confidence': log.confidence_score or 0,
                        'timestamp': log.date,
                        'action': log.action_taken
                    })
                
                # Security score calculation
                if total_scans > 0:
                    threat_ratio = threats_found / total_scans
                    security_score = max(0, 100 - (threat_ratio * 100))
                else:
                    security_score = 100
                
                return {
                    'group_name': group.name,
                    'group_id': group_id,
                    'analysis_period': f'{days} days',
                    'total_scans': total_scans,
                    'threats_found': threats_found,
                    'malicious_count': malicious_count,
                    'suspicious_count': suspicious_count,
                    'clean_count': total_scans - threats_found,
                    'security_score': round(security_score, 1),
                    'top_threat_domains': top_threats,
                    'recent_activity': recent_activity,
                    'last_scan': scan_logs[0].date if scan_logs else None,
                    'protection_level': group.tier,
                    'generated_at': datetime.now(timezone.utc)
                }
                
        except Exception as e:
            logger.error(f"Error generating group report: {e}")
            return {'error': str(e)}
    
    def get_threat_summary(self, group_id: int) -> str:
        """Generate human-readable threat summary"""
        report = self.generate_group_report(group_id)
        
        if 'error' in report:
            return f"❌ Unable to generate report: {report['error']}"
        
        summary = f"🛡️ Security Report: {report['group_name']}\n\n"
        summary += f"📊 Analysis Period: {report['analysis_period']}\n"
        summary += f"🔍 Total Scans: {report['total_scans']}\n"
        summary += f"⚠️ Threats Found: {report['threats_found']}\n"
        summary += f"🚨 Malicious: {report['malicious_count']}\n"
        summary += f"⚡ Suspicious: {report['suspicious_count']}\n"
        summary += f"✅ Clean: {report['clean_count']}\n"
        summary += f"🏆 Security Score: {report['security_score']}/100\n\n"
        
        if report['top_threat_domains']:
            summary += "🎯 Top Threat Domains:\n"
            for domain, info in report['top_threat_domains']:
                summary += f"• {domain} ({info['count']} detections)\n"
            summary += "\n"
        
        if report['recent_activity']:
            summary += "📋 Recent Activity:\n"
            for activity in report['recent_activity'][:3]:
                emoji = "🚨" if activity['classification'] == 'malicious' else "⚠️" if activity['classification'] == 'suspicious' else "✅"
                summary += f"{emoji} {activity['domain']} - {activity['classification']}\n"
        
        return summary
    
    def check_group_permissions(self, bot, chat_id: int) -> Dict[str, bool]:
        """Check bot permissions in group"""
        try:
            bot_member = bot.get_chat_member(chat_id, bot.id)
            
            return {
                'can_delete_messages': bot_member.can_delete_messages or False,
                'can_read_all_messages': getattr(bot_member, 'can_read_all_group_messages', False),
                'can_restrict_members': bot_member.can_restrict_members or False,
                'is_admin': bot_member.status in ['administrator', 'creator']
            }
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            return {
                'can_delete_messages': False,
                'can_read_all_messages': False,
                'can_restrict_members': False,
                'is_admin': False
            }