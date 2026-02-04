import sys
import os

from udf_toolkit.api import convert


def main():
    if len(sys.argv) < 2:
        print("Usage: python udf_to_pdf.py input.udf")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)

    filename, ext = os.path.splitext(input_file)

    if ext.lower() == '.udf':
        convert(input_file, filename + '.pdf', source='udf', target='pdf')
    else:
        print("Please provide a .udf file.")
        sys.exit(1)


if __name__ == '__main__':
    main()
