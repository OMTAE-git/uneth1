"""
Compliance Monitoring Module
Periodically checks websites for ADA compliance changes
"""

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import schedule
from dotenv import load_dotenv

load_dotenv()

from src.scrapers.compliance_checker import ADAComplianceChecker
from src.reports.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceMonitor:
    DB_PATH = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "compliance.db"
    )

    def __init__(self):
        self.init_database()
        self.report_gen = ReportGenerator()

    def init_database(self):
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitored_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                last_checked DATETIME,
                last_issue_count INTEGER,
                last_status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                issue_count INTEGER,
                high_issues INTEGER,
                medium_issues INTEGER,
                low_issues INTEGER,
                report_json TEXT,
                status TEXT,
                FOREIGN KEY (site_id) REFERENCES monitored_sites (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notification_type TEXT,
                message TEXT,
                sent BOOLEAN DEFAULT 0,
                FOREIGN KEY (site_id) REFERENCES monitored_sites (id)
            )
        """)

        conn.commit()
        conn.close()

    def add_site(self, url: str, name: str = None, email: str = None) -> int:
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO monitored_sites (url, name, email)
            VALUES (?, ?, ?)
        """,
            (url, name, email),
        )

        site_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Added site to monitoring: {url}")
        return site_id

    def remove_site(self, url: str):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM monitored_sites WHERE url = ?", (url,))
        result = cursor.fetchone()

        if result:
            site_id = result[0]
            cursor.execute(
                "DELETE FROM compliance_history WHERE site_id = ?", (site_id,)
            )
            cursor.execute("DELETE FROM notifications WHERE site_id = ?", (site_id,))
            cursor.execute("DELETE FROM monitored_sites WHERE id = ?", (site_id,))
            conn.commit()
            logger.info(f"Removed site from monitoring: {url}")
        else:
            logger.warning(f"Site not found: {url}")

        conn.close()

    def check_site(self, url: str) -> Optional[Dict]:
        try:
            checker = ADAComplianceChecker(url)
            if checker.run_checks():
                report = checker.get_report()
                self.save_check_result(url, report)
                return report
            return None
        except Exception as e:
            logger.error(f"Error checking site {url}: {e}")
            return None

    def save_check_result(self, url: str, report: Dict):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM monitored_sites WHERE url = ?", (url,))
        result = cursor.fetchone()

        if result:
            site_id = result[0]
            severity = report["severity_counts"]

            cursor.execute(
                """
                INSERT INTO compliance_history 
                (site_id, issue_count, high_issues, medium_issues, low_issues, report_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    site_id,
                    report["total_issues"],
                    severity["High"],
                    severity["Medium"],
                    severity["Low"],
                    str(report),
                    "improved" if report["total_issues"] == 0 else "issues_found",
                ),
            )

            cursor.execute(
                """
                UPDATE monitored_sites 
                SET last_checked = ?, last_issue_count = ?, last_status = ?
                WHERE id = ?
            """,
                (datetime.now(), report["total_issues"], "issues_found", site_id),
            )

            conn.commit()

        conn.close()

    def get_site_history(self, url: str, days: int = 30) -> List[Dict]:
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT s.id, s.url, h.checked_at, h.issue_count, h.high_issues, 
                   h.medium_issues, h.low_issues, h.status
            FROM monitored_sites s
            JOIN compliance_history h ON s.id = h.site_id
            WHERE s.url = ? AND h.checked_at > datetime('now', '-' || ? || ' days')
            ORDER BY h.checked_at DESC
        """,
            (url, days),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "url": row[1],
                "checked_at": row[2],
                "total_issues": row[3],
                "high_issues": row[4],
                "medium_issues": row[5],
                "low_issues": row[6],
                "status": row[7],
            }
            for row in rows
        ]

    def get_all_monitored_sites(self) -> List[Dict]:
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, url, name, email, last_checked, last_issue_count, last_status
            FROM monitored_sites
            ORDER BY last_checked DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "url": row[1],
                "name": row[2],
                "email": row[3],
                "last_checked": row[4],
                "issue_count": row[5],
                "status": row[6],
            }
            for row in rows
        ]

    def check_all_sites(self) -> List[Dict]:
        sites = self.get_all_monitored_sites()
        results = []

        for site in sites:
            logger.info(f"Checking site: {site['url']}")
            report = self.check_site(site["url"])
            if report:
                results.append({"url": site["url"], "report": report})

        return results

    def get_status_changes(self, days: int = 7) -> List[Dict]:
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT s.url, s.name, s.last_checked, s.last_issue_count,
                   h.issue_count as previous_count
            FROM monitored_sites s
            JOIN (
                SELECT site_id, issue_count
                FROM compliance_history
                WHERE checked_at < datetime('now', '-' || 1 || ' days')
                AND checked_at > datetime('now', '-' || ? || ' days')
            ) h ON s.id = h.site_id
            WHERE s.last_issue_count != h.issue_count
        """,
            (days,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "url": row[0],
                "name": row[1],
                "last_checked": row[2],
                "current_count": row[3],
                "previous_count": row[4],
                "change": row[3] - row[4],
            }
            for row in rows
        ]


def run_monitor_job():
    monitor = ComplianceMonitor()
    results = monitor.check_all_sites()
    logger.info(f"Monitored {len(results)} sites")


def start_scheduler(interval_hours: int = 24):
    monitor = ComplianceMonitor()
    monitor.check_all_sites()

    schedule.every(interval_hours).hours.do(run_monitor_job)

    logger.info(f"Scheduler started. Checking every {interval_hours} hours.")

    while True:
        schedule.run_pending()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            monitor = ComplianceMonitor()
            monitor.check_all_sites()
        elif sys.argv[1] == "status":
            monitor = ComplianceMonitor()
            sites = monitor.get_all_monitored_sites()
            for site in sites:
                print(f"{site['url']}: {site['issue_count']} issues ({site['status']})")
        elif sys.argv[1] == "add" and len(sys.argv) > 2:
            url = sys.argv[2]
            name = sys.argv[3] if len(sys.argv) > 3 else None
            email = sys.argv[4] if len(sys.argv) > 4 else None
            monitor = ComplianceMonitor()
            monitor.add_site(url, name, email)
        elif sys.argv[1] == "remove" and len(sys.argv) > 2:
            monitor = ComplianceMonitor()
            monitor.remove_site(sys.argv[2])
        else:
            print("Usage: python monitor.py [check|status|add|remove] [args]")
    else:
        print("Usage: python monitor.py [check|status|add|remove] [args]")
