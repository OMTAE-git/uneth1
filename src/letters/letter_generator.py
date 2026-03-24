"""
Letter Generator Module
Generates demand letters for ADA non-compliance
"""

import os
from datetime import datetime
from typing import Dict, List

from jinja2 import Template


class LetterGenerator:
    TEMPLATES_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
    )

    def __init__(self):
        self.demand_letter_template = self._load_template("demand_letter.html")

    def _load_template(self, template_name: str) -> str:
        template_path = os.path.join(self.TEMPLATES_DIR, template_name)
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                return f.read()
        return self._get_default_template()

    def _get_default_template(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <title>ADA Compliance Demand Letter</title>
    <style>
        body { font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 40px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; }
        .date { text-align: right; margin-bottom: 20px; }
        .recipient { margin-bottom: 30px; }
        .subject { font-weight: bold; text-decoration: underline; margin-bottom: 20px; }
        .issues-list { margin: 20px 0; }
        .issues-list li { margin: 10px 0; }
        .signature { margin-top: 40px; }
        .legal-notice { margin-top: 30px; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>DEMAND LETTER</h1>
        <p>Web Accessibility Compliance Notice</p>
    </div>

    <div class="date">{{ date }}</div>

    <div class="recipient">
        <strong>To:</strong><br>
        {{ recipient_name }}<br>
        {{ recipient_address }}<br>
        {{ recipient_email }}<br><br>
        <strong>Website:</strong> <a href="{{ website_url }}">{{ website_url }}</a>
    </div>

    <div class="subject">
        <strong>RE: Notice of Americans with Disabilities Act (ADA) Non-Compliance</strong>
    </div>

    <p>Dear {{ recipient_name }},</p>

    <p>Our organization has identified accessibility barriers on your website that may prevent individuals with disabilities from fully accessing your online services. This constitutes a violation of the Americans with Disabilities Act (ADA) and potentially Title III of the Civil Rights Act of 1990.</p>

    <p><strong>Identified Compliance Issues:</strong></p>
    <ul class="issues-list">
    {% for issue in issues %}
        <li>
            <strong>[{{ issue.severity }}]</strong> {{ issue.category }} - {{ issue.description }}<br>
            <small>WCAG Criterion: {{ issue.wcag_criterion }}</small>
        </li>
    {% endfor %}
    </ul>

    <p><strong>Required Actions:</strong></p>
    <ol>
        <li>Conduct a comprehensive accessibility audit within 14 days</li>
        <li>Remediate all identified issues within 30 days</li>
        <li>Implement ongoing monitoring to prevent future violations</li>
        <li>Provide documentation of compliance efforts upon request</li>
    </ol>

    <p>Failure to address these issues may result in legal action under Title III of the ADA, which provides for injunctive relief, attorney's fees, and compensatory damages.</p>

    <p>We encourage you to take immediate action to make your website accessible to all users, including those with disabilities. If you have questions or wish to discuss remediation options, please contact us within 14 days of this notice.</p>

    <div class="signature">
        <p>Sincerely,</p>
        <p><strong>{{ sender_name }}</strong><br>
        {{ sender_organization }}<br>
        Email: {{ sender_email }}<br>
        Phone: {{ sender_phone }}</p>
    </div>

    <div class="legal-notice">
        <p><strong>LEGAL NOTICE:</strong> This letter is provided for informational purposes only and does not constitute legal advice. Recipients are encouraged to consult with qualified legal counsel regarding ADA compliance requirements.</p>
    </div>
</body>
</html>"""

    def generate_demand_letter(
        self,
        recipient_name: str,
        recipient_email: str,
        recipient_address: str,
        website_url: str,
        issues: List[Dict],
        sender_name: str = "ADA Compliance Team",
        sender_organization: str = "Web Accessibility Services",
        sender_email: str = "compliance@example.com",
        sender_phone: str = "555-555-5555",
    ) -> str:
        template = Template(self.demand_letter_template)

        letter_html = template.render(
            date=datetime.now().strftime("%B %d, %Y"),
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            recipient_address=recipient_address,
            website_url=website_url,
            issues=issues,
            sender_name=sender_name,
            sender_organization=sender_organization,
            sender_email=sender_email,
            sender_phone=sender_phone,
        )

        return letter_html

    def generate_text_letter(
        self,
        recipient_name: str,
        recipient_email: str,
        website_url: str,
        issues: List[Dict],
        sender_name: str = "ADA Compliance Team",
        sender_organization: str = "Web Accessibility Services",
        sender_email: str = "compliance@example.com",
    ) -> str:
        letter_text = f"""
DEMAND LETTER - Web Accessibility Compliance Notice
{datetime.now().strftime("%B %d, %Y")}

To: {recipient_name}
Email: {recipient_email}
Website: {website_url}

RE: Notice of Americans with Disabilities Act (ADA) Non-Compliance

Dear {recipient_name},

Our organization has identified accessibility barriers on your website that may prevent individuals with disabilities from fully accessing your online services. This constitutes a violation of the Americans with Disabilities Act (ADA) and potentially Title III of the Civil Rights Act of 1990.

IDENTIFIED COMPLIANCE ISSUES:
{"-" * 50}
"""

        for i, issue in enumerate(issues, 1):
            letter_text += f"""
{i}. [{issue["severity"]}] {issue["category"]} - {issue["description"]}
   WCAG Criterion: {issue["wcag_criterion"]}
   Suggested Fix: {issue["suggestion"]}
"""

        letter_text += f"""
{"-" * 50}

REQUIRED ACTIONS:
1. Conduct a comprehensive accessibility audit within 14 days
2. Remediate all identified issues within 30 days
3. Implement ongoing monitoring to prevent future violations
4. Provide documentation of compliance efforts upon request

Failure to address these issues may result in legal action under Title III of the ADA, which provides for injunctive relief, attorney's fees, and compensatory damages.

Please contact us within 14 days to discuss remediation options.

Sincerely,
{sender_name}
{sender_organization}
{sender_email}
"""
        return letter_text

    def save_letter(self, content: str, filename: str, output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "output", "letters"
            )

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath
