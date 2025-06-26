# Security Bot Dashboard - Telegram Threat Detection System

## Overview

This is a comprehensive Telegram security bot that provides real-time URL scanning, threat detection, and group protection against malicious links, phishing attempts, and cyber threats. The system combines a Flask web dashboard with a Telegram bot that monitors groups and analyzes URLs using multiple threat intelligence sources.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

**Frontend**: Web dashboard built with Flask, Bootstrap, and custom cyberpunk-themed CSS for monitoring and administration
**Backend**: Python Flask application with SQLAlchemy ORM for data persistence
**Bot Integration**: Python Telegram Bot (PTB) for real-time group monitoring
**Threat Intelligence**: Multi-source threat detection using VirusTotal, URLhaus, and custom pattern matching
**Payment Processing**: Cryptocurrency and PayPal payment integration for subscription management

## Key Components

### Core Application (`app.py`)
- Flask application factory with SQLAlchemy integration
- PostgreSQL database configuration with SQLite fallback
- Security middleware initialization
- Proxy fix for deployment environments

### Telegram Bot (`bot_runner.py`)
- Consolidated bot functionality with command handlers
- Real-time message monitoring and URL extraction
- Integration with threat intelligence services
- User and group management

### Threat Intelligence (`threat_intelligence.py`)
- Multi-source threat detection (VirusTotal, URLhaus)
- 50+ malicious patterns for phishing, malware, and scam detection
- Risk scoring system (0-100 scale)
- Homograph attack and typosquatting detection

### Database Models (`models.py`)
- User model with subscription tracking and quota management
- TelegramGroup model with tier-based subscription system
- ScanLog model for audit trails and analytics
- Payment model for transaction tracking

### Payment System (`payment_processor.py`)
- Multi-currency support (BTC, TRX, USDT-TRC20, PayPal)
- QR code generation for crypto payments
- Real-time price fetching from CoinGecko
- Automatic payment verification

### Security Middleware (`security_middleware.py`)
- Rate limiting for API endpoints and general requests
- API key authentication for admin functions
- Security headers injection
- CORS handling for API endpoints

## Data Flow

1. **Message Processing**: Bot receives Telegram messages and extracts URLs
2. **Threat Analysis**: URLs are analyzed using multiple intelligence sources
3. **Risk Assessment**: Threat score calculated based on pattern matching and API responses
4. **Response Action**: Automatic blocking for high-threat content or user notification
5. **Logging**: All scans logged to database for analytics and audit trails
6. **Dashboard Updates**: Real-time statistics and monitoring through web interface

## External Dependencies

### Required APIs
- **Telegram Bot API**: Core bot functionality and message handling
- **VirusTotal API**: URL reputation and malware detection (optional but recommended)
- **URLhaus API**: Malware URL database lookup (optional)
- **CoinGecko API**: Cryptocurrency price data for payment processing
- **PayPal API**: Traditional payment processing

### Database
- **PostgreSQL**: Primary database (hosted on Neon)
- **SQLite**: Local fallback for development

### Infrastructure
- **Render**: Cloud hosting platform with Python 3.11 runtime
- **Neon Database**: Managed PostgreSQL service

## Deployment Strategy

The application is configured for cloud deployment with the following characteristics:

- **Multi-threaded Architecture**: Flask web server and Telegram bot run in separate threads
- **Environment Configuration**: Comprehensive environment variable management
- **Health Monitoring**: Built-in logging and error handling
- **Auto-scaling**: Rate limiting and resource management for high-traffic scenarios

### Key Configuration Files
- `.replit`: Platform-specific configuration with Python 3.11 and required packages
- `pyproject.toml`: Python dependencies and project metadata
- `.env`: Environment variables for API keys, database URLs, and configuration

### Security Considerations
- API key rotation and secure storage
- Rate limiting to prevent abuse
- Input sanitization and validation
- Secure session management
- HTTPS enforcement through proxy configuration

## Recent Changes

