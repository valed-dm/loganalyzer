import csv
import io
from typing import Dict

from src.loganalyzer.log_analyzer import LOG_LEVELS


HandlerStats = Dict[str, Dict[str, int]]


class ReportGenerator:
    """Factory class for generating different types of reports from log statistics.

    Provides static methods to generate various formatted reports from processed
    log statistics. Currently, supports:
    - 'handlers': Formatted text table with counts per handler
    - 'csv': Comma-separated values format
    """

    @staticmethod
    def get_report(report_name: str, stats: HandlerStats) -> str:
        """Factory method to generate the requested report type.

        Args:
            report_name: Type of report to generate ('handlers' or 'csv')
            stats: Processed log statistics in {handler: {level: count}} format

        Returns:
            str: Formatted report content as a string

        Raises:
            ValueError: If an unsupported report type is requested
        """
        if report_name == "handlers":
            return ReportGenerator.generate_handlers_report(stats)
        elif report_name == "csv":
            return ReportGenerator.generate_csv_report(stats)
        else:
            raise ValueError(f"Unsupported report type: {report_name}")

    @staticmethod
    def generate_handlers_report(stats: HandlerStats) -> str:
        """Generates a formatted text table report of handler statistics.

        Creates an aligned table showing:
        - Request handlers in first column
        - Log level counts in later columns
        - Header row with level names
        - Footer row with level totals
        - Automatic column width adjustment

        Args:
            stats: Processed log statistics in {handler: {level: count}} format

        Returns:
            str: Formatted table as a string with newlines

        Example Output:
            Total requests: 42
            HANDLER      DEBUG  INFO  WARNING  ERROR  CRITICAL
            /api/users   0      12    3        1      0
            /admin       5      20    0        0      0
                         5      32    3        1      0
        """
        total_requests = 0
        level_totals = dict.fromkeys(LOG_LEVELS, 0)
        rows = []

        for handler in sorted(stats.keys()):
            handler_data = stats[handler]
            row = [handler]
            for level in LOG_LEVELS:
                count = handler_data.get(level, 0)
                row.append(str(count))
                level_totals[level] += count
                total_requests += count
            rows.append(row)

        header = ["HANDLER", *LOG_LEVELS]
        footer = [" "] + [str(level_totals[level]) for level in LOG_LEVELS]

        max_col_widths = [
            max(len(str(item)) for item in col)
            for col in zip(*[header, *rows, footer], strict=False)
        ]

        report_lines = [f"Total requests: {total_requests}\n"]
        header_line = "".join(
            h.ljust(w + 4) for h, w in zip(header, max_col_widths, strict=False)
        )
        report_lines.append(header_line)

        for row in rows:
            row_line = "".join(
                item.ljust(w + 4) for item, w in zip(row, max_col_widths, strict=False)
            )
            report_lines.append(row_line)

        footer_line = "".join(
            item.ljust(w + 4) for item, w in zip(footer, max_col_widths, strict=False)
        )
        report_lines.append(footer_line)

        return "\n".join(report_lines)

    @staticmethod
    def generate_csv_report(stats: HandlerStats) -> str:
        """Generates log statistics in CSV format.

        Creates a comma-separated values report with:
        - Header row: "Handler, DEBUG, INFO, WARNING, ERROR, CRITICAL"
        - Data rows: handler path followed by counts for each log level
        - Proper CSV escaping of values
        - Sorted by handler path alphabetically

        Args:
            stats: Processed log statistics in {handler: {level: count}} format

        Returns:
            str: CSV-formatted string with header row and data rows

        Example Output:
            Handler, DEBUG, INFO, WARNING, ERROR, CRITICAL
            /api/users,0,12,3,1,0
            /admin/login,5,20,0,0,0

        Note:
            Uses standard CSV formatting rules - values containing commas or special
            characters will be properly escaped.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        header = ["HANDLER", *LOG_LEVELS]
        writer.writerow(header)

        for handler in sorted(stats.keys()):
            handler_data = stats[handler]
            row = [handler]
            for level in LOG_LEVELS:
                row.append(str(handler_data.get(level, 0)))
            writer.writerow(row)

        return output.getvalue()
