import argparse
from pathlib import Path

from .api import convert


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="udf-toolkit", description="UDF Toolkit converters")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file path")
    convert_parser.add_argument("output", nargs="?", help="Output file path")
    convert_parser.add_argument("--source", help="Source format (e.g., udf, docx, pdf, md)")
    convert_parser.add_argument("--target", help="Target format (e.g., udf, docx, pdf, md)")
    convert_parser.add_argument(
        "--scanned",
        action="store_true",
        help="Use scanned-PDF pipeline when converting PDF -> UDF",
    )
    convert_parser.add_argument(
        "--no-scanned",
        dest="scanned",
        action="store_false",
        help="Disable scanned-PDF pipeline",
    )
    convert_parser.set_defaults(scanned=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "convert":
        output = convert(
            args.input,
            args.output,
            source=args.source,
            target=args.target,
            scanned=args.scanned,
        )
        print(str(Path(output).resolve()))


if __name__ == "__main__":
    main()
