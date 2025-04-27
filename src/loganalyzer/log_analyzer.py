from collections import defaultdict
from pathlib import Path
from typing import DefaultDict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def new_default_int() -> DefaultDict[str, int]:
    """Creates a new defaultdict with int as default factory.

    Returns:
        DefaultDict[str, int]: A defaultdict that automatically creates int entries (0)
        for missing keys.
    """
    return defaultdict(int)


def new_default_stats() -> DefaultDict[str, DefaultDict[str, int]]:
    """Creates a nested defaultdict structure for log statistics.

    Returns:
        DefaultDict[str, DefaultDict[str, int]]: A two-level defaultdict where both
        levels automatically create int entries (0) for missing keys, suitable for
        counting log levels per handler.
    """
    return defaultdict(new_default_int)


class LogAnalyzer:
    """Main class for log analysis operations."""

    @staticmethod
    def parse_log_line(line: str) -> Optional[Tuple[str, str]]:
        """Parses Django request logs, extracting path and log level.

        Handles:
        - GET/POST/etc. requests → `/path?param=value#section` → `/path`
        - Internal Server Errors → `/error_path#frag` → `/error_path`
        - Returns `None` for invalid/malformed lines.
        """
        try:
            parts = line.strip().split()
            if len(parts) >= 6 and parts[3] == "django.request:":
                level = parts[2].upper()
                if parts[4] in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                    return parts[5].split("?")[0].split("#")[0], level
                elif parts[4:7] == ["Internal", "Server", "Error:"]:
                    return parts[7].split("[")[0].rstrip(":").split("#")[0], level
        except (IndexError, ValueError):
            pass
        return None

    @staticmethod
    def process_log_file(file_path: Path) -> DefaultDict[str, DefaultDict[str, int]]:
        """Processes a log file and counts log levels per request handler.

        Parses a Django request log file, counting occurrences of each log level
        (DEBUG, INFO, WARNING, etc.) for each request handler path. Automatically
        handles different file encodings (UTF-8 and Latin-1).

        Args:
            file_path: Path to the log file to process

        Returns:
            Nested defaultdict structure where:
            - First level keys are request handler paths
            - Second level keys are log levels (str)
            - Values are counts (int) of each log level per handler
        """
        stats = new_default_stats()
        encodings = ["utf-8", "latin-1"]

        for encoding in encodings:
            try:
                with file_path.open("r", encoding=encoding) as f:
                    for line in f:
                        parsed = LogAnalyzer.parse_log_line(line)
                        if parsed:
                            path, level = parsed
                            stats[path][level] += 1
                break
            except UnicodeDecodeError:
                continue

        return stats

    @staticmethod
    def merge_stats(
        stats_list: List[DefaultDict[str, DefaultDict[str, int]]],
    ) -> DefaultDict[str, DefaultDict[str, int]]:
        """Merges multiple log statistics collections into a single combined view.

        Combines counts from multiple log analysis runs (typically from different files)
        into aggregated statistics. Preserves the same nested defaultdict structure
        as individual statistics collections.

        Args:
            stats_list: List of statistics collections to merge, where each collection
                follows the {handler: {level: count}} structure

        Returns:
            Combined statistics in the same nested defaultdict format, with:
            - Outer keys: request handler paths
            - Inner keys: log levels (DEBUG, INFO, etc.)
            - Values: Summed counts across all input collections
        """
        merged: DefaultDict[str, DefaultDict[str, int]] = new_default_stats()
        for stats in stats_list:
            for handler, levels in stats.items():
                for level, count in levels.items():
                    merged[handler][level] += count
        return merged

    @staticmethod
    def print_stats(stats: DefaultDict[str, DefaultDict[str, int]]):
        """Prints log statistics in a formatted table.

        Displays request handler statistics in an aligned tabular format, with:
        - Handlers sorted alphabetically in the first column
        - Standard log levels (DEBUG, INFO, etc.) as column headers
        - Counts aligned under each level column

        Args:
            stats: Statistics to display, in the format:
                {handler: {log_level: count}}

        Example Output:
            HANDLER                  DEBUG   INFO    WARNING ERROR   CRITICAL
            /api/users/              0       12      3       1       0
            /admin/login/            5       20      0       0       0
        """
        print("HANDLER".ljust(25), "\t".join(LOG_LEVELS))
        for handler, counts in sorted(stats.items()):
            print(
                handler.ljust(25),
                "\t".join(str(counts.get(level, 0)) for level in LOG_LEVELS),
            )

    @staticmethod
    def detect_all_levels(file_paths: List[Path]) -> Set[str]:
        """Detect all log levels present in django.request logs"""
        found_levels = set()
        for file_path in file_paths:
            encodings = ["utf-8", "latin-1"]
            for encoding in encodings:
                try:
                    with file_path.open("r", encoding=encoding) as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 4 and parts[3] == "django.request:":
                                found_levels.add(parts[2].upper())
                    break
                except UnicodeDecodeError:
                    continue
        return found_levels
