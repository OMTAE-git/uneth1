"""
Compliance Monitoring Module
Periodically checks websites for ADA compliance changes with proper error handling and logging.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import schedule
from dotenv import load_dotenv

load_dotenv()

from src.scrapers.compliance_checker import ADAComplianceChecker
from src.reports.report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""

    pass


class SiteNotFoundError(Exception):
    """Custom exception when a site is not found in the database."""

    pass


class ComplianceMonitor:
    """
    Monitors websites for ADA compliance over time.

    Features:
    - Track multiple websites
    - Store compliance history
    - Detect status changes
    - Generate notifications
    - Schedule periodic checks
    """

    def __init__(self, database_path: Optional[str] = None) -> None:
        """
        Initialize the compliance monitor.

        Args:
            database_path: Optional custom database path
        """
        if database_path:
            self.database_path = database_path
        else:
            current_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            self.database_path = os.path.join(current_dir, "data", "compliance.db")

        self.report_generator = ReportGenerator()
        self._initialize_database()

        logger.info(
            f"Initialized ComplianceMonitor with database: {self.database_path}"
        )

    def _get_database_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with row factory.

        Returns:
            SQLite database connection
        """
        try:
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as database_error:
            logger.error(f"Database connection error: {database_error}")
            raise DatabaseError(f"Failed to connect to database: {database_error}")

    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitored_sites (
                    site_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website_url TEXT UNIQUE NOT NULL,
                    site_name TEXT,
                    contact_email TEXT,
                    last_checked_at DATETIME,
                    last_issue_count INTEGER,
                    last_status TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_issue_count INTEGER,
                    high_issue_count INTEGER,
                    medium_issue_count INTEGER,
                    low_issue_count INTEGER,
                    full_report_json TEXT,
                    compliance_status TEXT,
                    FOREIGN KEY (site_id) REFERENCES monitored_sites (site_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notification_type TEXT,
                    message_content TEXT,
                    is_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (site_id) REFERENCES monitored_sites (site_id)
                )
            """)

            connection.commit()
            connection.close()

            logger.info("Database initialized successfully")

        except DatabaseError as database_error:
            logger.error(f"Failed to initialize database: {database_error}")
            raise
        except Exception as unexpected_error:
            logger.error(f"Unexpected error initializing database: {unexpected_error}")
            raise

    def add_site(
        self,
        website_url: str,
        site_name: Optional[str] = None,
        contact_email: Optional[str] = None,
    ) -> int:
        """
        Add a website to the monitoring list.

        Args:
            website_url: URL of the website to monitor
            site_name: Optional name for the site
            contact_email: Optional contact email

        Returns:
            Site ID of the added site
        """
        try:
            logger.info(f"Adding site to monitoring: {website_url}")

            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO monitored_sites 
                (website_url, site_name, contact_email)
                VALUES (?, ?, ?)
            """,
                (website_url, site_name, contact_email),
            )

            site_id = cursor.lastrowid
            connection.commit()
            connection.close()

            logger.info(f"Successfully added site with ID: {site_id}")
            return site_id

        except sqlite3.IntegrityError:
            logger.warning(f"Site already exists: {website_url}")
            return self.get_site_id(website_url)
        except DatabaseError as database_error:
            logger.error(f"Database error adding site: {database_error}")
            raise
        except Exception as unexpected_error:
            logger.error(f"Error adding site: {unexpected_error}")
            raise

    def get_site_id(self, website_url: str) -> int:
        """
        Get the site ID for a website URL.

        Args:
            website_url: URL of the website

        Returns:
            Site ID

        Raises:
            SiteNotFoundError: If site is not found
        """
        try:
            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT site_id FROM monitored_sites WHERE website_url = ?",
                (website_url,),
            )
            result = cursor.fetchone()
            connection.close()

            if result:
                return result["site_id"]
            else:
                raise SiteNotFoundError(f"Site not found: {website_url}")

        except SiteNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting site ID: {e}")
            raise

    def remove_site(self, website_url: str) -> bool:
        """
        Remove a website from monitoring.

        Args:
            website_url: URL of the website to remove

        Returns:
            True if removed, False if not found
        """
        try:
            logger.info(f"Removing site from monitoring: {website_url}")

            connection = self._get_database_connection()
            cursor = connection.cursor()

            site_id = self.get_site_id(website_url)

            cursor.execute(
                "DELETE FROM compliance_history WHERE site_id = ?", (site_id,)
            )
            cursor.execute("DELETE FROM notifications WHERE site_id = ?", (site_id,))
            cursor.execute("DELETE FROM monitored_sites WHERE site_id = ?", (site_id,))

            connection.commit()
            connection.close()

            logger.info(f"Successfully removed site: {website_url}")
            return True

        except SiteNotFoundError:
            logger.warning(f"Site not found for removal: {website_url}")
            return False
        except Exception as e:
            logger.error(f"Error removing site: {e}")
            return False

    def check_single_site(self, website_url: str) -> Optional[Dict[str, Any]]:
        """
        Check a single website for compliance.

        Args:
            website_url: URL of the website to check

        Returns:
            Compliance report dictionary or None if failed
        """
        try:
            logger.info(f"Checking site: {website_url}")

            checker = ADAComplianceChecker(website_url)

            if checker.run_all_checks():
                report = checker.generate_report()

                report_dict = {
                    "url": report.url,
                    "total_issues": report.total_issues,
                    "severity_counts": {
                        "High": report.high_issues,
                        "Medium": report.medium_issues,
                        "Low": report.low_issues,
                    },
                    "issues": report.issues,
                }

                self._save_check_result(website_url, report_dict)
                logger.info(f"Check complete: {report.total_issues} issues found")
                return report_dict
            else:
                logger.warning(f"Failed to check site: {website_url}")
                return None

        except Exception as e:
            logger.error(f"Error checking site {website_url}: {e}")
            return None

    def _save_check_result(self, website_url: str, report: Dict[str, Any]) -> None:
        """
        Save a compliance check result to the database.

        Args:
            website_url: URL of the website
            report: Compliance report dictionary
        """
        try:
            site_id = self.get_site_id(website_url)
            severity_counts = report.get("severity_counts", {})

            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO compliance_history 
                (site_id, total_issue_count, high_issue_count, medium_issue_count, low_issue_count, full_report_json, compliance_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    site_id,
                    report["total_issues"],
                    severity_counts.get("High", 0),
                    severity_counts.get("Medium", 0),
                    severity_counts.get("Low", 0),
                    json.dumps(report),
                    "compliant" if report["total_issues"] == 0 else "non_compliant",
                ),
            )

            cursor.execute(
                """
                UPDATE monitored_sites 
                SET last_checked_at = ?, last_issue_count = ?, last_status = ?
                WHERE site_id = ?
            """,
                (
                    datetime.now(),
                    report["total_issues"],
                    "compliant" if report["total_issues"] == 0 else "non_compliant",
                    site_id,
                ),
            )

            connection.commit()
            connection.close()

            logger.debug(f"Saved check result for site ID: {site_id}")

        except SiteNotFoundError:
            logger.warning(f"Cannot save result - site not registered: {website_url}")
        except Exception as e:
            logger.error(f"Error saving check result: {e}")

    def get_site_history(
        self, website_url: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get compliance history for a site.

        Args:
            website_url: URL of the website
            days: Number of days of history to retrieve

        Returns:
            List of historical check results
        """
        try:
            logger.info(f"Retrieving history for {website_url} (last {days} days)")

            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 
                    s.site_id,
                    s.website_url,
                    h.checked_at,
                    h.total_issue_count,
                    h.high_issue_count,
                    h.medium_issue_count,
                    h.low_issue_count,
                    h.compliance_status
                FROM monitored_sites s
                JOIN compliance_history h ON s.site_id = h.site_id
                WHERE s.website_url = ? 
                AND h.checked_at > datetime('now', '-' || ? || ' days')
                ORDER BY h.checked_at DESC
            """,
                (website_url, days),
            )

            rows = cursor.fetchall()
            connection.close()

            history = [
                {
                    "site_id": row["site_id"],
                    "url": row["website_url"],
                    "checked_at": row["checked_at"],
                    "total_issues": row["total_issue_count"],
                    "high_issues": row["high_issue_count"],
                    "medium_issues": row["medium_issue_count"],
                    "low_issues": row["low_issue_count"],
                    "status": row["compliance_status"],
                }
                for row in rows
            ]

            logger.info(f"Retrieved {len(history)} history records")
            return history

        except Exception as e:
            logger.error(f"Error retrieving site history: {e}")
            return []

    def get_all_monitored_sites(self) -> List[Dict[str, Any]]:
        """
        Get all monitored sites.

        Returns:
            List of monitored site information
        """
        try:
            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT 
                    site_id, 
                    website_url, 
                    site_name, 
                    contact_email, 
                    last_checked_at, 
                    last_issue_count, 
                    last_status
                FROM monitored_sites
                ORDER BY last_checked_at DESC
            """)

            rows = cursor.fetchall()
            connection.close()

            sites = [
                {
                    "site_id": row["site_id"],
                    "url": row["website_url"],
                    "name": row["site_name"],
                    "email": row["contact_email"],
                    "last_checked": row["last_checked_at"],
                    "issue_count": row["last_issue_count"],
                    "status": row["last_status"],
                }
                for row in rows
            ]

            logger.info(f"Retrieved {len(sites)} monitored sites")
            return sites

        except Exception as e:
            logger.error(f"Error retrieving monitored sites: {e}")
            return []

    def check_all_sites(self) -> List[Dict[str, Any]]:
        """
        Check all monitored sites for compliance.

        Returns:
            List of check results for all sites
        """
        try:
            sites = self.get_all_monitored_sites()
            logger.info(f"Checking all {len(sites)} monitored sites")

            results = []
            for site in sites:
                website_url = site["url"]
                report = self.check_single_site(website_url)

                if report:
                    results.append({"url": website_url, "report": report})

            logger.info(f"Completed checks for {len(results)} sites")
            return results

        except Exception as e:
            logger.error(f"Error checking all sites: {e}")
            return []

    def get_status_changes(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get sites with status changes in the specified period.

        Args:
            days: Number of days to look back

        Returns:
            List of sites with status changes
        """
        try:
            connection = self._get_database_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT 
                    s.website_url,
                    s.site_name,
                    s.last_checked_at,
                    s.last_issue_count as current_count,
                    previous_check.issue_count as previous_count
                FROM monitored_sites s
                JOIN (
                    SELECT 
                        site_id, 
                        total_issue_count as issue_count,
                        checked_at
                    FROM compliance_history
                    WHERE checked_at < datetime('now', '-1 days')
                    AND checked_at > datetime('now', '-' || ? || ' days')
                ) previous_check ON s.site_id = previous_check.site_id
                WHERE s.last_issue_count != previous_check.issue_count
            """,
                (days,),
            )

            rows = cursor.fetchall()
            connection.close()

            changes = [
                {
                    "url": row["website_url"],
                    "name": row["site_name"],
                    "last_checked": row["last_checked_at"],
                    "current_count": row["current_count"],
                    "previous_count": row["previous_count"],
                    "change": row["current_count"] - row["previous_count"],
                }
                for row in rows
            ]

            logger.info(f"Found {len(changes)} sites with status changes")
            return changes

        except Exception as e:
            logger.error(f"Error getting status changes: {e}")
            return []


def run_monitor_job() -> None:
    """Job function for scheduled monitoring."""
    try:
        logger.info("Starting scheduled monitoring job")
        monitor = ComplianceMonitor()
        results = monitor.check_all_sites()
        logger.info(f"Scheduled job complete. Checked {len(results)} sites")
    except Exception as e:
        logger.error(f"Error in scheduled monitoring job: {e}")


def start_scheduler(interval_hours: int = 24) -> None:
    """
    Start the monitoring scheduler.

    Args:
        interval_hours: Hours between scheduled checks
    """
    logger.info(f"Starting scheduler with {interval_hours} hour intervals")

    run_monitor_job()
    schedule.every(interval_hours).hours.do(run_monitor_job)

    try:
        while True:
            schedule.run_pending()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


def main() -> None:
    """CLI entry point for the monitor."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python monitor.py [check|status|add|remove] [args]")
        sys.exit(1)

    command = sys.argv[1]
    monitor = ComplianceMonitor()

    try:
        if command == "check" and len(sys.argv) > 2:
            website_url = sys.argv[2]
            result = monitor.check_single_site(website_url)
            if result:
                print(f"Check complete: {result['total_issues']} issues found")
            else:
                print(f"Failed to check {website_url}")

        elif command == "check-all":
            results = monitor.check_all_sites()
            print(f"Checked {len(results)} sites")
            for result in results:
                print(f"  {result['url']}: {result['report']['total_issues']} issues")

        elif command == "status":
            sites = monitor.get_all_monitored_sites()
            if sites:
                print("\nMonitored Sites:")
                for site in sites:
                    status_indicator = "✓" if site["status"] == "compliant" else "✗"
                    print(
                        f"  {status_indicator} {site['url']}: {site['issue_count']} issues"
                    )
            else:
                print("No sites being monitored. Use 'add' to add a site.")

        elif command == "add" and len(sys.argv) > 3:
            website_url = sys.argv[2]
            contact_email = sys.argv[3] if len(sys.argv) > 3 else None
            site_name = sys.argv[4] if len(sys.argv) > 4 else None
            monitor.add_site(website_url, site_name, contact_email)
            print(f"Added {website_url} to monitoring")

        elif command == "remove" and len(sys.argv) > 2:
            website_url = sys.argv[2]
            if monitor.remove_site(website_url):
                print(f"Removed {website_url} from monitoring")
            else:
                print(f"Site not found: {website_url}")

        elif command == "history" and len(sys.argv) > 2:
            website_url = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            history = monitor.get_site_history(website_url, days)
            if history:
                print(f"\nHistory for {website_url} (last {days} days):")
                for check in history:
                    print(f"  {check['checked_at']}: {check['total_issues']} issues")
            else:
                print("No history found for this site.")
        else:
            print("Usage: python monitor.py [check|status|add|remove|history] [args]")

    except Exception as e:
        logger.error(f"Error in monitor CLI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
