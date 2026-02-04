import subprocess
import sys
from pathlib import Path

from docx import Document


def test_cli_convert_docx_to_udf(tmp_path: Path):
    docx_path = tmp_path / "input.docx"
    doc = Document()
    doc.add_paragraph("CLI Test")
    doc.save(docx_path)

    output_path = tmp_path / "output.udf"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "udf_toolkit.cli",
            "convert",
            str(docx_path),
            str(output_path),
            "--source",
            "docx",
            "--target",
            "udf",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert output_path.exists()
