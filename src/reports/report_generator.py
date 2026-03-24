"""
Report Generator Module
Generates detailed compliance reports
"""

import json
import os
from datetime import datetime
from typing import Dict, List

from jinja2 import Template


class ReportGenerator:
    def __init__(self):
        self.template_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "templates"
        )

    def generate_summary_report(self, data: Dict) -> str:
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADA Compliance Report - Summary</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ padding: 20px; border-radius: 8px; text-align: center; }}
        .card.high {{ background: #e74c3c; color: white; }}
        .card.medium {{ background: #f39c12; color: white; }}
        .card.low {{ background: #3498db; color: white; }}
        .card.total {{ background: #2c3e50; color: white; }}
        .card-number {{ font-size: 2.5em; font-weight: bold; }}
        .card-label {{ font-size: 0.9em; opacity: 0.9; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
        .badge.high {{ background: #e74c3c; color: white; }}
        .badge.medium {{ background: #f39c12; color: white; }}
        .badge.low {{ background: #3498db; color: white; }}
        .wcag {{ font-family: monospace; background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.85em; text-align: center; }}
        .progress-bar {{ background: #ecf0f1; border-radius: 10px; overflow: hidden; height: 20px; margin: 10px 0; }}
        .progress-fill {{ height: 100%; border-radius: 10px; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ADA Compliance Report</h1>
        <div class="meta">
            <p><strong>Website:</strong> {data.get("url", "N/A")}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
        </div>

        <div class="summary-cards">
            <div class="card total">
                <div class="card-number">{data.get("total_issues", 0)}</div>
                <div class="card-label">Total Issues</div>
            </div>
            <div class="card high">
                <div class="card-number">{data.get("severity_counts", {}).get("High", 0)}</div>
                <div class="card-label">High Priority</div>
            </div>
            <div class="card medium">
                <div class="card-number">{data.get("severity_counts", {}).get("Medium", 0)}</div>
                <div class="card-label">Medium Priority</div>
            </div>
            <div class="card low">
                <div class="card-number">{data.get("severity_counts", {}).get("Low", 0)}</div>
                <div class="card-label">Low Priority</div>
            </div>
        </div>

        <h2>Detailed Issues</h2>
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>WCAG</th>
                    <th>Description</th>
                    <th>Suggestion</th>
                </tr>
            </thead>
            <tbody>
"""

        for issue in data.get("issues", []):
            html += f"""
                <tr>
                    <td><span class="badge {issue["severity"].lower()}">{issue["severity"]}</span></td>
                    <td>{issue["category"]}</td>
                    <td><span class="wcag">{issue["wcag_criterion"]}</span></td>
                    <td>{issue["description"]}</td>
                    <td>{issue["suggestion"]}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>WCAG Criteria Reference</h2>
        <table>
            <thead>
                <tr>
                    <th>Criterion</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><span class="wcag">1.1.1</span></td><td>Non-text Content - All non-text content has text alternative</td></tr>
                <tr><td><span class="wcag">1.3.1</span></td><td>Info and Relationships - Information structure is programmatically determinable</td></tr>
                <tr><td><span class="wcag">1.4.3</span></td><td>Contrast (Minimum) - Text has contrast ratio of at least 4.5:1</td></tr>
                <tr><td><span class="wcag">2.1.1</span></td><td>Keyboard - All functionality available by keyboard</td></tr>
                <tr><td><span class="wcag">2.4.1</span></td><td>Bypass Blocks - Skip navigation links provided</td></tr>
                <tr><td><span class="wcag">2.4.2</span></td><td>Page Titled - Pages have descriptive titles</td></tr>
                <tr><td><span class="wcag">2.4.4</span></td><td>Link Purpose - Link text describes purpose</td></tr>
                <tr><td><span class="wcag">2.4.7</span></td><td>Focus Visible - Keyboard focus is visible</td></tr>
            </tbody>
        </table>

        <div class="footer">
            <p>This report was generated by the ADA Compliance Checker</p>
            <p>For legal matters, please consult with qualified legal counsel</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_progress_report(
        self, history: List[Dict], site_name: str = None
    ) -> str:
        if not history:
            return "<p>No history data available.</p>"

        first_check = history[-1]
        last_check = history[0]

        initial_issues = first_check.get("total_issues", 0)
        current_issues = last_check.get("total_issues", 0)
        improvement = initial_issues - current_issues
        improvement_pct = (
            (improvement / initial_issues * 100) if initial_issues > 0 else 0
        )

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance Progress Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }}
        .progress-summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; font-size: 0.9em; }}
        .chart {{ margin: 30px 0; }}
        .timeline {{ margin: 20px 0; }}
        .timeline-item {{ padding: 15px; border-left: 3px solid #3498db; margin-left: 20px; position: relative; }}
        .timeline-item::before {{ content: ''; width: 12px; height: 12px; background: #3498db; border-radius: 50%; position: absolute; left: -27px; top: 20px; }}
        .timeline-date {{ color: #7f8c8d; font-size: 0.85em; }}
        .timeline-count {{ font-weight: bold; font-size: 1.2em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Compliance Progress Report</h1>
        <p><strong>Site:</strong> {site_name or "Multiple Sites"}</p>
        <p><strong>Period:</strong> {first_check.get("checked_at", "N/A")} to {last_check.get("checked_at", "N/A")}</p>

        <div class="progress-summary">
            <div class="metric">
                <div class="metric-value">{initial_issues}</div>
                <div class="metric-label">Initial Issues</div>
            </div>
            <div class="metric">
                <div class="metric-value">{current_issues}</div>
                <div class="metric-label">Current Issues</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: {"green" if improvement > 0 else "red"}">
                    {"+" if improvement < 0 else ""}{improvement}
                </div>
                <div class="metric-label">{"Improvement" if improvement > 0 else "Change"} ({improvement_pct:.1f}%)</div>
            </div>
        </div>

        <h2>Timeline</h2>
        <div class="timeline">
"""

        for check in reversed(history):
            html += f"""
            <div class="timeline-item">
                <div class="timeline-date">{check.get("checked_at", "N/A")}</div>
                <div class="timeline-count">{check.get("total_issues", 0)} issues</div>
                <div>
                    <small>High: {check.get("high_issues", 0)} | 
                    Medium: {check.get("medium_issues", 0)} | 
                    Low: {check.get("low_issues", 0)}</small>
                </div>
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>
"""
        return html

    def save_report(self, content: str, filename: str, output_dir: str = None) -> str:
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "output", "reports"
            )

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def generate_batch_report(self, results: List[Dict]) -> str:
        total_sites = len(results)
        sites_with_issues = sum(
            1 for r in results if r.get("report", {}).get("total_issues", 0) > 0
        )
        total_issues = sum(r.get("report", {}).get("total_issues", 0) for r in results)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Batch Compliance Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .summary-item {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .summary-value {{ font-size: 1.8em; font-weight: bold; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }}
        .badge.pass {{ background: #27ae60; color: white; }}
        .badge.fail {{ background: #e74c3c; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Batch Compliance Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>

        <div class="summary">
            <div class="summary-item">
                <div class="summary-value">{total_sites}</div>
                <div>Sites Scanned</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{sites_with_issues}</div>
                <div>Sites with Issues</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{total_issues}</div>
                <div>Total Issues</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{total_issues / total_sites if total_sites > 0 else 0:.1f}</div>
                <div>Avg Issues/Site</div>
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

        for result in results:
            url = result.get("url", "N/A")
            report = result.get("report", {})
            total = report.get("total_issues", 0)
            counts = report.get("severity_counts", {})

            html += f"""
                <tr>
                    <td><a href="{url}">{url[:50]}{"..." if len(url) > 50 else ""}</a></td>
                    <td><span class="badge {"fail" if total > 0 else "pass"}">{"Issues Found" if total > 0 else "Pass"}</span></td>
                    <td>{total}</td>
                    <td>{counts.get("High", 0)}</td>
                    <td>{counts.get("Medium", 0)}</td>
                    <td>{counts.get("Low", 0)}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
