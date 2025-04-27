import argparse


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser for the log analyzer.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Analyze Django application logs and generate reports."
    )
    parser.add_argument("log_files", nargs="+", help="Paths to log files to analyze.")
    parser.add_argument(
        "--report",
        choices=["handlers", "levels", "csv"],
        default="handlers",
        help="Type of report to generate (default: handlers).",
    )
    parser.add_argument("--output", type=str, help="Optional output file path.")
    parser.add_argument(
        "--detect-levels",
        action="store_true",
        help="Detect all log levels present in django.request logs.",
    )
    return parser
