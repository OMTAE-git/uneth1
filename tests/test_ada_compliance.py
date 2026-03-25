"""
Unit tests for the ADA Compliance Suite
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.compliance_checker import ADAComplianceChecker, ComplianceReport
from src.letters.letter_generator import LetterGenerator
from src.monitoring.monitor import ComplianceMonitor
from src.reports.report_generator import ReportGenerator


class TestComplianceChecker:
    """Tests for ADAComplianceChecker class."""

    @pytest.fixture
    def checker(self):
        return ADAComplianceChecker("https://example.com")

    def test_checker_initialization(self, checker):
        assert checker.target_url == "https://example.com"
        assert checker.issues == []

    def test_report_class(self):
        report = ComplianceReport(
            url="https://test.com",
            total_issues=5,
            high_issues=2,
            medium_issues=2,
            low_issues=1,
            issues=[],
        )
        assert report.url == "https://test.com"
        assert report.total_issues == 5
        assert report.high_issues == 2

    @patch("src.scrapers.compliance_checker.requests.get")
    def test_fetch_page_success(self, mock_get, checker):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response

        result = checker.fetch_webpage()
        assert result is True
        assert checker.html_content == mock_response.text

    @patch("src.scrapers.compliance_checker.requests.get")
    def test_fetch_page_failure(self, mock_get, checker):
        mock_get.side_effect = Exception("Network error")
        result = checker.fetch_webpage()
        assert result is False


class TestLetterGenerator:
    """Tests for LetterGenerator class."""

    @pytest.fixture
    def generator(self):
        return LetterGenerator()

    def test_generator_initialization(self, generator):
        assert generator.templates_dir is not None
        assert os.path.exists(generator.templates_dir)

    def test_generate_text_letter(self, generator):
        letter = generator.generate_text_letter(
            recipient_name="Test Business",
            recipient_email="test@example.com",
            website_url="https://example.com",
            compliance_issues=[
                {
                    "severity": "High",
                    "category": "Images",
                    "wcag_criterion": "1.1.1",
                    "description": "Missing alt text",
                    "suggestion": "Add alt attributes",
                }
            ],
        )
        assert "Test Business" in letter
        assert "https://example.com" in letter
        assert "ADA" in letter

    def test_generate_html_letter(self, generator):
        letter = generator.generate_html_letter(
            recipient_name="Test Business",
            recipient_email="test@example.com",
            website_url="https://example.com",
            compliance_issues=[
                {
                    "severity": "High",
                    "description": "Missing alt text",
                    "suggestion": "Add alt attributes",
                }
            ],
            sender_name="Compliance Team",
            sender_email="compliance@test.com",
        )
        assert "<html>" in letter
        assert "Test Business" in letter

    def test_save_letter(self, generator):
        content = "<html><body>Test</body></html>"
        filepath = generator.save_letter(content, "test_letter.html")
        assert os.path.exists(filepath)
        with open(filepath) as f:
            assert f.read() == content
        os.remove(filepath)


class TestComplianceMonitor:
    """Tests for ComplianceMonitor class."""

    @pytest.fixture
    def monitor(self, tmp_path):
        db_path = str(tmp_path / "test_compliance.db")
        return ComplianceMonitor(database_path=db_path)

    def test_monitor_initialization(self, monitor):
        assert monitor.database_path is not None

    def test_add_site(self, monitor):
        site_id = monitor.add_site("https://test.com", "Test Site", "test@example.com")
        assert site_id > 0

    def test_get_site_id(self, monitor):
        monitor.add_site("https://unique-test.com")
        site_id = monitor.get_site_id("https://unique-test.com")
        assert isinstance(site_id, int)

    def test_get_all_monitored_sites(self, monitor):
        monitor.add_site("https://site1.com")
        monitor.add_site("https://site2.com")
        sites = monitor.get_all_monitored_sites()
        assert len(sites) >= 2

    def test_remove_site(self, monitor):
        monitor.add_site("https://to-remove.com")
        result = monitor.remove_site("https://to-remove.com")
        assert result is True

    def test_remove_nonexistent_site(self, monitor):
        result = monitor.remove_site("https://does-not-exist.com")
        assert result is False


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_generator_initialization(self, generator):
        assert generator.templates_dir is not None

    def test_generate_summary_report(self, generator):
        report_data = {
            "url": "https://example.com",
            "total_issues": 5,
            "severity_counts": {"High": 2, "Medium": 2, "Low": 1},
            "issues": [],
        }
        html = generator.generate_summary_report(report_data)
        assert "example.com" in html
        assert "5" in html

    def test_generate_batch_report(self, generator):
        results = [
            {"url": "https://site1.com", "report": {"total_issues": 3}},
            {"url": "https://site2.com", "report": {"total_issues": 0}},
        ]
        html = generator.generate_batch_report(results)
        assert "site1.com" in html
        assert "site2.com" in html

    def test_save_report(self, generator):
        html = "<html><body>Test Report</body></html>"
        filepath = generator.save_report(html, "test_report.html")
        assert os.path.exists(filepath)
        os.remove(filepath)


class TestAutonomousEngine:
    """Tests for AutonomousEngine class."""

    @pytest.fixture
    def engine(self):
        with patch("src.autonomous_engine.ComplianceMonitor"):
            with patch("src.autonomous_engine.LetterGenerator"):
                from src.autonomous_engine import AutonomousEngine

                return AutonomousEngine()

    def test_extract_domain(self, engine):
        domain = engine._extract_domain("https://www.example.com/page")
        assert domain == "example.com"

    def test_extract_domain_no_www(self, engine):
        domain = engine._extract_domain("https://subdomain.example.com/")
        assert domain == "subdomain.example.com"

    def test_stats_initialization(self, engine):
        assert engine.stats["sites_scanned"] == 0
        assert engine.stats["non_compliant"] == 0
        assert engine.stats["letters_generated"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
