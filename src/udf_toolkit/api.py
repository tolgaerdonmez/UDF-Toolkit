from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from .converters import (
    docx_to_udf as docx_to_udf_converter,
    scanned_pdf_to_udf as scanned_pdf_to_udf_converter,
    udf_to_docx as udf_to_docx_converter,
    udf_to_md as udf_to_md_converter,
    udf_to_pdf as udf_to_pdf_converter,
)


SUPPORTED_FORMATS = {
    "docx",
    "udf",
    "pdf",
    "md",
    "pdf_scanned",
}

FORMAT_ALIASES = {
    "markdown": "md",
    "scanned_pdf": "pdf_scanned",
    "pdf-ocr": "pdf_scanned",
    "pdf_ocr": "pdf_scanned",
    "text/markdown": "md",
}


def normalize_format(fmt: Optional[str]) -> Optional[str]:
    if fmt is None:
        return None
    fmt = fmt.strip().lower().lstrip(".")
    fmt = FORMAT_ALIASES.get(fmt, fmt)
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {fmt}. Supported: {sorted(SUPPORTED_FORMATS)}")
    return fmt


def detect_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower().lstrip(".")
    return normalize_format(suffix)  # type: ignore[return-value]


def _default_output_path(input_path: Path, target: str) -> Path:
    if target == "pdf_scanned":
        target = "udf"
    return input_path.with_suffix(f".{target}")


def convert(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    source: str | None = None,
    target: str | None = None,
    scanned: bool | None = None,
) -> Path:
    """Convert files between UDF, DOCX, PDF, and Markdown.

    Args:
        input_path: Path to input file.
        output_path: Optional output path. If omitted, derived from target.
        source: Optional source format (e.g., "udf", "docx", "pdf_scanned").
        target: Optional target format (e.g., "docx", "udf", "pdf", "md").
        scanned: If converting PDF to UDF, controls whether to use scanned-PDF pipeline.

    Returns:
        Path to the output file.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    source = normalize_format(source) if source else detect_format(input_path)
    if output_path is not None:
        output_path = Path(output_path)
        if target is None:
            target = detect_format(output_path)
    target = normalize_format(target)

    if target is None:
        raise ValueError("Target format must be provided or inferable from output_path.")

    if output_path is None:
        output_path = _default_output_path(input_path, target)

    converter = _resolve_converter(source, target, scanned)
    converter(str(input_path), str(output_path))
    return output_path


def _resolve_converter(
    source: str,
    target: str,
    scanned: bool | None,
) -> Callable[[str, str], None]:
    if source == "docx" and target == "udf":
        return docx_to_udf_converter
    if source == "udf" and target == "docx":
        return udf_to_docx_converter
    if source == "udf" and target == "pdf":
        return udf_to_pdf_converter
    if source == "udf" and target == "md":
        return udf_to_md_converter

    if source in {"pdf", "pdf_scanned"} and target == "udf":
        if scanned is False:
            raise ValueError("PDF to UDF requires scanned=True for the current pipeline.")
        return scanned_pdf_to_udf_converter

    raise ValueError(f"Unsupported conversion: {source} -> {target}")
