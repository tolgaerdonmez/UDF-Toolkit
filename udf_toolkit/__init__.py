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

## In-Memory Conversion API

The toolkit supports in-memory conversions that accept bytes/str input and return
ConversionResult objects containing the converted content and extracted UDF metadata
for round-trip conversion.

Example:
    >>> from udf_toolkit import convert_udf_to_docx, convert_udf_to_pdf
    >>> 
    >>> # From file path
    >>> result = convert_udf_to_docx("document.udf")
    >>> docx_bytes = result.content  # bytes
    >>> metadata = result.metadata   # UDFMetadata object
    >>> 
    >>> # From bytes (in-memory)
    >>> with open("document.udf", "rb") as f:
    ...     result = convert_udf_to_pdf(f.read())
    >>> pdf_bytes = result.content
    >>> 
    >>> # Get metadata for round-trip conversion
    >>> metadata_json = result.get_metadata_json()
"""

# Data types for structured conversions
from udf_toolkit.types import (
    UDFMetadata,
    ConversionResult,
    PageFormat,
    StyleDefinition,
    HeaderFooter,
    ParagraphElement,
    ContentElement,
    TextStyle,
    Alignment,
    TableElement,
    TableRow,
    TableCell,
    UDFInput,
)

# Core utilities
from udf_toolkit.core import (
    parse_udf_content,
    extract_udf_metadata,
    create_udf_bytes,
)

# New in-memory conversion functions
from udf_toolkit.udf_to_docx import convert_udf_to_docx
from udf_toolkit.udf_to_pdf import convert_udf_to_pdf
from udf_toolkit.udf_to_md import convert_udf_to_markdown

# Legacy file-based functions (maintained for backward compatibility)
from udf_toolkit.udf_to_docx import udf_to_docx
from udf_toolkit.udf_to_pdf import udf_to_pdf
from udf_toolkit.udf_to_md import udf_to_markdown
from udf_toolkit.docx_to_udf import docx_to_udf as convert_docx_to_udf
from udf_toolkit.scanned_pdf_to_udf import pdf_to_udf
from udf_toolkit.main import convert as docx_to_udf_file

__version__ = "0.2.0"
__all__ = [
    # Data types
    "UDFMetadata",
    "ConversionResult",
    "PageFormat",
    "StyleDefinition",
    "HeaderFooter",
    "ParagraphElement",
    "ContentElement",
    "TextStyle",
    "Alignment",
    "TableElement",
    "TableRow",
    "TableCell",
    "UDFInput",
    # Core utilities
    "parse_udf_content",
    "extract_udf_metadata",
    "create_udf_bytes",
    # In-memory conversion functions (recommended)
    "convert_udf_to_docx",
    "convert_udf_to_pdf",
    "convert_udf_to_markdown",
    # Legacy file-based functions
    "udf_to_docx",
    "udf_to_pdf",
    "udf_to_markdown",
    "convert_docx_to_udf",
    "pdf_to_udf",
    "docx_to_udf_file",
]
