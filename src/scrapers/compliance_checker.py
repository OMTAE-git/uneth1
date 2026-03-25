"""
ADA Compliance Checker
Scans websites for ADA accessibility issues with proper error handling and logging.
"""

import argparse
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ComplianceIssue:
    """Represents a single ADA compliance issue found on a website."""

    severity: str
    category: str
    element: str
    description: str
    suggestion: str
    wcag_criterion: str


@dataclass
class ComplianceReport:
    """Container for the complete compliance check report."""

    url: str
    total_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    issues: List[ComplianceIssue] = field(default_factory=list)
    error_message: Optional[str] = None


class ADAComplianceChecker:
    """
    Scans websites for ADA accessibility violations.

    Checks for:
    - Missing alt text on images
    - Improper heading structure
    - Color contrast issues
    - Keyboard navigation problems
    - Non-descriptive links
    - Missing form labels
    """

    WCAG_CRITERIA = {
        "1.1.1": "Non-text Content - All non-text content has text alternative",
        "1.3.1": "Info and Relationships - Information structure is programmatically determinable",
        "1.4.3": "Contrast (Minimum) - Text has contrast ratio of at least 4.5:1",
        "2.1.1": "Keyboard - All functionality available by keyboard",
        "2.4.1": "Bypass Blocks - Skip navigation links provided",
        "2.4.2": "Page Titled - Pages have descriptive titles",
        "2.4.4": "Link Purpose - Link text describes purpose",
        "2.4.7": "Focus Visible - Keyboard focus is visible",
    }

    def __init__(self, target_url: str) -> None:
        """
        Initialize the compliance checker.

        Args:
            target_url: The URL of the website to check
        """
        self.target_url = target_url
        self.issues: List[ComplianceIssue] = []
        self.html_content: Optional[str] = None
        self.parsed_html: Optional[BeautifulSoup] = None

        logger.info(f"Initialized ADA Compliance Checker for: {target_url}")

    def fetch_webpage(self) -> bool:
        """
        Fetch the webpage content.

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            logger.info(f"Fetching webpage: {self.target_url}")

            response = requests.get(self.target_url, headers=headers, timeout=30)
            response.raise_for_status()

            self.html_content = response.text
            self.parsed_html = BeautifulSoup(self.html_content, "lxml")

            logger.info(f"Successfully fetched {len(self.html_content)} bytes")
            return True

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching {self.target_url}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {self.target_url}: {e}")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {self.target_url}: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {self.target_url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error fetching {self.target_url}: {e}")
            return False

    def check_missing_alt_text(self) -> None:
        """
        Check for images missing alt text.

        WCAG 1.1.1: All images should have alt text for accessibility.
        """
        try:
            if not self.parsed_html:
                logger.warning("No parsed HTML available for alt text check")
                return

            logger.info("Checking for missing alt text on images...")

            images_without_alt = self.parsed_html.find_all("img", alt=False)
            for img_element in images_without_alt:
                image_source = img_element.get("src", "unknown source")
                if not img_element.get("alt"):
                    self.issues.append(
                        ComplianceIssue(
                            severity="High",
                            category="Images",
                            element=f"<img src='{image_source}'>",
                            description="Image missing alt text",
                            suggestion="Add descriptive alt text to describe the image content",
                            wcag_criterion="1.1.1",
                        )
                    )
                    logger.debug(f"Found image without alt: {image_source}")

            images_with_empty_alt = self.parsed_html.find_all("img", alt="")
            for img_element in images_with_empty_alt:
                image_source = img_element.get("src", "unknown source")
                self.issues.append(
                    ComplianceIssue(
                        severity="Medium",
                        category="Images",
                        element=f"<img src='{image_source}' alt=''>",
                        description="Image has empty alt text (decorative images only)",
                        suggestion="Ensure this image is truly decorative. If it conveys meaning, add alt text",
                        wcag_criterion="1.1.1",
                    )
                )

            logger.info(
                f"Alt text check complete. Found {len(images_without_alt)} images without alt"
            )

        except Exception as e:
            logger.error(f"Error checking alt text: {e}")

    def check_heading_structure(self) -> None:
        """
        Check for proper heading hierarchy.

        WCAG 1.3.1: Headings should follow logical order (h1 -> h2 -> h3).
        """
        try:
            if not self.parsed_html:
                logger.warning("No parsed HTML available for heading check")
                return

            logger.info("Checking heading structure...")

            all_headings = self.parsed_html.find_all(
                ["h1", "h2", "h3", "h4", "h5", "h6"]
            )
            heading_levels = [int(heading_tag.name[1]) for heading_tag in all_headings]

            if 1 not in heading_levels:
                self.issues.append(
                    ComplianceIssue(
                        severity="High",
                        category="Structure",
                        element="<body>",
                        description="Page missing h1 heading",
                        suggestion="Add an h1 heading that describes the page content",
                        wcag_criterion="1.3.1",
                    )
                )
                logger.warning("Page is missing h1 heading")

            for current_index in range(len(heading_levels) - 1):
                current_level = heading_levels[current_index]
                next_level = heading_levels[current_index + 1]

                if next_level > current_level + 1:
                    heading_element = all_headings[current_index + 1]
                    self.issues.append(
                        ComplianceIssue(
                            severity="Medium",
                            category="Structure",
                            element=str(heading_element)[:100],
                            description=f"Heading level skipped (h{current_level} to h{next_level})",
                            suggestion=f"Use h{current_level + 1} instead of h{next_level}",
                            wcag_criterion="1.3.1",
                        )
                    )
                    logger.debug(
                        f"Skipped heading level: h{current_level} to h{next_level}"
                    )

            logger.info(f"Heading check complete. Found {len(all_headings)} headings")

        except Exception as e:
            logger.error(f"Error checking headings: {e}")

    def check_color_contrast(self) -> None:
        """
        Check for potential color contrast issues.

        WCAG 1.4.3: Text should have minimum 4.5:1 contrast ratio.
        """
        try:
            if not self.parsed_html:
                logger.warning("No parsed HTML available for contrast check")
                return

            logger.info("Checking color contrast...")

            style_blocks = self.parsed_html.find_all("style")
            for style_block in style_blocks:
                style_content = style_block.string or ""
                if (
                    "color:" in style_content
                    and "background-color:" not in style_content
                ):
                    self.issues.append(
                        ComplianceIssue(
                            severity="Low",
                            category="Color Contrast",
                            element="<style>",
                            description="Inline styles may not meet contrast requirements",
                            suggestion="Verify color contrast ratio is at least 4.5:1 for normal text",
                            wcag_criterion="1.4.3",
                        )
                    )

            logger.info(
                f"Contrast check complete. Found {len(style_blocks)} style blocks"
            )

        except Exception as e:
            logger.error(f"Error checking contrast: {e}")

    def check_keyboard_navigation(self) -> None:
        """
        Check for keyboard navigation issues.

        WCAG 2.1.1: All functionality should be keyboard accessible.
        """
        try:
            if not self.parsed_html:
                logger.warning("No parsed HTML available for keyboard nav check")
                return

            logger.info("Checking keyboard navigation...")

            interactive_elements = self.parsed_html.find_all(
                ["a", "button", "input", "select", "textarea"]
            )

            for element in interactive_elements:
                if element.name in ["a", "button"]:
                    if not element.get("href") and not element.get("onclick"):
                        continue

                tab_index_value = element.get("tabindex")
                if tab_index_value:
                    try:
                        if int(tab_index_value) < 0:
                            self.issues.append(
                                ComplianceIssue(
                                    severity="Medium",
                                    category="Keyboard Navigation",
                                    element=str(element)[:100],
                                    description="Element has negative tabindex",
                                    suggestion="Remove negative tabindex or ensure focus is managed programmatically",
                                    wcag_criterion="2.1.1",
                                )
                            )
                            logger.debug(f"Found negative tabindex: {tab_index_value}")
                    except ValueError:
                        pass

            logger.info(
                f"Keyboard nav check complete. Found {len(interactive_elements)} interactive elements"
            )

        except Exception as e:
            logger.error(f"Error checking keyboard navigation: {e}")

    def check_link_descriptions(self) -> None:
        """
        Check for non-descriptive link text.

        WCAG 2.4.4: Link text should describe the link destination.
        """
        try:
            if not self.parsed_html:
                logger.warning("No parsed HTML available for link check")
                return

            logger.info("Checking link descriptions...")

            links_with_href = self.parsed_html.find_all("a", href=True)

            for link_element in links_with_href:
                link_text = link_element.get_text(strip=True)

                if not link_text:
                    self.issues.append(
                        ComplianceIssue(
                            severity="Medium",
                            category="Links",
                            element=str(link_element)[:100],
                            description="Link has no text content",
                            suggestion="Add descriptive link text that explains the link destination",
                            wcag_criterion="2.4.4",
                        )
                    )
                    logger.debug("Found link without text content")

                elif link_text.lower() in ["click here", "here", "read more", "more"]:
                    self.issues.append(
                        ComplianceIssue(
                            severity="Low",
                            category="Links",
                            element=str(link_element)[:100],
                            description=f"Non-descriptive link text: '{link_text}'",
                            suggestion="Use descriptive link text that indicates the destination",
                            wcag_criterion="2.4.4",
                        )
                    )
                    logger.debug(f"Found non-descriptive link: '{link_text}'")

            logger.info(f"Link check complete. Found {len(links_with_href)} links")

        except Exception as e:
            logger.error(f"Error checking links: {e}")

    def check_form_accessibility(self) -> None:
        """
        Check for form inputs missing labels.

        WCAG 1.3.1: Form inputs should have associated labels.
        """
        try:
            if not self.parsed_html:
                logger.warning("No parsed HTML available for form check")
                return

            logger.info("Checking form accessibility...")

            input_elements = self.parsed_html.find_all(
                "input", type=lambda t: t != "hidden"
            )

            for input_field in input_elements:
                aria_label = input_field.get("aria-label")
                aria_labelledby = input_field.get("aria-labelledby")
                placeholder = input_field.get("placeholder")

                input_id = input_field.get("id")
                associated_label = None
                if input_id:
                    associated_label = self.parsed_html.find(
                        "label", attrs={"for": input_id}
                    )

                if (
                    not aria_label
                    and not aria_labelledby
                    and not placeholder
                    and not associated_label
                ):
                    input_type = input_field.get("type", "text")
                    if input_type not in ["submit", "button", "reset", "image"]:
                        self.issues.append(
                            ComplianceIssue(
                                severity="High",
                                category="Forms",
                                element=str(input_field)[:100],
                                description="Form input missing label or accessible name",
                                suggestion="Add a <label> element, aria-label, or aria-labelledby",
                                wcag_criterion="1.3.1",
                            )
                        )
                        logger.debug(f"Found input without label: type={input_type}")

            logger.info(
                f"Form check complete. Found {len(input_elements)} input elements"
            )

        except Exception as e:
            logger.error(f"Error checking forms: {e}")

    def run_all_checks(self) -> bool:
        """
        Run all ADA compliance checks.

        Returns:
            True if checks completed, False if page fetch failed
        """
        logger.info(f"Starting ADA compliance checks for: {self.target_url}")

        if not self.fetch_webpage():
            logger.error("Failed to fetch webpage, aborting checks")
            return False

        self.check_missing_alt_text()
        self.check_heading_structure()
        self.check_color_contrast()
        self.check_keyboard_navigation()
        self.check_link_descriptions()
        self.check_form_accessibility()

        logger.info(
            f"Compliance checks complete. Found {len(self.issues)} total issues"
        )
        return True

    def generate_report(self) -> ComplianceReport:
        """
        Generate a compliance report from the check results.

        Returns:
            ComplianceReport with all findings
        """
        report = ComplianceReport(url=self.target_url, total_issues=len(self.issues))

        for issue in self.issues:
            if issue.severity == "High":
                report.high_issues += 1
            elif issue.severity == "Medium":
                report.medium_issues += 1
            elif issue.severity == "Low":
                report.low_issues += 1

            report.issues.append(
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "element": issue.element[:100],
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "wcag_criterion": issue.wcag_criterion,
                    "wcag_description": self.WCAG_CRITERIA.get(
                        issue.wcag_criterion, ""
                    ),
                }
            )

        logger.info(
            f"Generated report: {report.total_issues} issues ({report.high_issues} high, {report.medium_issues} medium, {report.low_issues} low)"
        )
        return report


def main() -> None:
    """CLI entry point for the compliance checker."""
    parser = argparse.ArgumentParser(
        description="ADA Compliance Checker - Scan websites for accessibility issues"
    )
    parser.add_argument("--url", required=True, help="URL to check for ADA compliance")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    checker = ADAComplianceChecker(args.url)

    if checker.run_all_checks():
        report = checker.generate_report()

        print(f"\n{'=' * 60}")
        print(f"ADA Compliance Report for {report.url}")
        print(f"{'=' * 60}")
        print(f"\nTotal Issues Found: {report.total_issues}")
        print(f"  High: {report.high_issues}")
        print(f"  Medium: {report.medium_issues}")
        print(f"  Low: {report.low_issues}")

        if report.issues:
            print(f"\n{'=' * 60}")
            print("Issue Details:")
            print(f"{'=' * 60}")

            for index, issue in enumerate(report.issues, 1):
                print(f"\n{index}. [{issue['severity']}] {issue['category']}")
                print(
                    f"   WCAG: {issue['wcag_criterion']} - {issue['wcag_description']}"
                )
                print(f"   Issue: {issue['description']}")
                print(f"   Element: {issue['element']}")
                print(f"   Fix: {issue['suggestion']}")

        if args.output:
            import json

            with open(args.output, "w") as output_file:
                json.dump(
                    {
                        "url": report.url,
                        "total_issues": report.total_issues,
                        "severity_counts": {
                            "High": report.high_issues,
                            "Medium": report.medium_issues,
                            "Low": report.low_issues,
                        },
                        "issues": report.issues,
                    },
                    output_file,
                    indent=2,
                )
            print(f"\n\nFull report saved to {args.output}")
    else:
        print("Failed to fetch page. Please check the URL and try again.")


if __name__ == "__main__":
    main()
