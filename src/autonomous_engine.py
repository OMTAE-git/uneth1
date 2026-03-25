#!/usr/bin/env python3
"""
Autonomous ADA Compliance Engine
Automatically discovers, checks, and generates demand letters for non-compliant websites.
"""

import json
import logging
import os
import smtplib
import sqlite3
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.compliance_checker import ADAComplianceChecker
from src.letters.letter_generator import LetterGenerator
from src.monitoring.monitor import ComplianceMonitor
from src.reports.report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("autonomous.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AutonomousEngine:
    def __init__(self):
        self.compliance_checker = None
        self.letter_generator = LetterGenerator()
        self.monitor = ComplianceMonitor()
        self.report_generator = ReportGenerator()
        self.stats = {
            "sites_scanned": 0,
            "non_compliant": 0,
            "letters_generated": 0,
            "letters_sent": 0,
            "start_time": datetime.now(),
        }
        self._load_config()

    def _load_config(self):
        config_path = os.path.join(
            os.path.dirname(__file__), "config", "autonomous.json"
        )
        if os.path.exists(config_path):
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            self.config = {
                "smtp_host": os.getenv("SMTP_HOST", ""),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "smtp_user": os.getenv("SMTP_USER", ""),
                "smtp_pass": os.getenv("SMTP_PASS", ""),
                "from_email": os.getenv("FROM_EMAIL", ""),
                "from_name": os.getenv("FROM_NAME", "ADA Compliance Team"),
                "check_interval_hours": 24,
                "max_sites_per_run": 50,
                "target_criteria": {"min_issues": 1, "require_high_issues": False},
                "auto_discover": True,
            }
        logger.info(f"Config loaded: {len(self.config)} settings")

    def discover_targets(
        self, search_queries: List[str] = None
    ) -> List[Dict[str, str]]:
        discovered = []

        # Read from target queue if exists
        queue_path = os.path.join(os.path.dirname(__file__), "target_queue.json")
        if os.path.exists(queue_path):
            with open(queue_path) as f:
                discovered = json.load(f)

        if not search_queries:
            search_queries = self.config.get(
                "search_queries",
                [
                    "business website accessibility",
                    "ADA compliance failure",
                    "website not accessible",
                ],
            )

        logger.info(f"Discovery: Found {len(discovered)} targets in queue")
        return discovered

    def check_website(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Checking: {url}")
            checker = ADAComplianceChecker(url)

            if checker.run_all_checks():
                report = checker.generate_report()
                self.stats["sites_scanned"] += 1

                result = {
                    "url": url,
                    "total_issues": report.total_issues,
                    "high_issues": report.high_issues,
                    "medium_issues": report.medium_issues,
                    "low_issues": report.low_issues,
                    "issues": report.issues,
                    "checked_at": datetime.now().isoformat(),
                }

                if report.total_issues > 0:
                    self.stats["non_compliant"] += 1
                    self._save_target(result)

                return result
            return None
        except Exception as e:
            logger.error(f"Error checking {url}: {e}")
            return None

    def _save_target(self, result: Dict[str, Any]):
        db_path = os.path.join(os.path.dirname(__file__), "data", "targets.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                total_issues INTEGER,
                high_issues INTEGER,
                medium_issues INTEGER,
                low_issues INTEGER,
                issues_json TEXT,
                discovered_at TEXT,
                letter_sent INTEGER DEFAULT 0,
                letter_sent_at TEXT
            )
        """)

        cursor.execute(
            """
            INSERT OR REPLACE INTO targets 
            (url, total_issues, high_issues, medium_issues, low_issues, issues_json, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result["url"],
                result["total_issues"],
                result["high_issues"],
                result["medium_issues"],
                result["low_issues"],
                json.dumps(result["issues"]),
                result["checked_at"],
            ),
        )
        conn.commit()
        conn.close()

    def get_pending_targets(self) -> List[Dict[str, Any]]:
        db_path = os.path.join(os.path.dirname(__file__), "data", "targets.db")
        if not os.path.exists(db_path):
            return []

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM targets 
            WHERE letter_sent = 0 
            ORDER BY total_issues DESC, high_issues DESC
            LIMIT ?
        """,
            (self.config.get("max_sites_per_run", 50),),
        )

        targets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return targets

    def generate_letter(
        self, target: Dict[str, Any], contact_info: Dict[str, str] = None
    ) -> str:
        try:
            issues = (
                json.loads(target["issues_json"])
                if isinstance(target["issues_json"], str)
                else target["issues_json"]
            )

            recipient_name = (
                contact_info.get("name", "Legal Department")
                if contact_info
                else "Legal Department"
            )
            recipient_email = contact_info.get(
                "email", "legal@" + self._extract_domain(target["url"])
            )
            website_url = target["url"]

            letter_content = self.letter_generator.generate_html_letter(
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                recipient_address=contact_info.get("address", "Address on file")
                if contact_info
                else "Address on file",
                website_url=website_url,
                compliance_issues=issues,
                sender_name=self.config.get("from_name", "ADA Compliance Team"),
                sender_organization=self.config.get(
                    "from_org", "Web Accessibility Services"
                ),
                sender_email=self.config.get("from_email", "compliance@example.com"),
                sender_phone=self.config.get("from_phone", "555-555-5555"),
            )

            self.stats["letters_generated"] += 1
            return letter_content

        except Exception as e:
            logger.error(f"Error generating letter: {e}")
            return None

    def _extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse

        return urlparse(url).netloc.replace("www.", "")

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        if not self.config.get("smtp_host"):
            logger.warning("SMTP not configured, skipping email send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = (
                f"{self.config.get('from_name')} <{self.config.get('from_email')}>"
            )
            msg["To"] = to_email

            text_part = MIMEText(html_content.replace("<[^>]+>", " "), "plain")
            html_part = MIMEText(html_content, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP(
                self.config["smtp_host"], self.config["smtp_port"]
            ) as server:
                server.starttls()
                if self.config.get("smtp_user"):
                    server.login(self.config["smtp_user"], self.config["smtp_pass"])
                server.send_message(msg)

            self.stats["letters_sent"] += 1
            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def mark_letter_sent(self, url: str):
        db_path = os.path.join(os.path.dirname(__file__), "data", "targets.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE targets SET letter_sent = 1, letter_sent_at = ? WHERE url = ?
        """,
            (datetime.now().isoformat(), url),
        )
        conn.commit()
        conn.close()

    def run_full_cycle(self):
        logger.info("=" * 60)
        logger.info("AUTONOMOUS CYCLE STARTED")
        logger.info("=" * 60)

        # Check monitored sites
        monitored = self.monitor.get_all_monitored_sites()
        if monitored:
            logger.info(f"Checking {len(monitored)} monitored sites")
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.check_website, site["url"]): site
                    for site in monitored
                }
                for future in as_completed(futures):
                    future.result()

        # Process pending targets
        targets = self.get_pending_targets()
        logger.info(f"Processing {len(targets)} non-compliant targets")

        for target in targets:
            letter = self.generate_letter(target)
            if letter:
                recipient_email = "legal@" + self._extract_domain(target["url"])
                subject = (
                    f"ADA Compliance Demand - {self._extract_domain(target['url'])}"
                )

                if self.config.get("auto_send", True):
                    self.send_email(recipient_email, subject, letter)

                self.mark_letter_sent(target["url"])

                # Save letter
                self._save_letter(target["url"], letter)

        # Print stats
        self._print_stats()

    def _save_letter(self, url: str, content: str):
        letters_dir = os.path.join(os.path.dirname(__file__), "data", "letters")
        os.makedirs(letters_dir, exist_ok=True)

        filename = f"{self._extract_domain(url)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(letters_dir, filename)

        with open(filepath, "w") as f:
            f.write(content)
        logger.info(f"Letter saved: {filepath}")

    def _print_stats(self):
        runtime = datetime.now() - self.stats["start_time"]
        logger.info("=" * 60)
        logger.info("AUTONOMOUS ENGINE STATS")
        logger.info(f"  Runtime: {runtime}")
        logger.info(f"  Sites Scanned: {self.stats['sites_scanned']}")
        logger.info(f"  Non-Compliant: {self.stats['non_compliant']}")
        logger.info(f"  Letters Generated: {self.stats['letters_generated']}")
        logger.info(f"  Letters Sent: {self.stats['letters_sent']}")
        logger.info("=" * 60)

    def run_continuous(self, interval_hours: int = None):
        if interval_hours is None:
            interval_hours = self.config.get("check_interval_hours", 24)

        logger.info(f"Starting autonomous engine - cycle every {interval_hours}h")

        import schedule

        self.run_full_cycle()  # Run immediately

        schedule.every(interval_hours).hours.do(self.run_full_cycle)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Autonomous engine stopped")
            self._print_stats()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous ADA Compliance Engine")
    parser.add_argument("--once", action="store_true", help="Run single cycle and exit")
    parser.add_argument("--interval", type=int, default=24, help="Hours between cycles")
    parser.add_argument("--url", type=str, help="Check single URL")
    parser.add_argument("--no-email", action="store_true", help="Don't send emails")

    args = parser.parse_args()

    engine = AutonomousEngine()

    if args.url:
        result = engine.check_website(args.url)
        if result:
            print(json.dumps(result, indent=2))
        return

    if args.no_email:
        engine.config["auto_send"] = False

    if args.once:
        engine.run_full_cycle()
    else:
        engine.run_continuous(args.interval)


if __name__ == "__main__":
    main()
