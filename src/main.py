from pathlib import Path
import sys

from src.utils.exceptions import LogAnalyzerError
from src.utils.handler import detect_levels_mode
from src.utils.handler import generate_report
from src.utils.parser import create_parser
from src.utils.validate import validate_files


def main() -> None:
    """
    Entry point for the log analyzer tool.

    Parses command-line arguments, validates input files, processes logs,
    and generates a report or detects available log levels.
    Handles known and unexpected errors gracefully.
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        valid_files = validate_files(args.log_files)

        if args.detect_levels:
            detect_levels_mode(valid_files)
            return

        report = generate_report(valid_files, args.report)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Report saved to {output_path}")
        else:
            print(report)

    except LogAnalyzerError as e:
        print(f"LogAnalyzer error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
