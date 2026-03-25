#!/usr/bin/env python3
"""
ADA Compliance Suite CLI
Main command-line interface with proper error handling and logging.
"""

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.compliance_checker import ADAComplianceChecker
from src.letters.letter_generator import LetterGenerator
from src.monitoring.monitor import ComplianceMonitor
from src.reports.report_generator import ReportGenerator
from src.autonomous_engine import AutonomousEngine


def check_website_compliance(args: argparse.Namespace) -> None:
    """
    Check a website for ADA compliance.

    Args:
        args: Command line arguments
    """
    try:
        logger.info(f"Checking compliance for: {args.url}")

        checker = ADAComplianceChecker(args.url)

        if checker.run_all_checks():
            report = checker.generate_report()

            if args.json:
                output_data = {
                    "url": report.url,
                    "total_issues": report.total_issues,
                    "severity_counts": {
                        "High": report.high_issues,
                        "Medium": report.medium_issues,
                        "Low": report.low_issues,
                    },
                    "issues": report.issues,
                }
                print(json.dumps(output_data, indent=2))
            else:
                print(f"\n{'=' * 60}")
                print(f"ADA Compliance Report for {report.url}")
                print(f"{'=' * 60}")
                print(f"\nTotal Issues: {report.total_issues}")
                print(f"  High: {report.high_issues}")
                print(f"  Medium: {report.medium_issues}")
                print(f"  Low: {report.low_issues}")

                if args.verbose and report.issues:
                    print(f"\n{'=' * 60}")
                    print("Issue Details:")
                    print(f"{'=' * 60}")
                    for index, issue in enumerate(report.issues, 1):
                        print(f"\n{index}. [{issue['severity']}] {issue['category']}")
                        print(
                            f"   WCAG {issue['wcag_criterion']}: {issue['description']}"
                        )
                        print(f"   Fix: {issue['suggestion']}")

            if args.output:
                output_data = {
                    "url": report.url,
                    "total_issues": report.total_issues,
                    "severity_counts": {
                        "High": report.high_issues,
                        "Medium": report.medium_issues,
                        "Low": report.low_issues,
                    },
                    "issues": report.issues,
                }
                with open(args.output, "w") as output_file:
                    json.dump(output_data, output_file, indent=2)
                print(f"\n\nReport saved to {args.output}")

            logger.info(
                f"Compliance check complete: {report.total_issues} issues found"
            )
        else:
            print("Failed to fetch page. Please check the URL and try again.")
            logger.error("Failed to fetch webpage for compliance check")

    except Exception as e:
        logger.error(f"Error during compliance check: {e}")
        print(f"An error occurred: {e}")


def generate_demand_letter(args: argparse.Namespace) -> None:
    """
    Generate a demand letter for ADA non-compliance.

    Args:
        args: Command line arguments
    """
    try:
        logger.info(f"Generating letter for: {args.recipient}")

        letter_generator = LetterGenerator()
        compliance_issues = []

        if args.check_url:
            logger.info(f"Checking website for issues: {args.check_url}")
            checker = ADAComplianceChecker(args.check_url)
            if checker.run_all_checks():
                report = checker.generate_report()
                compliance_issues = report.issues
            else:
                logger.warning(
                    f"Failed to check {args.check_url}, generating letter with empty issues"
                )
        else:
            logger.info("Generating letter without website check")

        if args.text:
            letter_content = letter_generator.generate_text_letter(
                recipient_name=args.recipient,
                recipient_email=args.email,
                website_url=args.website,
                compliance_issues=compliance_issues,
                sender_name=args.sender or "ADA Compliance Team",
                sender_organization=args.organization or "Web Accessibility Services",
                sender_email=args.sender_email or "compliance@example.com",
            )
        else:
            letter_content = letter_generator.generate_html_letter(
                recipient_name=args.recipient,
                recipient_email=args.email,
                recipient_address=args.address or "Address on file",
                website_url=args.website,
                compliance_issues=compliance_issues,
                sender_name=args.sender or "ADA Compliance Team",
                sender_organization=args.organization or "Web Accessibility Services",
                sender_email=args.sender_email or "compliance@example.com",
                sender_phone=args.phone or "555-555-5555",
            )

        if args.output:
            filepath = letter_generator.save_letter(letter_content, args.output)
            print(f"Letter saved to {filepath}")
            logger.info(f"Letter saved: {filepath}")
        else:
            print(letter_content)

    except Exception as e:
        logger.error(f"Error generating letter: {e}")
        print(f"An error occurred: {e}")