- June 25, 2025: **Complete Rebuild of /scan, /scan_all, and /subscribe Commands**
  - Rebuilt /scan command with comprehensive VirusTotal and URLhaus analysis
  - Enhanced /scan_all with industry-standard threat intelligence and auto-blocking
  - Upgraded /subscribe with professional payment processing and enhanced packages
  - Implemented detailed threat reporting with malware family identification
  - Added real-time progress tracking for all scanning operations
  - Enhanced security classification with 85+ risk threshold for malicious content
  - Integrated multi-source threat correlation (VirusTotal + URLhaus + Pattern Analysis)
  - All commands now provide authentic threat analysis using real security APIs

- June 25, 2025: **Comprehensive System Bug Fixes and URL Migration**
  - Updated all URL references from Replit to Render deployment
  - Fixed dashboard chart initialization conflicts with proper cleanup
  - Corrected payment processor return values for consistency
  - Resolved database integrity issues and foreign key constraints
  - Enhanced error handling across all components
  - System now fully operational with all components tested and verified

- June 25, 2025: **Enhanced Crypto Payment System with Real-time Verification**
  - Implemented webhook-based payment processing for BTC and USDT-TRC20
  - Added WebhookPaymentProcessor with BlockCypher and NowNodes API integration
  - Created comprehensive payment monitoring system with both webhook and polling verification
  - Enhanced /subscribe command with automatic payment detection and credit activation
  - Added payment status endpoints for real-time tracking
  - Integrated background payment monitoring service for comprehensive coverage
  - Users now get automatic credit activation upon blockchain confirmation

- June 25, 2025: **Fixed PayPal Configuration Issues**
  - Resolved PayPal authentication by switching from hardcoded to environment variables
  - Fixed sandbox/live mode configuration - now properly reads from .env
  - PayPal credentials now work correctly in sandbox mode for testing
  - Added PAYPAL_MODE environment variable for easy switching between sandbox/live
  - PayPal integration now ready for testing with current sandbox credentials

- June 25, 2025: **Completed PayPal Integration for /subscribe Command**
  - Implemented full PayPal checkout flow using credentials from .env
  - Added PayPal payment processing with automatic credit activation
  - Created PayPal integration module with order creation and capture
  - Updated payment templates with professional success/error/cancel pages
  - /subscribe command now supports both PayPal and crypto payments
  - Users can purchase credits with: /subscribe starter paypal

- June 25, 2025: **Removed All Demo Data - Real Data Only**
  - Eliminated all demo URLs, placeholder data, and synthetic content
  - Connected all systems to fetch authentic data from database sources
  - Enhanced real-time message processing with comprehensive URL scanning
  - Added real-time API endpoints for dashboard data
  - System now operates exclusively with genuine group activity data

- June 25, 2025: **Updated /scan_all to Use Real Group URLs**
  - Modified /scan_all to extract URLs from actual group message history
  - Removed demo URLs and now scans only URLs posted in the group
  - Enhanced URL extraction to get recent messages from database
  - Improved user experience by scanning real group content

- June 25, 2025: **Fixed Threat Level Logic in Scan Commands**
  - Corrected threat level calculation (clean=LOW, suspicious=MEDIUM, malicious=HIGH)
  - Fixed auto-blocking logic to only block malicious or high-confidence suspicious URLs
  - Updated confidence display to show detection confidence vs threat level
  - Improved threat classification accuracy and user messaging

- June 25, 2025: **Enhanced /scan_all Command with Auto-Blocking**
  - Implemented credit-based charging (1 credit per website scanned)
  - Added automatic blocking for threats with >70% confidence level
  - Connected blocked threats to THREATS BLOCKED dashboard counter
  - Updated admin dashboard for credit model with protection levels
  - Real-time progress updates during group scanning
  - Comprehensive threat reporting with detailed action logs

- June 25, 2025: **Credit-Based Subscription System Implementation**
  - Replaced monthly subscription plans with flexible credit packages
  - Added credit tracking fields to User model (scan_credits, total_credits_purchased, total_credits_used)
  - Updated payment processor to handle credit purchases instead of subscriptions
  - Modified bot commands (/subscribe, /stats, /pricing) to reflect credit system
  - Enhanced dashboard statistics to show credit usage metrics
  - Credit packages: Starter ($5/100 credits), Standard ($15/350 credits), Premium ($35/1000 credits), Enterprise ($75/3000 credits)

## Changelog

- June 25, 2025. Initial setup
- June 25, 2025. Migrated to credit-based subscription model

## User Preferences

Preferred communication style: Simple, everyday language.