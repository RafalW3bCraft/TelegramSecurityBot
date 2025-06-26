import os
import re
import json
import logging
import hashlib
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from core import cache_get, cache_set, get_config

logger = logging.getLogger(__name__)

class ThreatIntelligence:
    """Threat intelligence service for URL scanning"""
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.virustotal_api_key = get_config('virustotal_api_key') or os.environ.get('VIRUSTOTAL_API_KEY')
        self.urlhaus_api_key = get_config('urlhaus_api_key') or os.environ.get('URLHAUS_API_KEY')
        
        # API endpoints - Updated to latest versions
        self.virustotal_url = "https://www.virustotal.com/vtapi/v2/url/report"
        self.virustotal_scan_url = "https://www.virustotal.com/vtapi/v2/url/scan"
        self.urlhaus_url = "https://urlhaus-api.abuse.ch/v1/url/"
        self.urlhaus_lookup_url = "https://urlhaus-api.abuse.ch/v1/host/"
        
        # Comprehensive malicious patterns for all threat types
        self.malicious_patterns = [
            # High-risk TLDs and suspicious domains
            r'\.tk$', r'\.ml$', r'\.ga$', r'\.cf$', r'\.pw$', r'\.top$', r'\.click$', r'\.download$', r'\.stream$',
            
            # Phishing patterns - Banking
            r'secure.*bank.*login', r'bank.*verify.*account', r'update.*bank.*info', r'banking.*security.*alert',
            r'account.*verification.*required', r'suspend.*bank.*account', r'confirm.*banking.*details',
            
            # Phishing patterns - PayPal
            r'paypal.*verify.*account', r'paypal.*suspend', r'paypal.*security', r'paypal.*limitation',
            r'paypal.*confirm.*identity', r'paypal.*unusual.*activity', r'paypal.*account.*review',
            
            # Phishing patterns - Amazon/E-commerce
            r'amazon.*suspend.*account', r'amazon.*verify.*payment', r'amazon.*security.*alert',
            r'amazon.*unusual.*activity', r'ebay.*suspend', r'shop.*verify.*account',
            
            # Phishing patterns - Apple/Google/Microsoft
            r'apple.*id.*suspend', r'icloud.*verify', r'google.*account.*suspend', r'gmail.*verify',
            r'microsoft.*account.*suspend', r'outlook.*verify', r'windows.*activation',
            
            # Cryptocurrency scams
            r'crypto.*giveaway', r'bitcoin.*doubler', r'eth.*airdrop', r'crypto.*investment',
            r'blockchain.*wallet.*verify', r'bitcoin.*generator', r'crypto.*mining.*pool',
            r'nft.*free.*mint', r'defi.*yield.*farm', r'token.*presale',
            
            # Romance/Dating scams
            r'dating.*verify', r'lonely.*hearts', r'romantic.*connection', r'sugar.*daddy',
            r'cam.*girl.*free', r'adult.*verify.*age',
            
            # Tech support scams
            r'computer.*virus.*detected', r'windows.*defender.*alert', r'security.*warning.*urgent',
            r'tech.*support.*call', r'computer.*infected', r'malware.*detected',
            
            # Government/Tax scams
            r'irs.*refund', r'tax.*return.*update', r'government.*benefits', r'social.*security.*suspend',
            r'stimulus.*payment', r'tax.*debt.*relief',
            
            # Generic suspicious patterns
            r'urgent.*verify', r'account.*suspended', r'click.*here.*now', r'act.*immediately',
            r'limited.*time.*offer', r'congratulations.*winner', r'you.*have.*won',
            r'claim.*prize.*now', r'final.*notice', r'immediate.*action.*required',
            
            # Malware/Download patterns
            r'download.*codec', r'player.*update.*required', r'flash.*update', r'java.*update.*urgent',
            r'codec.*missing', r'video.*not.*available', r'install.*player',
            
            # URL shorteners with suspicious content
            r'(bit\.ly|tinyurl\.com|t\.co|short\.link|tiny\.cc)/[a-zA-Z0-9]*(phish|scam|hack|virus|malware)',
            
            # Typosquatting major sites
            r'goog1e\.com', r'facebok\.com', r'amaz0n\.com', r'paypa1\.com', r'microsooft\.com',
            r'app1e\.com', r'yah00\.com', r'youtub3\.com', r'twitt3r\.com', r'1nstagram\.com',
            
            # Suspicious subdomain patterns
            r'[a-z]+\.(com|net|org)\.tk', r'[a-z]+\.(secure|login|verify|account)\.',
            r'(secure|login|verify|update|confirm)-[a-z]+\.',
            
            # IP address URLs (often malicious)
            r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            
            # Suspicious file extensions in URLs
            r'\.(exe|scr|bat|com|pif|vbs|jar|zip)(\?|$)',
            
            # Base64 encoded suspicious content
            r'base64|data:.*base64',
            
            # Homograph attacks (mixed scripts)
            r'[а-я].*\.com', r'[α-ω].*\.com'  # Cyrillic/Greek in Latin domains
        ]
        
        # Known safe domains (whitelist)
        self.safe_domains = {
            'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
            'instagram.com', 'linkedin.com', 'github.com', 'stackoverflow.com',
            'wikipedia.org', 'reddit.com', 'amazon.com', 'microsoft.com',
            'apple.com', 'netflix.com', 'discord.com', 'telegram.org'
        }
        
        # Known malicious domains and IPs
        self.known_malicious_domains = {
            # Google Safe Browsing test sites
            'malware.testing.google.test',
            'testsafebrowsing.appspot.com',
            'ianfette.org',
            
            # Known malware domains
            '027.ru', 'malwaredomainlist.com', 'urlvoid.com',
            
            # Common phishing domains
            'secure-update.tk', 'account-verify.ml', 'login-secure.ga',
            'paypal-verify.cf', 'amazon-suspend.pw',
            
            # Cryptocurrency scam domains
            'bitcoin-generator.top', 'crypto-doubler.click', 'eth-airdrop.stream'
        }
        
        # Suspicious IP ranges (simplified for demo)
        self.suspicious_ip_ranges = [
            '185.220.',  # Known Tor exit nodes range
            '192.42.',   # Some malicious ranges
            '198.96.'    # Example suspicious range
        ]
        
        # Known good URL shorteners
        self.trusted_shorteners = {
            'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'short.link',
            'tiny.cc', 'ow.ly', 'buff.ly', 'is.gd'
        }
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
            
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {e}")
            return url
    
    def check_pattern_match(self, url, domain):
        """Enhanced pattern matching for comprehensive threat detection"""
        try:
            url_lower = url.lower()
            domain_lower = domain.lower()
            matches = []
            
            for pattern in self.malicious_patterns:
                if re.search(pattern, url_lower) or re.search(pattern, domain_lower):
                    matches.append(pattern)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error checking patterns for {url}: {e}")
            return []

    def check_suspicious_ip(self, url):
        """Check if URL uses suspicious IP addresses"""
        try:
            import ipaddress
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            host = parsed.hostname
            
            # Check if host is an IP address
            try:
                ip = ipaddress.ip_address(host)
                # Check against suspicious ranges
                for suspicious_range in self.suspicious_ip_ranges:
                    if str(ip).startswith(suspicious_range):
                        return True
                        
                # Private IPs are suspicious in public URLs
                if ip.is_private:
                    return True
                    
            except (ValueError, TypeError):
                # Not an IP address, continue with domain checks
                pass
                
            return False
            
        except Exception as e:
            logger.debug(f"IP check error for {url}: {e}")
            return False

    def check_url_shortener(self, url, domain):
        """Check if URL uses suspicious shorteners"""
        try:
            # Extract base domain without subdomains
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                base_domain = '.'.join(domain_parts[-2:])
                
                if base_domain in self.trusted_shorteners:
                    # Even trusted shorteners can be suspicious with certain patterns
                    if any(suspicious in url.lower() for suspicious in ['phish', 'scam', 'hack', 'virus']):
                        return 'suspicious_shortener'
                    return 'trusted_shortener'
                    
                # Check for suspicious shortener-like domains
                if len(base_domain) <= 6 and any(tld in base_domain for tld in ['.tk', '.ml', '.ga', '.cf']):
                    return 'suspicious_shortener'
                    
            return None
            
        except Exception as e:
            logger.debug(f"Shortener check error for {url}: {e}")
            return None

    def check_homograph_attack(self, domain):
        """Check for homograph/IDN attacks"""
        try:
            # Check for mixed scripts (suspicious)
            latin_chars = re.findall(r'[a-zA-Z]', domain)
            cyrillic_chars = re.findall(r'[а-яА-Я]', domain)
            greek_chars = re.findall(r'[α-ωΑ-Ω]', domain)
            
            script_count = sum([bool(latin_chars), bool(cyrillic_chars), bool(greek_chars)])
            
            if script_count > 1:
                return True
                
            # Check for suspicious Unicode characters
            if any(ord(char) > 127 for char in domain):
                try:
                    # Try to encode as ASCII - will fail for Unicode
                    domain.encode('ascii')
                except UnicodeEncodeError:
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug(f"Homograph check error for {domain}: {e}")
            return False
    
    def scan_url(self, url: str) -> Dict[str, Any]:
        """
        Enhanced comprehensive URL threat analysis with detailed reporting
        
        Returns:
            Dict containing detailed analysis results including VirusTotal and URLhaus data
        """
        try:
            logger.info(f"Enhanced scanning URL: {url}")
            
            # Parse domain from URL
            domain = self.extract_domain(url)
            if not domain:
                return {
                    'classification': 'error',
                    'confidence': 0.0,
                    'risk_score': 0,
                    'threat_sources': [],
                    'malware_families': [],
                    'threat_types': [],
                    'error': 'Invalid URL format'
                }
            
            # Check whitelist first
            from models import is_domain_whitelisted
            if is_domain_whitelisted(domain):
                logger.info(f"Domain {domain} is whitelisted")
                return {
                    'classification': 'clean',
                    'confidence': 100.0,
                    'risk_score': 0,
                    'threat_sources': ['Whitelist'],
                    'malware_families': [],
                    'threat_types': [],
                    'detection_ratio': '0/0',
                    'details': 'Domain is in trusted whitelist'
                }
            
            # Initialize comprehensive analysis
            threat_sources = []
            malware_families = []
            threat_types = []
            risk_factors = []
            total_risk_score = 0
            detection_engines = 0
            positive_detections = 0
            
            # VirusTotal Analysis
            vt_result = self.scan_with_virustotal(url)
            if vt_result and vt_result.get('positives', 0) > 0:
                detection_engines = vt_result.get('total', 0)
                positive_detections = vt_result.get('positives', 0)
                
                if positive_detections > 0:
                    threat_sources.append('VirusTotal')
                    risk_factors.append(f"{positive_detections}/{detection_engines} AV engines")
                    
                    # Calculate risk based on detection ratio
                    detection_ratio = positive_detections / detection_engines if detection_engines > 0 else 0
                    if detection_ratio >= 0.3:  # 30% or more engines detected
                        total_risk_score += 85
                        threat_types.append('Malware')
                    elif detection_ratio >= 0.15:  # 15-30% engines detected
                        total_risk_score += 60
                        threat_types.append('Suspicious')
                    elif detection_ratio >= 0.05:  # 5-15% engines detected
                        total_risk_score += 35
                        threat_types.append('Low-Risk')
            
            # URLhaus Analysis
            urlhaus_result = self.scan_with_urlhaus(url)
            if urlhaus_result and urlhaus_result.get('threat'):
                threat_sources.append('URLhaus')
                threat_info = urlhaus_result.get('threat', 'malware')
                threat_types.append(threat_info.title())
                risk_factors.append(f"URLhaus: {threat_info}")
                total_risk_score += 90
                
                # Extract malware families from URLhaus payloads
                malware_payloads = urlhaus_result.get('malware', [])
                for payload in malware_payloads[:3]:  # Limit to first 3
                    if isinstance(payload, dict) and 'malware_family' in payload:
                        family = payload['malware_family'].lower()
                        if family not in malware_families:
                            malware_families.append(family)
            
            # Enhanced Pattern Analysis
            pattern_matches = self.check_pattern_match(url, domain)
            if pattern_matches:
                threat_sources.append('Pattern Analysis')
                pattern_risk = len(pattern_matches) * 15  # 15 points per pattern match
                
                for pattern in pattern_matches[:5]:  # Limit to first 5 patterns
                    if any(term in pattern for term in ['phish', 'bank', 'paypal', 'amazon']):
                        threat_types.append('Phishing')
                    elif any(term in pattern for term in ['malware', 'virus', 'trojan']):
                        threat_types.append('Malware')
                    elif any(term in pattern for term in ['scam', 'crypto', 'investment']):
                        threat_types.append('Scam')
                    elif any(term in pattern for term in ['tk$', 'ml$', 'ga$', 'cf$']):
                        threat_types.append('Suspicious TLD')
                
                risk_factors.extend([f"Pattern: {p}" for p in pattern_matches[:3]])
                total_risk_score += min(pattern_risk, 60)  # Cap pattern risk at 60
            
            # Advanced Threat Classification with Industry Standards
            confidence = 0.0
            classification = 'clean'
            
            # Critical threats (immediate blocking recommended)
            if total_risk_score >= 85 or positive_detections >= 5:
                classification = 'malicious'
                confidence = min(95.0, 70.0 + (total_risk_score * 0.3))
            # High-risk threats (caution advised)
            elif total_risk_score >= 45 or positive_detections >= 2:
                classification = 'suspicious'
                confidence = min(85.0, 55.0 + (total_risk_score * 0.4))
            # Clean URLs
            else:
                classification = 'clean'
                confidence = max(88.0, 100.0 - (total_risk_score * 0.5))
            
            # Remove duplicates and clean up lists
            threat_sources = list(dict.fromkeys(threat_sources))  # Preserve order
            malware_families = list(dict.fromkeys(malware_families))
            threat_types = list(dict.fromkeys(threat_types))
            
            result = {
                'classification': classification,
                'confidence': round(confidence, 1),
                'risk_score': min(total_risk_score, 100),
                'threat_sources': threat_sources,
                'malware_families': malware_families,
                'threat_types': threat_types,
                'detection_ratio': f"{positive_detections}/{detection_engines}" if detection_engines > 0 else "0/0",
                'risk_factors': risk_factors,
                'domain': domain,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Enhanced URL scan complete: {url} -> {classification} ({confidence:.1f}%, risk: {total_risk_score})")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced scan error for URL {url}: {e}")
            return {
                'classification': 'error',
                'confidence': 0.0,
                'risk_score': 0,
                'threat_sources': [],
                'malware_families': [],
                'threat_types': [],
                'detection_ratio': '0/0',
                'error': str(e)
            }

    def scan_with_virustotal(self, url):
        """Scan URL with VirusTotal - Enhanced with submission if not found"""
        try:
            if not self.virustotal_api_key:
                return None
            
            # First, try to get existing report
            params = {
                'apikey': self.virustotal_api_key,
                'resource': url
            }
            
            response = requests.get(self.virustotal_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # If URL exists in database
            if data.get('response_code') == 1:
                positives = data.get('positives', 0)
                total = data.get('total', 1)
                
                return {
                    'source': 'virustotal',
                    'positives': positives,
                    'total': total,
                    'ratio': positives / total if total > 0 else 0,
                    'permalink': data.get('permalink', ''),
                    'scan_date': data.get('scan_date', '')
                }
            
            # If URL not found (response_code 0), submit for scanning
            elif data.get('response_code') == 0:
                logger.info(f"URL not in VirusTotal database, submitting for scan: {url}")
                
                # Submit URL for scanning
                scan_params = {
                    'apikey': self.virustotal_api_key,
                    'url': url
                }
                
                scan_response = requests.post(self.virustotal_scan_url, data=scan_params, timeout=10)
                scan_response.raise_for_status()
                scan_data = scan_response.json()
                
                if scan_data.get('response_code') == 1:
                    # Return minimal result indicating submission
                    return {
                        'source': 'virustotal',
                        'positives': 0,
                        'total': 1,
                        'ratio': 0.0,
                        'permalink': scan_data.get('permalink', ''),
                        'scan_date': 'submitted',
                        'status': 'submitted_for_scanning'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"VirusTotal scan error for {url}: {e}")
            return None
    
    def scan_with_urlhaus(self, url):
        """Scan URL with URLhaus - Enhanced with host lookup"""
        try:
            # First try direct URL lookup
            data = {'url': url}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            response = requests.post(self.urlhaus_url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('query_status') == 'ok':
                threat_level = result.get('threat', 'unknown')
                
                return {
                    'source': 'urlhaus',
                    'threat': threat_level,
                    'malware': result.get('payloads', []),
                    'tags': result.get('tags', []),
                    'date_added': result.get('date_added', ''),
                    'lookup_type': 'url'
                }
            
            # If URL not found, try host lookup
            try:
                domain = self.extract_domain(url)
                if domain:
                    host_data = {'host': domain}
                    host_response = requests.post(self.urlhaus_lookup_url, data=host_data, headers=headers, timeout=10)
                    host_response.raise_for_status()
                    
                    host_result = host_response.json()
                    
                    if host_result.get('query_status') == 'ok':
                        urls = host_result.get('urls', [])
                        if urls:
                            # Host has malicious URLs
                            return {
                                'source': 'urlhaus',
                                'threat': 'malware_download',
                                'malware': [],
                                'tags': ['host_lookup'],
                                'date_added': urls[0].get('date_added', ''),
                                'lookup_type': 'host',
                                'host_urls_count': len(urls)
                            }
            except Exception as host_e:
                logger.debug(f"URLhaus host lookup failed for {domain}: {host_e}")
            
            return None
            
        except Exception as e:
            logger.error(f"URLhaus scan error for {url}: {e}")
            return None
    
    def analyze_results(self, url, vt_result, uh_result, pattern_matches):
        """Analyze all scan results and determine classification"""
        try:
            score = 0
            sources = []
            confidence = 0.0
            
            # Check whitelist first
            domain = self.extract_domain(url)
            if domain in self.safe_domains:
                return {
                    'classification': 'clean',
                    'confidence': 0.95,
                    'threat_level': 'none',
                    'threat_categories': [],
                    'sources': ['whitelist'],
                    'score': 0,
                    'details': 'Domain is in trusted whitelist'
                }
            
            # Check known malicious domains
            if domain in self.known_malicious_domains:
                return {
                    'classification': 'malicious',
                    'confidence': 0.90,
                    'threat_level': 'critical',
                    'threat_categories': ['known_malicious'],
                    'sources': ['known_malicious'],
                    'score': 90,
                    'details': 'Domain is in known malicious list'
                }
            
            # Enhanced pattern matching analysis
            pattern_matches = self.check_pattern_match(url, domain)
            if pattern_matches:
                pattern_score = len(pattern_matches) * 15  # More patterns = higher score
                score += min(pattern_score, 60)  # Cap at 60 points
                sources.append('pattern_matching')
            
            # Additional threat checks
            if self.check_suspicious_ip(url):
                score += 50
                sources.append('suspicious_ip')
            
            shortener_check = self.check_url_shortener(url, domain)
            if shortener_check == 'suspicious_shortener':
                score += 30
                sources.append('suspicious_shortener')
            elif shortener_check == 'trusted_shortener':
                score -= 10  # Slightly reduce suspicion for trusted shorteners
            
            if self.check_homograph_attack(domain):
                score += 45
                sources.append('homograph_attack')
            
            # VirusTotal analysis
            if vt_result:
                sources.append('virustotal')
                ratio = vt_result.get('ratio', 0)
                
                if ratio > 0.1:  # More than 10% detection
                    score += min(50, ratio * 100)
                elif ratio > 0.05:  # 5-10% detection
                    score += 25
            
            # URLhaus analysis
            if uh_result:
                sources.append('urlhaus')
                threat = uh_result.get('threat', '').lower()
                
                if threat in ['malware_download', 'botnet_cc']:
                    score += 60
                elif threat in ['phishing', 'exploit_kit']:
                    score += 50
                elif threat == 'suspicious':
                    score += 30
            
            # Enhanced threat classification with detailed categories
            if score >= 80:
                classification = 'malicious'
                confidence = min(0.95, 0.75 + (score - 80) / 100)
                threat_level = 'critical'
            elif score >= 60:
                classification = 'malicious' 
                confidence = min(0.90, 0.60 + (score - 60) / 100)
                threat_level = 'high'
            elif score >= 40:
                classification = 'suspicious'
                confidence = min(0.80, 0.40 + (score - 40) / 100)
                threat_level = 'medium'
            elif score >= 20:
                classification = 'questionable'
                confidence = min(0.65, 0.20 + (score - 20) / 100)
                threat_level = 'low'
            else:
                classification = 'clean'
                confidence = max(0.60, 1.0 - (score / 100))
                threat_level = 'none'
            
            # Determine threat categories based on sources and patterns
            threat_categories = []
            
            # Check pattern matches for threat types
            pattern_str = ' '.join(pattern_matches) if isinstance(pattern_matches, list) else str(pattern_matches)
            
            if 'phish' in pattern_str.lower() or any('verify' in p or 'login' in p for p in pattern_matches if isinstance(pattern_matches, list)):
                threat_categories.append('phishing')
            if 'crypto' in pattern_str.lower() or 'bitcoin' in pattern_str.lower():
                threat_categories.append('cryptocurrency_scam')
            if 'malware' in str(sources).lower() or 'virus' in str(sources).lower():
                threat_categories.append('malware')
            if 'suspicious_ip' in sources:
                threat_categories.append('suspicious_infrastructure')
            if 'homograph_attack' in sources:
                threat_categories.append('typosquatting')
            if uh_result and 'botnet' in str(uh_result.get('threat', '')).lower():
                threat_categories.append('botnet')
            if any('tech.*support' in p or 'windows.*defender' in p for p in pattern_matches if isinstance(pattern_matches, list)):
                threat_categories.append('tech_support_scam')
            if any('dating' in p or 'romantic' in p for p in pattern_matches if isinstance(pattern_matches, list)):
                threat_categories.append('romance_scam')
            
            return {
                'classification': classification,
                'confidence': confidence,
                'threat_level': threat_level,
                'threat_categories': threat_categories,
                'sources': sources,
                'score': score,
                'details': {
                    'virustotal': vt_result,
                    'urlhaus': uh_result,
                    'pattern_matches': pattern_matches,
                    'ip_check': self.check_suspicious_ip(url),
                    'shortener_check': shortener_check,
                    'homograph_check': self.check_homograph_attack(domain)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing results for {url}: {e}")
            return {
                'classification': 'unknown',
                'confidence': 0.0,
                'sources': ['error'],
                'details': str(e)
            }
    
    def scan_url(self, url):
        """Main URL scanning function"""
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Generate cache key
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_key = f"threat_scan:{url_hash}"
            
            # Check cache first
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for URL scan: {url}")
                return cached_result
            
            logger.info(f"Scanning URL: {url}")
            
            # Extract domain
            domain = self.extract_domain(url)
            
            # Run all checks
            pattern_matches = self.check_pattern_match(url, domain)
            vt_result = self.scan_with_virustotal(url)
            uh_result = self.scan_with_urlhaus(url)
            
            # Analyze results
            result = self.analyze_results(url, vt_result, uh_result, pattern_matches)
            
            # Cache result for 30 minutes
            cache_set(cache_key, result, ttl=1800)
            
            logger.info(f"URL scan complete: {url} -> {result['classification']} ({result['confidence']:.2%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning URL {url}: {e}")
            return {
                'classification': 'error',
                'confidence': 0.0,
                'sources': ['error'],
                'details': str(e)
            }
    
    def bulk_scan_urls(self, urls):
        """Scan multiple URLs"""
        try:
            results = {}
            
            for url in urls:
                try:
                    results[url] = self.scan_url(url)
                except Exception as e:
                    logger.error(f"Error in bulk scan for {url}: {e}")
                    results[url] = {
                        'classification': 'error',
                        'confidence': 0.0,
                        'sources': ['error'],
                        'details': str(e)
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk URL scan: {e}")
            return {}
    
    def get_threat_stats(self):
        """Get threat intelligence statistics"""
        try:
            from models import ScanLog
            from sqlalchemy import func
            
            # Get scan statistics
            total_scans = ScanLog.query.count()
            malicious_count = ScanLog.query.filter_by(scan_result='malicious').count()
            suspicious_count = ScanLog.query.filter_by(scan_result='suspicious').count()
            clean_count = ScanLog.query.filter_by(scan_result='clean').count()
            
            # Calculate percentages
            total = total_scans or 1  # Avoid division by zero
            
            return {
                'total_scans': total_scans,
                'malicious': {
                    'count': malicious_count,
                    'percentage': (malicious_count / total) * 100
                },
                'suspicious': {
                    'count': suspicious_count,
                    'percentage': (suspicious_count / total) * 100
                },
                'clean': {
                    'count': clean_count,
                    'percentage': (clean_count / total) * 100
                },
                'api_sources': {
                    'virustotal_enabled': bool(self.virustotal_api_key),
                    'urlhaus_enabled': bool(self.urlhaus_api_key)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting threat stats: {e}")
            return {
                'total_scans': 0,
                'malicious': {'count': 0, 'percentage': 0},
                'suspicious': {'count': 0, 'percentage': 0},
                'clean': {'count': 0, 'percentage': 0},
                'api_sources': {
                    'virustotal_enabled': False,
                    'urlhaus_enabled': False
                }
            }

# Create threat intelligence instance
threat_intelligence = ThreatIntelligence()

logger.info("Threat intelligence service initialized successfully")
