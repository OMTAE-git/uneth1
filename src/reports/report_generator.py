"""
Report Generator Module
Generates detailed compliance reports with proper error handling and logging.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Template, TemplateError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReportGenerationError(Exception):
    """Custom exception for report generation errors."""

    pass


class ReportGenerator:
    """
    Generates comprehensive ADA compliance reports.

    Supports:
    - Summary reports for single sites
    - Progress reports over time
    - Batch reports for multiple sites
    - HTML output format
    """

    def __init__(self, templates_directory: Optional[str] = None) -> None:
        """
        Initialize the report generator.

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

        logger.info(
            f"Initialized ReportGenerator with templates from: {self.templates_dir}"
        )

    def generate_summary_report(self, compliance_data: Dict[str, Any]) -> str:
        """
        Generate a summary compliance report in HTML format.

        Args:
            compliance_data: Dictionary containing compliance check results

        Returns:
            HTML string of the summary report
        """
        try:
            logger.info(
                f"Generating summary report for: {compliance_data.get('url', 'Unknown')}"
            )

            website_url = compliance_data.get("url", "N/A")
            total_issues = compliance_data.get("total_issues", 0)
            severity_counts = compliance_data.get("severity_counts", {})
            compliance_issues = compliance_data.get("issues", [])

            high_count = severity_counts.get("High", 0)
            medium_count = severity_counts.get("Medium", 0)
            low_count = severity_counts.get("Low", 0)

            compliance_score = self._calculate_compliance_score(
                high_count, medium_count, low_count
            )

            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADA Compliance Report - Summary</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .report-card {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 20px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; }}
        .meta-info {{ color: #7f8c8d; font-size: 0.95em; margin-bottom: 25px; }}
        .meta-info p {{ margin: 5px 0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 25px 0; }}
        .metric-card {{ padding: 25px; border-radius: 8px; text-align: center; color: white; }}
        .metric-card.total {{ background: linear-gradient(135deg, #2c3e50, #34495e); }}
        .metric-card.high {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
        .metric-card.medium {{ background: linear-gradient(135deg, #f39c12, #d68910); }}
        .metric-card.low {{ background: linear-gradient(135deg, #3498db, #2980b9); }}
        .metric-card.score {{ background: linear-gradient(135deg, #27ae60, #229954); }}
        .metric-value {{ font-size: 3em; font-weight: bold; margin-bottom: 5px; }}
        .metric-label {{ font-size: 0.9em; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; }}
        .issues-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .issues-table th {{ background: #34495e; color: white; padding: 15px; text-align: left; font-weight: 600; }}
        .issues-table td {{ padding: 12px 15px; border-bottom: 1px solid #ecf0f1; }}
        .issues-table tr:hover {{ background: #f8f9fa; }}
        .issues-table tr:last-child td {{ border-bottom: none; }}
        .severity-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.85em; font-weight: bold; color: white; }}
        .severity-badge.high {{ background: #e74c3c; }}
        .severity-badge.medium {{ background: #f39c12; }}
        .severity-badge.low {{ background: #3498db; }}
        .wcag-code {{ font-family: 'Courier New', monospace; background: #ecf0f1; padding: 3px 8px; border-radius: 3px; font-size: 0.9em; color: #2c3e50; }}
        .suggestion {{ color: #27ae60; font-style: italic; }}
        .progress-container {{ margin: 30px 0; }}
        .progress-bar {{ background: #ecf0f1; border-radius: 10px; overflow: hidden; height: 25px; }}
        .progress-fill {{ height: 100%; border-radius: 10px; transition: width 0.5s ease; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.85em; text-align: center; }}
        .no-issues {{ text-align: center; padding: 40px; background: #d4edda; color: #155724; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-card">
            <h1>ADA Compliance Report</h1>
            <div class="meta-info">
                <p><strong>Website:</strong> <a href="{website_url}">{website_url}</a></p>
                <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
                <p><strong>Report ID:</strong> {datetime.now().strftime("%Y%m%d%H%M%S")}</p>
            </div>

            <div class="summary-grid">
                <div class="metric-card total">
                    <div class="metric-value">{total_issues}</div>
                    <div class="metric-label">Total Issues</div>
                </div>
                <div class="metric-card high">
                    <div class="metric-value">{high_count}</div>
                    <div class="metric-label">High Priority</div>
                </div>
                <div class="metric-card medium">
                    <div class="metric-value">{medium_count}</div>
                    <div class="metric-label">Medium Priority</div>
                </div>
                <div class="metric-card low">
                    <div class="metric-value">{low_count}</div>
                    <div class="metric-label">Low Priority</div>
                </div>
                <div class="metric-card score">
                    <div class="metric-value">{compliance_score}%</div>
                    <div class="metric-label">Compliance Score</div>
                </div>
            </div>

            <div class="progress-container">
                <h3>Issue Distribution</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {self._calculate_percentage(high_count, total_issues)}%; background: #e74c3c;"></div>
                    <div class="progress-fill" style="width: {self._calculate_percentage(medium_count, total_issues)}%; background: #f39c12;"></div>
                    <div class="progress-fill" style="width: {self._calculate_percentage(low_count, total_issues)}%; background: #3498db;"></div>
                </div>
                <p style="margin-top: 10px; font-size: 0.85em; color: #7f8c8d;">
                    High: {self._calculate_percentage(high_count, total_issues)}% | 
                    Medium: {self._calculate_percentage(medium_count, total_issues)}% | 
                    Low: {self._calculate_percentage(low_count, total_issues)}%
                </p>
            </div>

            <h2>Detailed Issues</h2>
"""

            if compliance_issues:
                html_content += """
            <table class="issues-table">
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>Category</th>
                        <th>WCAG</th>
                        <th>Description</th>
                        <th>Suggested Fix</th>
                    </tr>
                </thead>
                <tbody>
"""
                for issue in compliance_issues:
                    severity_class = issue.get("severity", "low").lower()
                    html_content += f"""
                    <tr>
                        <td><span class="severity-badge {severity_class}">{issue.get("severity", "N/A")}</span></td>
                        <td>{issue.get("category", "N/A")}</td>
                        <td><span class="wcag-code">{issue.get("wcag_criterion", "N/A")}</span></td>
                        <td>{issue.get("description", "N/A")}</td>
                        <td class="suggestion">{issue.get("suggestion", "N/A")}</td>
                    </tr>
"""
                html_content += """
                </tbody>
            </table>
"""
            else:
                html_content += """
            <div class="no-issues">
                <h3>No Issues Found!</h3>
                <p>This website appears to be compliant with ADA accessibility standards.</p>
            </div>
"""

            html_content += """
            <h2>WCAG Criteria Reference</h2>
            <table class="issues-table">
                <thead>
                    <tr>
                        <th>Criterion</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td><span class="wcag-code">1.1.1</span></td><td>Non-text Content - All non-text content has text alternative</td></tr>
                    <tr><td><span class="wcag-code">1.3.1</span></td><td>Info and Relationships - Information structure is programmatically determinable</td></tr>
                    <tr><td><span class="wcag-code">1.4.3</span></td><td>Contrast (Minimum) - Text has contrast ratio of at least 4.5:1</td></tr>
                    <tr><td><span class="wcag-code">2.1.1</span></td><td>Keyboard - All functionality available by keyboard</td></tr>
                    <tr><td><span class="wcag-code">2.4.1</span></td><td>Bypass Blocks - Skip navigation links provided</td></tr>
                    <tr><td><span class="wcag-code">2.4.2</span></td><td>Page Titled - Pages have descriptive titles</td></tr>
                    <tr><td><span class="wcag-code">2.4.4</span></td><td>Link Purpose - Link text describes purpose</td></tr>
                    <tr><td><span class="wcag-code">2.4.7</span></td><td>Focus Visible - Keyboard focus is visible</td></tr>
                </tbody>
            </table>

            <div class="footer">
                <p>This report was generated by the ADA Compliance Checker</p>
                <p>For legal matters, please consult with qualified legal counsel</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

            logger.info("Summary report generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise ReportGenerationError(f"Failed to generate summary report: {e}")

    def generate_progress_report(
        self, history_data: List[Dict[str, Any]], site_identifier: Optional[str] = None
    ) -> str:
        """
        Generate a progress report showing compliance changes over time.

        Args:
            history_data: List of historical compliance check results
            site_identifier: Optional site name or URL for the report header

        Returns:
            HTML string of the progress report
        """
        try:
            logger.info(
                f"Generating progress report for: {site_identifier or 'Multiple Sites'}"
            )

            if not history_data:
                return "<p>No history data available.</p>"

            earliest_check = history_data[-1]
            latest_check = history_data[0]

            initial_issues = earliest_check.get("total_issues", 0)
            current_issues = latest_check.get("total_issues", 0)
            issue_difference = initial_issues - current_issues
            improvement_percentage = (
                (issue_difference / initial_issues * 100) if initial_issues > 0 else 0
            )

            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance Progress Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .subtitle {{ color: #7f8c8d; margin-bottom: 30px; }}
        .progress-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0; }}
        .progress-metric {{ background: #f8f9fa; padding: 25px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }}
        .improvement {{ color: #27ae60; }}
        .regression {{ color: #e74c3c; }}
        .timeline {{ margin: 30px 0; position: relative; padding-left: 30px; }}
        .timeline::before {{ content: ''; position: absolute; left: 10px; top: 0; bottom: 0; width: 3px; background: #3498db; }}
        .timeline-entry {{ position: relative; margin-bottom: 25px; padding: 15px 20px; background: #f8f9fa; border-radius: 8px; }}
        .timeline-entry::before {{ content: ''; position: absolute; left: -24px; top: 20px; width: 12px; height: 12px; background: #3498db; border-radius: 50%; border: 3px solid white; }}
        .timeline-date {{ color: #7f8c8d; font-size: 0.85em; }}
        .timeline-issues {{ font-size: 1.3em; font-weight: bold; margin: 5px 0; }}
        .timeline-breakdown {{ font-size: 0.85em; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Compliance Progress Report</h1>
        <div class="subtitle">
            <p><strong>Site:</strong> {site_identifier or "Multiple Sites"}</p>
            <p><strong>Period:</strong> {earliest_check.get("checked_at", "N/A")} to {latest_check.get("checked_at", "N/A")}</p>
            <p><strong>Total Checks:</strong> {len(history_data)}</p>
        </div>

        <div class="progress-grid">
            <div class="progress-metric">
                <div class="metric-value">{initial_issues}</div>
                <div class="metric-label">Initial Issues</div>
            </div>
            <div class="progress-metric">
                <div class="metric-value">{current_issues}</div>
                <div class="metric-label">Current Issues</div>
            </div>
            <div class="progress-metric">
                <div class="metric-value {"improvement" if issue_difference > 0 else "regression"}">
                    {"+" if issue_difference < 0 else ""}{issue_difference}
                </div>
                <div class="metric-label">Change ({improvement_percentage:.1f}% {"improved" if improvement_percentage > 0 else "change"})</div>
            </div>
        </div>

        <h2>Compliance Timeline</h2>
        <div class="timeline">
"""

            for check in reversed(history_data):
                issue_count = check.get("total_issues", 0)
                check_date = check.get("checked_at", "N/A")
                high_issues = check.get("high_issues", 0)
                medium_issues = check.get("medium_issues", 0)
                low_issues = check.get("low_issues", 0)

                html_content += f"""
            <div class="timeline-entry">
                <div class="timeline-date">{check_date}</div>
                <div class="timeline-issues">{issue_count} issues</div>
                <div class="timeline-breakdown">
                    High: {high_issues} | Medium: {medium_issues} | Low: {low_issues}
                </div>
            </div>
"""

            html_content += """
        </div>
    </div>
</body>
</html>
"""

            logger.info("Progress report generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            raise ReportGenerationError(f"Failed to generate progress report: {e}")

    def generate_batch_report(self, batch_results: List[Dict[str, Any]]) -> str:
        """
        Generate a batch report for multiple sites.

        Args:
            batch_results: List of site check results

        Returns:
            HTML string of the batch report
        """
        try:
            logger.info(f"Generating batch report for {len(batch_results)} sites")

            total_sites = len(batch_results)
            sites_with_issues = sum(
                1
                for result in batch_results
                if result.get("report", {}).get("total_issues", 0) > 0
            )
            sites_compliant = total_sites - sites_with_issues
            total_issues = sum(
                result.get("report", {}).get("total_issues", 0)
                for result in batch_results
            )
            average_issues = total_issues / total_sites if total_sites > 0 else 0

            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Batch Compliance Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 25px 0; }}
        .summary-item {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .summary-label {{ color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .status-badge {{ display: inline-block; padding: 5px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
        .status-badge.pass {{ background: #27ae60; color: white; }}
        .status-badge.fail {{ background: #e74c3c; color: white; }}
        .severity-cell {{ font-size: 0.9em; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.85em; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Batch Compliance Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>

        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-value">{total_sites}</div>
                <div class="summary-label">Sites Scanned</div>
            </div>
            <div class="summary-item">
                <div class="summary-value" style="color: #e74c3c;">{sites_with_issues}</div>
                <div class="summary-label">Non-Compliant</div>
            </div>
            <div class="summary-item">
                <div class="summary-value" style="color: #27ae60;">{sites_compliant}</div>
                <div class="summary-label">Compliant</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{average_issues:.1f}</div>
                <div class="summary-label">Avg Issues/Site</div>
            </div>
        </div>

        <h2>Results by Site</h2>
        <table>
            <thead>
                <tr>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Total</th>
                    <th>High</th>
                    <th>Medium</th>
                    <th>Low</th>
                </tr>
            </thead>
            <tbody>
"""

            for result in batch_results:
                website_url = result.get("url", "N/A")
                report = result.get("report", {})
                total = report.get("total_issues", 0)
                counts = report.get("severity_counts", {})

                status_class = "pass" if total == 0 else "fail"
                status_text = "Compliant" if total == 0 else "Issues Found"

                truncated_url = (
                    website_url[:50] + "..." if len(website_url) > 50 else website_url
                )

                html_content += f"""
                <tr>
                    <td><a href="{website_url}" title="{website_url}">{truncated_url}</a></td>
                    <td><span class="status-badge {status_class}">{status_text}</span></td>
                    <td><strong>{total}</strong></td>
                    <td class="severity-cell" style="color: #e74c3c;">{counts.get("High", 0)}</td>
                    <td class="severity-cell" style="color: #f39c12;">{counts.get("Medium", 0)}</td>
                    <td class="severity-cell" style="color: #3498db;">{counts.get("Low", 0)}</td>
                </tr>
"""

            html_content += """
            </tbody>
        </table>

        <div class="footer">
            <p>This batch report was generated by the ADA Compliance Checker</p>
        </div>
    </div>
</body>
</html>
"""

            logger.info("Batch report generated successfully")
            return html_content

        except Exception as e:
            logger.error(f"Error generating batch report: {e}")
            raise ReportGenerationError(f"Failed to generate batch report: {e}")

    def save_report(
        self, report_content: str, filename: str, output_directory: Optional[str] = None
    ) -> str:
        """
        Save a report to file.

        Args:
            report_content: HTML content of the report
            filename: Name of the output file
            output_directory: Optional output directory path

        Returns:
            Full path to the saved report
        """
        try:
            if output_directory is None:
                output_directory = os.path.join(
                    os.path.dirname(__file__), "..", "..", "output", "reports"
                )

            os.makedirs(output_directory, exist_ok=True)
            filepath = os.path.join(output_directory, filename)

            with open(filepath, "w", encoding="utf-8") as output_file:
                output_file.write(report_content)

            logger.info(f"Saved report to: {filepath}")
            return filepath

        except IOError as file_error:
            logger.error(f"Failed to save report: {file_error}")
            raise ReportGenerationError(f"Failed to save report: {file_error}")
        except Exception as unexpected_error:
            logger.error(f"Unexpected error saving report: {unexpected_error}")
            raise

    def _calculate_compliance_score(
        self, high_issues: int, medium_issues: int, low_issues: int
    ) -> int:
        """
        Calculate a compliance score based on issue counts.

        Args:
            high_issues: Number of high severity issues
            medium_issues: Number of medium severity issues
            low_issues: Number of low severity issues

        Returns:
            Compliance score (0-100)
        """
        total_issues = high_issues + medium_issues + low_issues

        if total_issues == 0:
            return 100

        penalty = (high_issues * 10) + (medium_issues * 5) + (low_issues * 2)
        score = max(0, 100 - penalty)

        return score

    def _calculate_percentage(self, part: int, total: int) -> float:
        """
        Calculate percentage with zero division handling.

        Args:
            part: The part value
            total: The total value

        Returns:
            Percentage as float
        """
        if total == 0:
            return 0.0
        return (part / total) * 100
