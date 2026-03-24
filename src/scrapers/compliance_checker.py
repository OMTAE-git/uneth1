"""
ADA Compliance Checker
Scans websites for ADA accessibility issues
"""

import argparse
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComplianceIssue:
    severity: str
    category: str
    element: str
    description: str
    suggestion: str
    wcag_criterion: str


class ADAComplianceChecker:
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

    def __init__(self, url: str):
        self.url = url
        self.issues: List[ComplianceIssue] = []
        self.html_content = None
        self.soup = None

    def fetch_page(self) -> bool:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            self.html_content = response.text
            self.soup = BeautifulSoup(self.html_content, "lxml")
            return True
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return False

    def check_alt_text(self):
        images_without_alt = self.soup.find_all("img", alt=False)
        for img in images_without_alt:
            src = img.get("src", "unknown")
            if not img.get("alt"):
                self.issues.append(
                    ComplianceIssue(
                        severity="High",
                        category="Images",
                        element=f"<img src='{src}'>",
                        description="Image missing alt text",
                        suggestion="Add descriptive alt text to describe the image content",
                        wcag_criterion="1.1.1",
                    )
                )

        images_with_empty_alt = self.soup.find_all("img", alt="")
        for img in images_with_empty_alt:
            src = img.get("src", "unknown")
            self.issues.append(
                ComplianceIssue(
                    severity="Medium",
                    category="Images",
                    element=f"<img src='{src}' alt=''>",
                    description="Image has empty alt text (decorative images only)",
                    suggestion="Ensure this image is truly decorative. If it conveys meaning, add alt text",
                    wcag_criterion="1.1.1",
                )
            )

    def check_headings(self):
        headings = self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        heading_levels = [int(h.name[1]) for h in headings]

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

        for i, level in enumerate(heading_levels[:-1]):
            next_level = heading_levels[i + 1]
            if next_level > level + 1:
                self.issues.append(
                    ComplianceIssue(
                        severity="Medium",
                        category="Structure",
                        element=headings[i + 1],
                        description=f"Heading level skipped (h{level} to h{next_level})",
                        suggestion=f"Use h{level + 1} instead of h{next_level}",
                        wcag_criterion="1.3.1",
                    )
                )

    def check_color_contrast(self):
        style_tags = self.soup.find_all("style")
        for style in style_tags:
            if "color:" in style.string and "background-color:" not in style.string:
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

    def check_keyboard_navigation(self):
        interactive_elements = self.soup.find_all(
            ["a", "button", "input", "select", "textarea"]
        )
        for elem in interactive_elements:
            if elem.name in ["a", "button"]:
                if not elem.get("href") and not elem.get("onclick"):
                    continue
            tabindex = elem.get("tabindex")
            if tabindex and int(tabindex) < 0:
                self.issues.append(
                    ComplianceIssue(
                        severity="Medium",
                        category="Keyboard Navigation",
                        element=elem,
                        description=f"Element has negative tabindex",
                        suggestion="Remove negative tabindex or ensure focus is managed programmatically",
                        wcag_criterion="2.1.1",
                    )
                )

    def check_links(self):
        links = self.soup.find_all("a", href=True)
        for link in links:
            text = link.get_text(strip=True)
            if not text:
                self.issues.append(
                    ComplianceIssue(
                        severity="Medium",
                        category="Links",
                        element=link,
                        description="Link has no text content",
                        suggestion="Add descriptive link text that explains the link destination",
                        wcag_criterion="2.4.4",
                    )
                )
            elif text.lower() in ["click here", "here", "read more", "more"]:
                self.issues.append(
                    ComplianceIssue(
                        severity="Low",
                        category="Links",
                        element=link,
                        description=f"Non-descriptive link text: '{text}'",
                        suggestion="Use descriptive link text that indicates the destination",
                        wcag_criterion="2.4.4",
                    )
                )

    def check_form_labels(self):
        inputs = self.soup.find_all("input", type=lambda t: t != "hidden")
        for inp in inputs:
            aria_label = inp.get("aria-label")
            aria_labelledby = inp.get("aria-labelledby")
            placeholder = inp.get("placeholder")
            associated_label = None

            input_id = inp.get("id")
            if input_id:
                associated_label = self.soup.find("label", attrs={"for": input_id})

            if (
                not aria_label
                and not aria_labelledby
                and not placeholder
                and not associated_label
            ):
                input_type = inp.get("type", "text")
                if input_type not in ["submit", "button", "reset", "image"]:
                    self.issues.append(
                        ComplianceIssue(
                            severity="High",
                            category="Forms",
                            element=inp,
                            description="Form input missing label or accessible name",
                            suggestion="Add a <label> element, aria-label, or aria-labelledby",
                            wcag_criterion="1.3.1",
                        )
                    )

    def run_checks(self):
        if not self.fetch_page():
            return False

        logger.info("Running ADA compliance checks...")
        self.check_alt_text()
        self.check_headings()
        self.check_color_contrast()
        self.check_keyboard_navigation()
        self.check_links()
        self.check_form_labels()

        return True

    def get_report(self) -> dict:
        severity_counts = {"High": 0, "Medium": 0, "Low": 0}
        for issue in self.issues:
            severity_counts[issue.severity] += 1

        return {
            "url": self.url,
            "total_issues": len(self.issues),
            "severity_counts": severity_counts,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "element": str(i.element)[:100],
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "wcag_criterion": i.wcag_criterion,
                    "wcag_description": self.WCAG_CRITERIA.get(i.wcag_criterion, ""),
                }
                for i in self.issues
            ],
        }


def main():
    parser = argparse.ArgumentParser(description="ADA Compliance Checker")
    parser.add_argument("--url", required=True, help="URL to check")
    parser.add_argument("--output", help="Output file for report (JSON)")
    args = parser.parse_args()

    checker = ADAComplianceChecker(args.url)

    if checker.run_checks():
        report = checker.get_report()

        print(f"\n{'=' * 60}")
        print(f"ADA Compliance Report for {report['url']}")
        print(f"{'=' * 60}")
        print(f"\nTotal Issues Found: {report['total_issues']}")
        print(f"  High: {report['severity_counts']['High']}")
        print(f"  Medium: {report['severity_counts']['Medium']}")
        print(f"  Low: {report['severity_counts']['Low']}")

        if report["issues"]:
            print(f"\n{'=' * 60}")
            print("Issue Details:")
            print(f"{'=' * 60}")

            for i, issue in enumerate(report["issues"], 1):
                print(f"\n{i}. [{issue['severity']}] {issue['category']}")
                print(
                    f"   WCAG: {issue['wcag_criterion']} - {issue['wcag_description']}"
                )
                print(f"   Issue: {issue['description']}")
                print(f"   Element: {issue['element']}")
                print(f"   Fix: {issue['suggestion']}")

        if args.output:
            import json

            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n\nFull report saved to {args.output}")


if __name__ == "__main__":
    main()
