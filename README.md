# ADA Compliance Suite

Automated ADA compliance checking, demand letter generation, and monitoring system.

## Features

- **Web Scraping & Compliance Checks**: Scan websites for ADA accessibility issues
- **Automated Letter Generation**: Generate customized demand letters
- **Compliance Monitoring**: Track compliance status over time
- **Detailed Reporting**: Generate comprehensive HTML reports
- **Autonomous Mode**: Fully automated scanning and letter generation
- **Web Dashboard**: Production-ready Flask dashboard

## Quick Start

```bash
# Install dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Check a website
python cli.py check --url https://example.com

# Run automated engine
python cli.py autonomous --once --no-email
```

## CLI Commands

```bash
python cli.py check --url https://example.com
python cli.py check --url https://example.com --verbose --json
python cli.py monitor --add --url https://example.com --email you@example.com
python cli.py monitor --status
python cli.py letter --recipient "Business" --email "legal@biz.com" --website "https://biz.com"
python cli.py autonomous --once
python cli.py autonomous --interval 12  # Run every 12 hours
```

## Docker Deployment

```bash
# Configure environment
cp .env.example .env
# Edit .env with SMTP credentials

# Build and run
docker-compose up -d

# View dashboard
open http://localhost:5000

# View logs
docker-compose logs -f ada-autonomous
```

## Production Deployment

### Docker (Recommended)
```bash
docker-compose -f docker-compose.yml up -d
```

### Manual
```bash
pip install -r requirements.txt

# Terminal 1: Web dashboard
python src/web_dashboard.py

# Terminal 2: Background worker
python src/autonomous_engine.py --interval 24
```

## Testing

```bash
pytest tests/ -v --cov=src
flake8 src/ --count --select=E9,F63,F7,F82
```

## Configuration

Create `.env` or set environment variables:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=compliance@example.com
AUTO_SEND=true
CHECK_INTERVAL_HOURS=24
```

## Project Structure

```
uneth1/
├── cli.py                     # CLI interface
├── src/
│   ├── autonomous_engine.py   # Fully autonomous operation
│   ├── web_dashboard.py        # Flask web dashboard
│   ├── config.py               # Configuration classes
│   ├── scrapers/               # Web scraping
│   ├── letters/                # Letter generation
│   ├── monitoring/             # Compliance monitoring
│   └── reports/                # Report generation
├── tests/                     # Unit tests
├── templates/                 # Web templates
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## WCAG Criteria Checked

| Criterion | Description |
|-----------|-------------|
| 1.1.1 | Non-text Content - Alt text |
| 1.3.1 | Info and Relationships |
| 1.4.3 | Contrast (Minimum) 4.5:1 |
| 2.1.1 | Keyboard Accessible |
| 2.4.1 | Bypass Blocks |
| 2.4.2 | Page Titled |
| 2.4.4 | Link Purpose |
| 2.4.7 | Focus Visible |

## License

MIT
