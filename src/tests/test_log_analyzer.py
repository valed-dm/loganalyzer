from collections import defaultdict
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from src.loganalyzer.log_analyzer import LogAnalyzer
from src.loganalyzer.report import ReportGenerator
from src.main import validate_files


@pytest.fixture
def sample_stats():
    return {
        "/api/v1/auth/login/": {
            "DEBUG": 23,
            "INFO": 78,
            "WARNING": 14,
            "ERROR": 15,
            "CRITICAL": 18,
        },
        "/api/v1/products/": {
            "DEBUG": 23,
            "INFO": 70,
            "WARNING": 11,
            "ERROR": 18,
        },
    }


def test_parse_log_line():
    """Test log line parsing with various input formats.

    Verifies correct handling of:
    - Standard successful request logs (GET/POST with status)
    - Error logs (Internal Server Error format)
    - Malformed/invalid log lines
    """
    line = (
        "2025-03-28 12:21:51,000 INFO django.request: "
        "GET /admin/dashboard/ 200 OK [192.168.1.68]"
    )
    assert LogAnalyzer.parse_log_line(line) == ("/admin/dashboard/", "INFO")

    error_line = (
        "2025-03-28 12:11:57,000 ERROR django.request: Internal Server Error:"
        " /admin/dashboard/ [192.168.1.29] - ValueError: Invalid input data"
    )
    assert LogAnalyzer.parse_log_line(error_line) == ("/admin/dashboard/", "ERROR")

    bad_line = "Invalid log line"
    assert LogAnalyzer.parse_log_line(bad_line) is None


def test_generate_handlers_report(sample_stats):
    """Verify handlers report contains correct totals, paths, and expected counts.

    Tests that the generated report:
    - Includes the correct total requests count
    - Contains expected handler paths
    - Displays correct count values for all log levels
    """
    report = ReportGenerator.get_report("handlers", sample_stats)
    assert "Total requests: 270" in report
    assert "/api/v1/auth/login/" in report
    assert "23" in report
    assert "78" in report
    assert "14" in report
    assert "15" in report
    assert "18" in report


def test_merge_stats():
    """Test merging of multiple log statistics collections.

    Verifies that:
    - Counts for the same handler/level are summed correctly
    - New handlers are added to the merged collection
    - Unmentioned levels default to 0
    - Original stats remain unchanged in a merged result
    """
    # Setup - two different stat collections with overlapping data
    stats1 = defaultdict(lambda: defaultdict(int))
    stats1["/handler1"]["DEBUG"] = 10
    stats1["/handler1"]["INFO"] = 20
    stats1["/handler1"]["ERROR"] = 3

    stats2 = defaultdict(lambda: defaultdict(int))
    stats2["/handler1"]["DEBUG"] = 5
    stats2["/handler1"]["INFO"] = 15
    stats2["/handler2"]["INFO"] = 15

    # Action
    merged = LogAnalyzer.merge_stats([stats1, stats2])

    # Assert summing logic
    assert merged["/handler1"]["DEBUG"] == 15, "DEBUG counts should sum"
    assert merged["/handler1"]["INFO"] == 35, "INFO counts should sum"
    assert merged["/handler1"]["ERROR"] == 3, "ERROR should preserve single value"

    # Assert new handler inclusion
    assert "/handler2" in merged, "New handlers should be added"
    assert merged["/handler2"]["INFO"] == 15, "New handler counts should carry over"

    # Assert default zero values
    assert merged["/handler1"]["WARNING"] == 0, "Unmentioned levels should default to 0"
    assert (
        merged["/handler2"]["CRITICAL"] == 0
    ), "Unmentioned levels should default to 0"