def manage_monitoring(args: argparse.Namespace) -> None:
    """
    Manage website monitoring.

    Args:
        args: Command line arguments
    """
    try:
        monitor = ComplianceMonitor()

        if args.add:
            monitor.add_site(args.url, args.name, args.email)
            print(f"Added {args.url} to monitoring")
            logger.info(f"Added site to monitoring: {args.url}")

        elif args.remove:
            if monitor.remove_site(args.url):
                print(f"Removed {args.url} from monitoring")
                logger.info(f"Removed site from monitoring: {args.url}")
            else:
                print(f"Site not found: {args.url}")

        elif args.check:
            result = monitor.check_single_site(args.url)
            if result:
                print(f"Checked {args.url}: {result['total_issues']} issues found")
            else:
                print(f"Failed to check {args.url}")

        elif args.check_all:
            results = monitor.check_all_sites()
            print(f"Checked {len(results)} sites")
            for result in results:
                print(f"  {result['url']}: {result['report']['total_issues']} issues")

        elif args.status:
            sites = monitor.get_all_monitored_sites()
            if sites:
                print("\nMonitored Sites:")
                for site in sites:
                    status_icon = "[✓]" if site["status"] == "compliant" else "[✗]"
                    print(
                        f"  {status_icon} {site['url']}: {site['issue_count']} issues ({site['status']})"
                    )
            else:
                print("No sites being monitored. Use --add to add a site.")

        elif args.history:
            days = 30
            history = monitor.get_site_history(args.url, days=days)
            if history:
                print(f"\nHistory for {args.url} (last {days} days):")
                for check in history:
                    print(f"  {check['checked_at']}: {check['total_issues']} issues")
            else:
                print("No history found for this site.")
        else:
            sites = monitor.get_all_monitored_sites()
            print(f"Monitoring {len(sites)} sites")
            for site in sites:
                print(f"  {site['url']}")

    except Exception as e:
        logger.error(f"Error in monitoring: {e}")
        print(f"An error occurred: {e}")


def run_autonomous(args: argparse.Namespace) -> None:
    """Run the autonomous compliance engine."""
    try:
        engine = AutonomousEngine()

        if args.once:
            logger.info("Running single autonomous cycle")
            engine.run_full_cycle()
        else:
            logger.info(f"Starting autonomous engine - {args.interval}h cycles")
            engine.run_continuous(args.interval)

    except Exception as e:
        logger.error(f"Error in autonomous mode: {e}")
        print(f"An error occurred: {e}")


