"""
Letter Generator Module
Generates professional demand letters for ADA non-compliance with proper error handling and logging.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from jinja2 import Template, TemplateError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LetterGenerator:
    """
    Generates demand letters for ADA non-compliance.

    Supports both HTML and plain text letter formats.
    """

    def __init__(self, templates_directory: Optional[str] = None) -> None:
        """
        Initialize the letter generator.

        Args:
            templates_directory: Optional custom templates directory path
        """
        if templates_directory:
            self.templates_dir = templates_directory
        else:
            current_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            self.templates_dir = os.path.join(current_dir, "templates")

        self.html_template_content: Optional[str] = None
        self._load_template_content()

        logger.info(
            f"Initialized LetterGenerator with templates from: {self.templates_dir}"
        )

    def _load_template_content(self) -> None:
        """Load the HTML template from file or use default."""
        try:
            template_path = os.path.join(self.templates_dir, "demand_letter.html")

            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as template_file:
                    self.html_template_content = template_file.read()
                logger.info(f"Loaded template from: {template_path}")
            else:
                self.html_template_content = self._get_default_html_template()
                logger.info("Using default HTML template")

        except IOError as e:
            logger.error(f"Failed to read template file: {e}")
            self.html_template_content = self._get_default_html_template()
        except Exception as e:
            logger.error(f"Unexpected error loading template: {e}")
            self.html_template_content = self._get_default_html_template()

    def _get_default_html_template(self) -> str:
        """
        Get the default HTML template for demand letters.

        Returns:
            Default HTML template string
        """
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ADA Compliance Demand Letter</title>
    <style>
        body { font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 40px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #333; padding-bottom: 20px; }
        .header h1 { margin: 0; color: #333; }
        .date { text-align: right; margin-bottom: 20px; }
        .recipient { margin-bottom: 30px; }
        .subject { font-weight: bold; text-decoration: underline; margin-bottom: 20px; }
        .issues-list { margin: 20px 0; padding-left: 20px; }
        .issues-list li { margin: 15px 0; padding: 10px; background: #f9f9f9; border-left: 3px solid #333; }
        .actions-list { margin: 20px 0; padding-left: 20px; }
        .actions-list li { margin: 10px 0; }
        .signature { margin-top: 40px; }
        .legal-notice { margin-top: 30px; padding: 15px; background: #f0f0f0; font-size: 0.9em; color: #666; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; font-weight: bold; }
        .badge.high { background: #e74c3c; color: white; }
        .badge.medium { background: #f39c12; color: white; }
        .badge.low { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>DEMAND LETTER</h1>
        <p>Web Accessibility Compliance Notice</p>
    </div>

    <div class="date">{{ current_date }}</div>

    <div class="recipient">
        <strong>To:</strong><br>
        {{ recipient_name }}<br>
        {{ recipient_address }}<br>
        Email: {{ recipient_email }}<br><br>
        <strong>Website:</strong> <a href="{{ website_url }}">{{ website_url }}</a>
    </div>

    <div class="subject">
        <strong>RE: Notice of Americans with Disabilities Act (ADA) Non-Compliance</strong>
    </div>

    <p>Dear {{ recipient_name }},</p>

    <p>Our organization has identified accessibility barriers on your website that may prevent individuals with disabilities from fully accessing your online services. This constitutes a potential violation of the Americans with Disabilities Act (ADA) and Title III of the Civil Rights Act of 1990.</p>

    <p><strong>Identified Compliance Issues:</strong></p>
    <ol class="issues-list">
    {% for issue in compliance_issues %}
        <li>
            <span class="badge {{ issue.severity|lower }}">{{ issue.severity }}</span>
            <strong>{{ issue.category }}</strong> - {{ issue.description }}<br>
            <small>WCAG Criterion: {{ issue.wcag_criterion }}</small>
        </li>
    {% endfor %}
    </ol>

    <p><strong>Required Actions:</strong></p>
    <ol class="actions-list">
        <li>Conduct a comprehensive accessibility audit within <strong>14 days</strong></li>
        <li>Remediate all identified issues within <strong>30 days</strong></li>
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

    def generate_html_letter(
        self,
        recipient_name: str,
        recipient_email: str,
        website_url: str,
        compliance_issues: List[Dict[str, str]],
        recipient_address: str = "Address on file",
        sender_name: str = "ADA Compliance Team",
        sender_organization: str = "Web Accessibility Services",
        sender_email: str = "compliance@example.com",
        sender_phone: str = "555-555-5555",
    ) -> str:
        """
        Generate an HTML demand letter.

        Args:
            recipient_name: Name of the recipient
            recipient_email: Email address of the recipient
            website_url: URL of the non-compliant website
            compliance_issues: List of compliance issues found
            recipient_address: Physical address of recipient
            sender_name: Name of the sender
            sender_organization: Organization name
            sender_email: Sender's email
            sender_phone: Sender's phone number

        Returns:
            HTML string of the generated letter
        """
        try:
            logger.info(f"Generating HTML letter for: {recipient_name} ({website_url})")

            template = Template(self.html_template_content)

            letter_html = template.render(
                current_date=datetime.now().strftime("%B %d, %Y"),
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                recipient_address=recipient_address,
                website_url=website_url,
                compliance_issues=compliance_issues,
                sender_name=sender_name,
                sender_organization=sender_organization,
                sender_email=sender_email,
                sender_phone=sender_phone,
            )

            logger.info(
                f"Successfully generated HTML letter with {len(compliance_issues)} issues"
            )
            return letter_html

        except TemplateError as e:
            logger.error(f"Template error while generating letter: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating HTML letter: {e}")
            raise

    def generate_text_letter(
        self,
        recipient_name: str,
        recipient_email: str,
        website_url: str,
        compliance_issues: List[Dict[str, str]],
        sender_name: str = "ADA Compliance Team",
        sender_organization: str = "Web Accessibility Services",
        sender_email: str = "compliance@example.com",
    ) -> str:
        """
        Generate a plain text demand letter.

        Args:
            recipient_name: Name of the recipient
            recipient_email: Email address of the recipient
            website_url: URL of the non-compliant website
            compliance_issues: List of compliance issues found
            sender_name: Name of the sender
            sender_organization: Organization name
            sender_email: Sender's email

        Returns:
            Plain text string of the generated letter
        """
        try:
            logger.info(f"Generating text letter for: {recipient_name} ({website_url})")

            letter_text = f"""
{"=" * 60}
DEMAND LETTER
Web Accessibility Compliance Notice
{"=" * 60}

