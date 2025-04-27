from pathlib import Path
from typing import List

from src.loganalyzer.log_analyzer import LogAnalyzer
from src.loganalyzer.report import HandlerStats
from src.loganalyzer.report import ReportGenerator
from src.utils.pool import cpu_pool


def process_single_file(file_path: Path) -> HandlerStats:
    """
    Process a single log file and return collected statistics.

    Args:
        file_path (Path): Path to the log file.

    Returns:
        HandlerStats: Statistics grouped by handler and log level.
    """
    return LogAnalyzer.process_log_file(file_path)


def detect_levels_mode(valid_files: List[Path]) -> None:
    """Detect and print all log levels found in the provided log files."""
    levels = LogAnalyzer.detect_all_levels(valid_files)
    print(f"Found log levels in django.request: {sorted(levels)}")


def generate_report(valid_files: List[Path], report_type: str) -> str:
    """Generate a report from valid log files based on the selected report type."""
    with cpu_pool() as pool:
        stats_list = pool.map(process_single_file, valid_files)
    merged_stats = LogAnalyzer.merge_stats(stats_list)
    return ReportGenerator.get_report(report_type, merged_stats)
