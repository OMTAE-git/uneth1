#!/usr/bin/env python3
"""
ADA Compliance Suite CLI
Main command-line interface for the ADA compliance checking system
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.compliance_checker import ADAComplianceChecker
from src.letters.letter_generator import LetterGenerator
from src.monitoring.monitor import ComplianceMonitor
from src.reports.report_generator import ReportGenerator


def check_compliance(args):
    checker = ADAComplianceChecker(args.url)

    if checker.run_checks():
        report = checker.get_report()

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"\n{'=' * 60}")
            print(f"ADA Compliance Report for {report['url']}")
            print(f"{'=' * 60}")
            print(f"\nTotal Issues: {report['total_issues']}")
            print(f"  High: {report['severity_counts']['High']}")
            print(f"  Medium: {report['severity_counts']['Medium']}")
            print(f"  Low: {report['severity_counts']['Low']}")

            if args.verbose and report["issues"]:
                print(f"\n{'=' * 60}")
                print("Issue Details:")
                print(f"{'=' * 60}")
                for i, issue in enumerate(report["issues"], 1):
                    print(f"\n{i}. [{issue['severity']}] {issue['category']}")
                    print(f"   WCAG {issue['wcag_criterion']}: {issue['description']}")
                    print(f"   Fix: {issue['suggestion']}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to {args.output}")

        return report
    else:
        print("Failed to fetch page. Please check the URL and try again.")
        return None


def generate_letter(args):
    letter_gen = LetterGenerator()

    if args.check_url:
        checker = ADAComplianceChecker(args.check_url)
        if checker.run_checks():
            report = checker.get_report()
            issues = report["issues"]
        else:
            issues = []
    else:
        issues = []

    if args.text:
        letter = letter_gen.generate_text_letter(
            recipient_name=args.recipient,
            recipient_email=args.email,
            website_url=args.website,
            issues=issues,
        )
    else:
        letter = letter_gen.generate_demand_letter(
            recipient_name=args.recipient,
            recipient_email=args.email,
            recipient_address=args.address or "Address on file",
            website_url=args.website,
            issues=issues,
            sender_name=args.sender or "ADA Compliance Team",
            sender_organization=args.organization or "Web Accessibility Services",
            sender_email=args.sender_email or "compliance@example.com",
            sender_phone=args.phone or "555-555-5555",
        )

    if args.output:
        filepath = letter_gen.save_letter(letter, args.output)
        print(f"Letter saved to {filepath}")
    else:
        print(letter)


def monitor_site(args):
    monitor = ComplianceMonitor()

    if args.add:
        monitor.add_site(args.url, args.name, args.email)
        print(f"Added {args.url} to monitoring")
    elif args.remove:
        monitor.remove_site(args.url)
        print(f"Removed {args.url} from monitoring")
    elif args.check:
        report = monitor.check_site(args.url)
        if report:
            print(f"Checked {args.url}: {report['total_issues']} issues found")
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
                print(
                    f"  {site['url']}: {site['issue_count']} issues ({site['status']})"
                )
        else:
            print("No sites being monitored. Use --add to add a site.")
    elif args.history:
        history = monitor.get_site_history(args.url)
        if history:
            print(f"\nHistory for {args.url} (last 30 days):")
            for check in history:
                print(f"  {check['checked_at']}: {check['total_issues']} issues")
        else:
            print("No history found for this site.")
    else:
        sites = monitor.get_all_monitored_sites()
        print(f"Monitoring {len(sites)} sites")
        for site in sites:
            print(f"  {site['url']}")


def generate_report(args):
    report_gen = ReportGenerator()

    if args.type == "summary" and args.url:
        checker = ADAComplianceChecker(args.url)
        if checker.run_checks():
            report = checker.get_report()
            html = report_gen.generate_summary_report(report)
            filepath = report_gen.save_report(
                html, args.output or "compliance_report.html"
            )
            print(f"Report saved to {filepath}")
        else:
            print("Failed to generate report")
    elif args.type == "progress" and args.url:
        monitor = ComplianceMonitor()
        history = monitor.get_site_history(args.url, days=args.days or 30)
        html = report_gen.generate_progress_report(history, args.url)
        filepath = report_gen.save_report(html, args.output or "progress_report.html")
        print(f"Report saved to {filepath}")
    elif args.type == "batch" and args.urls:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(ADAComplianceChecker(url).run_checks): url
                for url in args.urls
            }
            for future in as_completed(futures):
                url = futures[future]
                try:
                    checker = ADAComplianceChecker(url)
                    if checker.run_checks():
                        results.append({"url": url, "report": checker.get_report()})
                except Exception as e:
                    print(f"Error checking {url}: {e}")

        html = report_gen.generate_batch_report(results)
        filepath = report_gen.save_report(html, args.output or "batch_report.html")
        print(f"Report saved to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="ADA Compliance Suite")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    check_parser = subparsers.add_parser(
        "check", help="Check a website for ADA compliance"
    )
    check_parser.add_argument("--url", required=True, help="URL to check")
    check_parser.add_argument("--json", action="store_true", help="Output as JSON")
    check_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed issues"
    )
    check_parser.add_argument("--output", "-o", help="Save report to file")

    letter_parser = subparsers.add_parser("letter", help="Generate a demand letter")
    letter_parser.add_argument("--recipient", required=True, help="Recipient name")
    letter_parser.add_argument("--email", required=True, help="Recipient email")
    letter_parser.add_argument("--website", required=True, help="Website URL")
    letter_parser.add_argument("--address", help="Recipient address")
    letter_parser.add_argument("--check-url", help="URL to check for issues")
    letter_parser.add_argument(
        "--text", action="store_true", help="Generate plain text letter"
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

    args = parser.parse_args()

    if args.command == "check":
        check_compliance(args)
    elif args.command == "letter":
        generate_letter(args)
    elif args.command == "monitor":
        monitor_site(args)
    elif args.command == "report":
        generate_report(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