def generate_compliance_report(args: argparse.Namespace) -> None:
    """
    Generate compliance reports.

    Args:
        args: Command line arguments
    """
    try:
        report_generator = ReportGenerator()

        if args.type == "summary" and args.url:
            checker = ADAComplianceChecker(args.url)
            if checker.run_all_checks():
                report = checker.generate_report()

                report_data = {
                    "url": report.url,
                    "total_issues": report.total_issues,
                    "severity_counts": {
                        "High": report.high_issues,
                        "Medium": report.medium_issues,
                        "Low": report.low_issues,
                    },
                    "issues": report.issues,
                }

                html = report_generator.generate_summary_report(report_data)
                output_filename = args.output or "compliance_report.html"
                filepath = report_generator.save_report(html, output_filename)
                print(f"Report saved to {filepath}")
                logger.info(f"Summary report generated: {filepath}")
            else:
                print("Failed to generate report")

        elif args.type == "progress" and args.url:
            monitor = ComplianceMonitor()
            history = monitor.get_site_history(args.url, days=args.days or 30)
            html = report_generator.generate_progress_report(history, args.url)
            output_filename = args.output or "progress_report.html"
            filepath = report_generator.save_report(html, output_filename)
            print(f"Report saved to {filepath}")
            logger.info(f"Progress report generated: {filepath}")

        elif args.type == "batch" and args.urls:
            logger.info(f"Generating batch report for {len(args.urls)} sites")

            results: List[dict] = []

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(ADAComplianceChecker(url).run_checks): url
                    for url in args.urls
                }

                for future in as_completed(futures):
                    website_url = futures[future]
                    try:
                        checker = ADAComplianceChecker(website_url)
                        if checker.run_all_checks():
                            report = checker.generate_report()
                            results.append(
                                {
                                    "url": website_url,
                                    "report": {
                                        "total_issues": report.total_issues,
                                        "severity_counts": {
                                            "High": report.high_issues,
                                            "Medium": report.medium_issues,
                                            "Low": report.low_issues,
                                        },
                                    },
                                }
                            )
                    except Exception as site_error:
                        logger.error(f"Error checking {website_url}: {site_error}")

            html = report_generator.generate_batch_report(results)
            output_filename = args.output or "batch_report.html"
            filepath = report_generator.save_report(html, output_filename)
            print(f"Report saved to {filepath}")
            logger.info(f"Batch report generated: {filepath}")

        else:
            print(
                "Invalid command. Specify --url for single/progress or --urls for batch reports."
            )

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        print(f"An error occurred: {e}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ADA Compliance Suite - Web accessibility checking and monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Check a website:
    python cli.py check --url https://example.com
    
  Check with verbose output:
    python cli.py check --url https://example.com --verbose
    
  Generate HTML report:
    python cli.py check --url https://example.com --output report.json
    
  Generate a demand letter:
    python cli.py letter --recipient "Business" --email "test@test.com" --website "https://example.com"
    
  Monitor a website:
    python cli.py monitor --add --url https://example.com --email "test@test.com"
    
  Generate summary report:
    python cli.py report --type summary --url https://example.com
        """,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    check_parser = subparsers.add_parser(
        "check", help="Check a website for ADA compliance"
    )
    check_parser.add_argument(
        "--url", required=True, help="URL to check for ADA compliance"
    )
    check_parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    check_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed issues"
    )
    check_parser.add_argument("--output", "-o", help="Save report to file")

    letter_parser = subparsers.add_parser("letter", help="Generate a demand letter")
    letter_parser.add_argument("--recipient", required=True, help="Recipient name")
    letter_parser.add_argument("--email", required=True, help="Recipient email")
    letter_parser.add_argument("--website", required=True, help="Website URL")
    letter_parser.add_argument("--address", help="Recipient address")
    letter_parser.add_argument(
        "--check-url", help="URL to check for issues to include in letter"
    )
    letter_parser.add_argument(
        "--text", action="store_true", help="Generate plain text letter instead of HTML"
    )
    letter_parser.add_argument("--sender", help="Sender name")
    letter_parser.add_argument("--organization", help="Organization name")
    letter_parser.add_argument("--sender-email", help="Sender email")
    letter_parser.add_argument("--phone", help="Sender phone")
    letter_parser.add_argument("--output", "-o", help="Output filename")

    monitor_parser = subparsers.add_parser(
        "monitor", help="Monitor websites for compliance"
    )
    monitor_parser.add_argument("--url", help="Website URL")
    monitor_parser.add_argument("--name", help="Site name")
    monitor_parser.add_argument("--email", help="Contact email")
    monitor_parser.add_argument(
        "--add", action="store_true", help="Add site to monitoring"
    )
    monitor_parser.add_argument(
        "--remove", action="store_true", help="Remove site from monitoring"
    )
    monitor_parser.add_argument(
        "--check", action="store_true", help="Check a monitored site"
    )
    monitor_parser.add_argument(
        "--check-all", action="store_true", help="Check all monitored sites"
    )
    monitor_parser.add_argument(
        "--status", action="store_true", help="Show monitoring status"
    )
    monitor_parser.add_argument(
        "--history", action="store_true", help="Show site history"
    )

    report_parser = subparsers.add_parser("report", help="Generate compliance reports")
    report_parser.add_argument(
        "--type",
        choices=["summary", "progress", "batch"],
        default="summary",
        help="Report type",
    )
    report_parser.add_argument("--url", help="URL for single site report")
    report_parser.add_argument("--urls", nargs="+", help="URLs for batch report")
    report_parser.add_argument(
        "--days", type=int, help="Days of history for progress report"
    )
    report_parser.add_argument("--output", "-o", help="Output filename")

    auto_parser = subparsers.add_parser(
        "autonomous", help="Run autonomous compliance engine"
    )
    auto_parser.add_argument(
        "--once", action="store_true", help="Run single cycle and exit"
    )
    auto_parser.add_argument(
        "--interval", type=int, default=24, help="Hours between cycles (default: 24)"
    )
    auto_parser.add_argument("--url", type=str, help="Check single URL autonomously")
    auto_parser.add_argument(
        "--no-email", action="store_true", help="Don't send emails"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.command == "check":
        check_website_compliance(args)
    elif args.command == "letter":
        generate_demand_letter(args)
    elif args.command == "monitor":
        manage_monitoring(args)
    elif args.command == "report":
        generate_compliance_report(args)
    elif args.command == "autonomous":
        run_autonomous(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