Date: {datetime.now().strftime("%B %d, %Y")}

To: {recipient_name}
Email: {recipient_email}
Website: {website_url}

{"=" * 60}
RE: Notice of Americans with Disabilities Act (ADA) Non-Compliance
{"=" * 60}

Dear {recipient_name},

Our organization has identified accessibility barriers on your website that may prevent individuals with disabilities from fully accessing your online services. This constitutes a potential violation of the Americans with Disabilities Act (ADA) and Title III of the Civil Rights Act of 1990.

IDENTIFIED COMPLIANCE ISSUES:
{"-" * 50}
"""

            for index, issue in enumerate(compliance_issues, 1):
                letter_text += f"""
{index}. [{issue["severity"]}] {issue["category"]}
   Description: {issue["description"]}
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

{"-" * 50}
Sincerely,

{sender_name}
{sender_organization}
Email: {sender_email}

LEGAL NOTICE: This letter is provided for informational purposes only and does not 
constitute legal advice. Recipients are encouraged to consult with qualified legal 
counsel regarding ADA compliance requirements.
"""

            logger.info(
                f"Successfully generated text letter with {len(compliance_issues)} issues"
            )
            return letter_text

        except Exception as e:
            logger.error(f"Error generating text letter: {e}")
            raise

    def save_letter(
        self, letter_content: str, filename: str, output_directory: Optional[str] = None
    ) -> str:
        """
        Save a generated letter to file.

        Args:
            letter_content: The letter content to save
            filename: Name of the file to save
            output_directory: Optional output directory path

        Returns:
            Full path to the saved file
        """
        try:
            if output_directory is None:
                output_directory = os.path.join(
                    os.path.dirname(__file__), "..", "..", "output", "letters"
                )

            os.makedirs(output_directory, exist_ok=True)
            filepath = os.path.join(output_directory, filename)

            with open(filepath, "w", encoding="utf-8") as output_file:
                output_file.write(letter_content)

            logger.info(f"Saved letter to: {filepath}")
            return filepath

        except IOError as e:
            logger.error(f"Failed to save letter to {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving letter: {e}")
            raise

    def generate_and_save(
        self,
        recipient_name: str,
        recipient_email: str,
        website_url: str,
        compliance_issues: List[Dict[str, str]],
        output_filename: str,
        letter_format: str = "html",
        **kwargs,
    ) -> str:
        """
        Generate and save a letter in one operation.

        Args:
            recipient_name: Name of the recipient
            recipient_email: Email address of the recipient
            website_url: URL of the non-compliant website
            compliance_issues: List of compliance issues found
            output_filename: Name of the output file
            letter_format: Format type ("html" or "text")
            **kwargs: Additional arguments passed to letter generator

        Returns:
            Full path to the saved file
        """
        try:
            logger.info(
                f"Generating and saving {letter_format} letter for {recipient_name}"
            )

            if letter_format.lower() == "html":
                letter_content = self.generate_html_letter(
                    recipient_name=recipient_name,
                    recipient_email=recipient_email,
                    website_url=website_url,
                    compliance_issues=compliance_issues,
                    **kwargs,
                )
            else:
                letter_content = self.generate_text_letter(
                    recipient_name=recipient_name,
                    recipient_email=recipient_email,
                    website_url=website_url,
                    compliance_issues=compliance_issues,
                    **kwargs,
                )

            filepath = self.save_letter(letter_content, output_filename)
            logger.info(f"Letter generation and save complete: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to generate and save letter: {e}")
            raise
