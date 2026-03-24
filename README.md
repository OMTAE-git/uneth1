# uneth1 - ADA Compliance Suite

Automated ADA compliance checking, demand letter generation, and monitoring system for e-commerce websites.

## Features

- **Web Scraping & Compliance Checks**: Scan websites for ADA accessibility issues (alt text, keyboard navigation, color contrast, screen reader compatibility)
- **Automated Letter Generation**: Generate customized demand letters for non-compliant websites
- **Compliance Monitoring**: Track compliance status over time with scheduled checks
- **Detailed Reporting**: Generate comprehensive HTML/PDF reports

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Check a Website for ADA Compliance

```bash
python cli.py check --url https://example.com
python cli.py check --url https://example.com --json  # JSON output
python cli.py check --url https://example.com --verbose  # Detailed issues
```

### Generate a Demand Letter

```bash
python cli.py letter \
  --recipient "Business Name" \
  --email "contact@example.com" \
  --website "https://example.com" \
  --check-url "https://example.com" \
  --sender "Your Name" \
  --organization "Your Organization"
```

### Monitor Websites

```bash
# Add a site to monitoring
python cli.py monitor --add --url https://example.com --name "Example" --email "contact@example.com"

# Check all monitored sites
python cli.py monitor --check-all

# View monitoring status
python cli.py monitor --status
```

### Generate Reports

```bash
# Single site summary report
python cli.py report --type summary --url https://example.com

# Progress report
python cli.py report --type progress --url https://example.com --days 30

# Batch report
python cli.py report --type batch --urls https://site1.com https://site2.com
```

## WCAG Criteria Checked

| Criterion | Description |
|-----------|-------------|
| 1.1.1 | Non-text Content - Images must have alt text |
| 1.3.1 | Info and Relationships - Proper heading structure |
| 1.4.3 | Contrast (Minimum) - 4.5:1 contrast ratio |
| 2.1.1 | Keyboard - All functionality accessible via keyboard |
| 2.4.1 | Bypass Blocks - Skip navigation links |
| 2.4.2 | Page Titled - Descriptive page titles |
| 2.4.4 | Link Purpose - Descriptive link text |
| 2.4.7 | Focus Visible - Visible keyboard focus |

## Project Structure

```
uneth1/
├── src/
│   ├── scrapers/          # Web scraping and compliance checking
│   ├── letters/           # Letter generation
│   ├── monitoring/        # Compliance monitoring
│   ├── reports/           # Report generation
│   └── utils/             # Utilities
├── templates/             # Email/letter templates
├── config/               # Configuration files
├── data/                 # Database and data storage
├── output/               # Generated reports and letters
├── tests/                # Unit tests
├── cli.py                # Main CLI
└── requirements.txt      # Python dependencies
```

## Usage Examples

### Python API

```python
from src.scrapers.compliance_checker import ADAComplianceChecker
from src.letters.letter_generator import LetterGenerator
from src.monitoring.monitor import ComplianceMonitor

# Check a website
checker = ADAComplianceChecker('https://example.com')
checker.run_checks()
report = checker.get_report()
print(f"Found {report['total_issues']} issues")

# Generate a letter
letter_gen = LetterGenerator()
letter = letter_gen.generate_demand_letter(
    recipient_name="Business Name",
    recipient_email="contact@example.com",
    website_url="https://example.com",
    issues=report['issues']
)

# Add to monitoring
monitor = ComplianceMonitor()
monitor.add_site('https://example.com', 'Example Site', 'contact@example.com')
```

## Legal Disclaimer

This tool is provided for informational purposes only. It does not constitute legal advice. Users should consult with qualified legal counsel regarding ADA compliance requirements and any legal actions.

## License

MIT
