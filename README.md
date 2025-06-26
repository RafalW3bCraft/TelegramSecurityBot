# G3r4kiSec - Comprehensive Telegram Threat Detection System

A powerful Telegram security bot that provides real-time URL scanning, threat detection, and group protection against malicious links, phishing attempts, and cyber threats.

---
# 🚀 Live Demo

Access the deployed G3r4kiSec Telegram Security Bot dashboard here:

[![Open Dashboard](https://img.shields.io/badge/OPEN%20DASHBOARD-Click%20Here-blue?style=for-the-badge&logo=telegram)](https://telegramsecuritybot-izqz.onrender.com)

🌐 **URL:** [https://telegramsecuritybot-izqz.onrender.com](https://telegramsecuritybot-izqz.onrender.com)

---

## 🛡️ Features

### Real-Time Threat Detection
- **Multi-Source Intelligence**: Integrates VirusTotal, URLhaus, and advanced pattern matching
- **Comprehensive Coverage**: Detects phishing, malware, crypto scams, typosquatting, and tech support scams
- **50+ Threat Patterns**: Banking phishing, PayPal scams, Amazon phishing, cryptocurrency fraud
- **IP-Based Detection**: Identifies suspicious IP addresses and infrastructure
- **Homograph Attack Detection**: Catches internationalized domain name attacks

### Advanced Classification System
- **Critical Threats** (80+ score): Immediate danger requiring instant action
- **High Threats** (60-79 score): Dangerous content with high confidence
- **Medium Threats** (40-59 score): Suspicious activity requiring attention
- **Low Threats** (20-39 score): Questionable content for review
- **Clean Content** (<20 score): Safe and verified URLs

### Telegram Integration
- **Automatic Scanning**: Real-time URL analysis in group messages
- **Instant Alerts**: Detailed threat notifications with confidence scores
- **Manual Scanning**: On-demand URL analysis with `/scan` command
- **Group Analysis**: Comprehensive security reports with `/scan_all`
- **Subscription Management**: Multi-tier payment system with crypto support

### Payment & Subscription System
- **Cryptocurrency Support**: Bitcoin (BTC), TRON (TRX), USDT-TRC20
- **Traditional Payments**: PayPal integration
- **Flexible Plans**: Individual scans, group subscriptions, enterprise tiers
- **Automatic Processing**: QR code generation and payment verification

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Telegram Bot Token
- VirusTotal API key (optional but recommended)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/RafalW3bCraft/TelegramSecurityBot.git
   cd G3r4kiSec
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Or, if using uv:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create a `.env` file with your configuration values:
   ```env
   # Telegram Bot Configuration
   BOT_TOKEN=your_telegram_bot_token_here

   # Database Configuration
   DATABASE_URL=postgresql://admin:admin@your_host:5432/secura?sslmode=require

   # PostgreSQL Environment Variables
   PGHOST=your_host
   PGPORT=5432
   PGUSER=admin
   PGPASSWORD=admin
   PGDATABASE=secura

   # API Keys (Optional but Recommended)
   VIRUSTOTAL_API_KEY=your_virustotal_api_key

   # Payment Configuration
   BTC_WALLET_ADDRESS=your_bitcoin_wallet_address
   TRX_WALLET_ADDRESS=your_tron_wallet_address
   USDT_WALLET_ADDRESS=your_usdt_trc20_wallet_address

   # Security Settings
   ADMIN_USER_IDS=123456789,987654321  # Comma-separated admin Telegram IDs
   API_KEY=your_api_key_for_dashboard
   SESSION_SECRET=your_session_secret_key
   ```
   **Important**: Never commit `.env` files to version control. The `.gitignore` file is configured to exclude all environment files.

4. **Database Setup**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Start the Application**
   ```bash
   python main.py
   ```

---

## 📖 Usage Guide

### Telegram Bot Commands

#### Basic Commands
- `/start` - Initialize bot and show welcome message
- `/help` - Display all available commands
- `/status` - Check your current scan quota and usage
- `/pricing` - View subscription plans and pricing

#### Scanning Commands
- `/scan <url>` - Manually scan a specific URL
  ```
  /scan https://suspicious-site.com
  ```
- `/scan_all` - Perform comprehensive group analysis (premium feature)

#### Subscription Commands
- `/subscribe` - View subscription options and payment methods
- Payment support for BTC, TRX, USDT, and PayPal

### Web Dashboard

Access the admin dashboard at `http://localhost:5000` (or your deployed URL):

#### Dashboard Features
- **Real-time Statistics**: Group counts, scan metrics, threat detection rates
- **Group Management**: View all monitored groups and their subscription status
- **Scan Analytics**: Detailed reports on threat detection and user activity
- **Payment Management**: Review and approve pending cryptocurrency payments
- **System Health**: Monitor API status and performance metrics

#### API Endpoints
- `GET /api/scan` - Manual URL scanning API
- `GET /api/user/{telegram_id}/stats` - User statistics
- `GET /api/system/health` - System health check
- `GET /api/stats/realtime` - Real-time dashboard statistics

---

## 🔧 Development

### Project Structure
```
G3r4kiSec/
├── app.py                   # Flask application initialization
├── main.py                  # Main entry point
├── bot_runner.py            # Telegram bot implementation
├── threat_intelligence.py   # URL scanning and analysis
├── payment_processor.py     # Payment handling
├── payment_monitor.py       # Payment monitoring and verification
├── payment_verification.py  # Payment verification logic
├── paypal_integration.py    # PayPal integration
├── webhook_payment_processor.py # Webhook payment handling
├── webhook_routes.py        # Webhook routes for payments
├── group_scanner.py         # Group scanning logic
├── core.py                  # Core utilities and logic
├── routes.py                # Web dashboard routes
├── models.py                # Database models
├── security_middleware.py   # Security and rate limiting
├── utils.py                 # Utility functions
├── static/                  # CSS, JS, and assets
│   ├── css/
│   │   └── cyberpunk.css
│   └── js/
│       └── dashboard.js
├── templates/               # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── index.html
│   ├── paypal_cancel.html
│   ├── paypal_checkout.html
│   ├── paypal_error.html
│   └── paypal_success.html
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Lock file for dependencies
├── LICENSE
├── README.md
├── .gitignore
└── replit.md                # Replit deployment instructions
```

### Adding New Features

1. **New Threat Detection Patterns**
   - Modify `threat_intelligence.py`
   - Add patterns to `malicious_patterns` list
   - Update threat categorization logic

2. **Payment Methods**
   - Extend `payment_processor.py`
   - Add new cryptocurrency or payment gateway
   - Update bot payment flow

3. **Bot Commands**
   - Add command handlers in `bot_runner.py`
   - Update help text and documentation
   - Test with different user scenarios

### Testing

Run comprehensive threat detection tests:
```bash
python -c "
from threat_intelligence import ThreatIntelligence
ti = ThreatIntelligence()

# Test various threat types
test_urls = [
    'https://secure-bank-login.tk/verify',
    'https://bitcoin-doubler.click/invest', 
    'http://192.168.1.100/malware.exe',
    'https://google.com'
]

for url in test_urls:
    result = ti.scan_url(url)
    print(f'{url}: {result[\"classification\"]} ({result[\"threat_level\"]})')
"
```

---

## 🏗️ Architecture

### System Components
- **Flask Web Application**: Admin dashboard and API endpoints
- **Telegram Bot**: Real-time message monitoring and user interaction
- **Threat Intelligence**: Multi-source URL analysis engine
- **Payment Processor**: Cryptocurrency and PayPal integration
- **Security Middleware**: Rate limiting and authentication

### Database Schema
- **Users**: Telegram user management and quota tracking
- **TelegramGroups**: Group subscriptions and monitoring
- **ScanLogs**: Complete audit trail of all scans performed
- **Payments**: Transaction history and payment verification
- **Whitelist**: Trusted domains and exceptions

### Security Features
- **Rate Limiting**: API and general request throttling
- **Authentication**: API key protection for sensitive endpoints
- **Input Validation**: Comprehensive URL and data sanitization
- **Audit Logging**: Complete activity tracking and monitoring

---

## 🚢 Deployment

### Production Environment
1. **Environment Variables**: Set all required environment variables
2. **Database**: Use PostgreSQL with connection pooling
3. **Process Manager**: Use Gunicorn with multiple workers
4. **Reverse Proxy**: Configure Nginx for SSL termination
5. **Monitoring**: Set up logging and health checks

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

### Replit Deployment
This project is optimized for Replit deployment:
1. Fork the repository
2. Set environment variables in Replit Secrets
3. Run the application - it will automatically start

---

## 📊 API Reference

### Scan URL Endpoint
```http
POST /api/scan
Content-Type: application/json

{
  "url": "https://example.com",
  "scan_type": "manual"
}
```

**Response:**
```json
{
  "classification": "suspicious",
  "confidence": 0.75,
  "threat_level": "medium",
  "threat_categories": ["phishing"],
  "sources": ["pattern_matching", "virustotal"],
  "score": 45,
  "details": {
    "virustotal": {...},
    "urlhaus": {...},
    "pattern_matches": [...]
  }
}
```

### User Statistics
```http
GET /api/user/{telegram_id}/stats
```

**Response:**
```json
{
  "user_id": 123456789,
  "individual_scans_remaining": 5,
  "group_scans_remaining": 1,
  "total_scans_performed": 25,
  "threats_detected": 3,
  "subscription_status": "active"
}
```

---

## 🛠️ Troubleshooting

### Common Issues

1. **Bot Not Responding**
   - Verify `BOT_TOKEN` is correct
   - Check bot permissions in target groups
   - Ensure bot is not already running elsewhere

2. **Database Connection Errors**
   - Verify `DATABASE_URL` format
   - Check PostgreSQL service status
   - Ensure database exists and permissions are correct

3. **API Rate Limiting**
   - VirusTotal: 4 requests/minute for free tier
   - URLhaus: No strict limits but be respectful
   - Implement caching for repeated scans

4. **Payment Processing Issues**
   - Verify wallet addresses are correct
   - Check PayPal credentials and sandbox/production mode
   - Monitor payment logs for transaction errors

### Performance Optimization

1. **Database Indexing**
   ```sql
   CREATE INDEX idx_scan_logs_date ON scan_logs(date);
   CREATE INDEX idx_users_telegram_id ON users(telegram_id);
   CREATE INDEX idx_groups_group_id ON telegram_groups(group_id);
   ```

2. **Caching**
   - Implement Redis for scan result caching
   - Cache threat intelligence results for 1 hour
   - Use in-memory cache for frequently accessed data

3. **Rate Limiting**
   - Adjust limits based on your API quotas
   - Implement exponential backoff for API calls
   - Use queuing for batch processing

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit with clear messages: `git commit -m "Add feature description"`
5. Push to your fork: `git push origin feature-name`
6. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where applicable
- Add docstrings for all functions
- Include error handling and logging

---

## 📝 License

MIT License

Copyright (c) 2025 RafalW3bCraft

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 📞 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check the wiki for detailed guides
- **Security**: Report security vulnerabilities privately to RafalW3bCraft
- **Community**: Join discussions in the project's GitHub Discussions

---

## 🔮 Roadmap

### Upcoming Features
- [ ] Machine learning threat detection
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Custom threat feeds integration
- [ ] API rate limiting dashboard
- [ ] Advanced user management
- [ ] Webhook notifications
- [ ] Threat intelligence sharing

### Version History
- **v1.0.0** - Initial release with comprehensive threat detection
- **v1.1.0** - Enhanced pattern matching and payment system
- **v1.2.0** - Advanced classification and threat categorization

---

**Built with ❤️ by RafalW3bCraft**

For more information, visit the [project repository](https://github.com/RafalW3bCraft/TelegramSecurityBot).