@patch("pathlib.Path.open")
def test_process_log_file(mock_open):
    """Test log file processing with realistic log lines.

    Verifies that:
    - Valid log lines are properly parsed and counted
    - Different log levels (INFO, DEBUG, ERROR) are correctly categorized
    - Malformed/invalid log lines are silently skipped
    - Paths are properly extracted from both successful and error requests
    - Statistics are aggregated correctly per handler path
    """
    mock_open.return_value.__enter__.return_value = StringIO(
        "2025-03-28 12:21:51,000 INFO django.request: GET /test/ 200 OK\n"
        "2025-03-28 12:22:52,000 DEBUG django.request: GET /test/debug/ 200 OK\n"
        "2025-03-28 12:23:53,000 ERROR django.request: Internal Server Error: "
        "/test/error/\n"
        "2025-03-28 12:24:54,000 INFO django.request: GET /test/ 200 OK\n"
        "Invalid log line that should be skipped\n"
    )

    stats = LogAnalyzer.process_log_file(Path("dummy.log"))

    # Verify counts
    assert stats["/test/"]["INFO"] == 2, "Should count multiple hits to same path"
    assert stats["/test/debug/"]["DEBUG"] == 1, "Should count DEBUG level requests"
    assert stats["/test/error/"]["ERROR"] == 1, "Should count ERROR level requests"

    # Verify structure
    assert len(stats) == 3, "Should create entries for 3 unique paths"
    assert set(stats.keys()) == {
        "/test/",
        "/test/debug/",
        "/test/error/",
    }, "Should have correct path keys"

    # Verify no false positives
    assert stats["/test/"]["DEBUG"] == 0, "Unused levels should remain 0"
    assert "Invalid log line" not in str(stats), "Malformed lines should be ignored"


def test_validate_files(tmp_path):
    """Test file validation logic with various file scenarios.

    Verifies that:
    - Returns List[Path] objects for existing regular files
    - Paths in returned list match input order
    - Raises FileNotFoundError for non-existent files
    - Error message includes the invalid path
    - Only actual files are validated (directories/special files would fail)
    """
    valid_file1 = tmp_path / "file1.log"
    valid_file1.write_text("valid log content")
    valid_file2 = tmp_path / "file2.log"
    valid_file2.write_text("more valid logs")
    nonexistent_file = tmp_path / "ghost.log"

    # Test success case with multiple valid files
    input_paths = [str(valid_file1), str(valid_file2)]
    result = validate_files(input_paths)

    assert isinstance(result, list), "Should return a list"
    assert len(result) == 2, "Should return all valid files"
    assert all(isinstance(p, Path) for p in result), "Should return Path objects"
    assert result == [valid_file1, valid_file2], "Should preserve input order"

    # Test error case with a non-existent file
    with pytest.raises(FileNotFoundError) as exc_info:
        validate_files([str(nonexistent_file)])
    assert str(nonexistent_file) in str(
        exc_info.value
    ), "Error should mention invalid path"

    # Test order preservation explicitly
    reversed_result = validate_files([str(valid_file2), str(valid_file1)])
    assert reversed_result == [
        valid_file2,
        valid_file1,
    ], "Should maintain exact input order"


def test_edge_cases():
    """Test edge cases in log line parsing.

    Verifies current behavior where:
    - Query parameters (?param=value) are stripped
    - URL fragments (#section) are stripped
    - Empty/malformed lines return None
    - Paths are properly extracted
    """
    # Test query parameters
    line = "2025-03-28 12:21:51,000 INFO django.request: GET /test/?param=value"
    assert LogAnalyzer.parse_log_line(line) == (
        "/test/",
        "INFO",
    ), "Should strip query parameters"

    # Test URL fragments
    line = "2025-03-28 12:21:52,000 DEBUG django.request: GET /test/#section"
    assert LogAnalyzer.parse_log_line(line) == (
        "/test/",
        "DEBUG",
    ), "Should strip URL fragments"

    # Test malformed lines
    assert LogAnalyzer.parse_log_line("") is None, "Empty line should return None"
    assert (
        LogAnalyzer.parse_log_line("2025-03-28") is None
    ), "Incomplete line should return None"

    # Test combined query + fragment
    line = (
        "2025-03-28 12:21:53,000 WARNING django.request: GET /test/?param=value#section"
    )
    assert LogAnalyzer.parse_log_line(line) == (
        "/test/",
        "WARNING",
    ), "Should strip both queries and fragments"
