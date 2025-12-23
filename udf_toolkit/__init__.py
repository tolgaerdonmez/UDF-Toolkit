"""
UDF Toolkit - A toolkit for converting files between UDF and other formats.

UDF (UYAP Document Format) is a document format used by UYAP, the Turkish
National Judiciary Informatics System.

This toolkit provides converters for:
- UDF to DOCX
- UDF to PDF
- UDF to Markdown
- DOCX to UDF
- Scanned PDF to UDF
"""

from udf_toolkit.udf_to_docx import udf_to_docx
from udf_toolkit.udf_to_pdf import udf_to_pdf
from udf_toolkit.udf_to_md import udf_to_markdown
from udf_toolkit.docx_to_udf import docx_to_udf as convert_docx_to_udf
from udf_toolkit.scanned_pdf_to_udf import pdf_to_udf

__version__ = "0.1.0"
__all__ = [
    "udf_to_docx",
    "udf_to_pdf",
    "udf_to_markdown",
    "convert_docx_to_udf",
    "pdf_to_udf",
]
