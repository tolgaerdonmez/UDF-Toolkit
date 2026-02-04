import sys
import os

from udf_toolkit.api import convert


def docx_to_udf():
    if len(sys.argv) < 2:
        print("Usage: python docx_to_udf.py input.docx")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)

    filename, ext = os.path.splitext(input_file)

    if ext.lower() == '.docx':
        convert(input_file, filename + '.udf', source='docx', target='udf')
    else:
        print("Please provide a .docx file.")
        sys.exit(1)


if __name__ == '__main__':
    docx_to_udf()
