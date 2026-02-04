import zipfile
from docx import Document

from ..docx_processing import process_paragraph, process_table


UDF_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8" ?>
<template format_id="1.8">
<content><![CDATA[{content}]]></content>
<properties><pageFormat mediaSizeName="1" leftMargin="42.51968479156494" rightMargin="28.34645652770996" topMargin="14.17322826385498" bottomMargin="14.17322826385498" paperOrientation="1" headerFOffset="20.0" footerFOffset="20.0" /></properties>
<elements resolver="hvl-default">
{elements}
</elements>
<styles><style name="default" description="Geçerli" family="Dialog" size="12" bold="false" italic="false" foreground="-13421773" FONT_ATTRIBUTE_KEY="javax.swing.plaf.FontUIResource[family=Dialog,name=Dialog,style=plain,size=12]" /><style name="hvl-default" family="Times New Roman" size="12" description="Gövde" /></styles>
</template>'''


def convert(docx_file: str, udf_file: str) -> None:
    try:
        document = Document(docx_file)
    except Exception as exc:
        raise RuntimeError(f"Error loading DOCX file: {exc}") from exc

    content = []
    elements = []
    current_offset = 0
    empty_paragraph_placeholder = '\u200B'

    for element in document.element.body:
        if element.tag.endswith('p'):
            para_text, para_elements = process_paragraph(element, document, current_offset)
            elements.append(para_elements)
            content.append(para_text)
            current_offset += len(para_text)
        elif element.tag.endswith('tbl'):
            table_text, table_element = process_table(element, document, current_offset)
            elements.append(table_element)
            content.append(table_text)
            current_offset += len(table_text)

    if not content:
        content.append(empty_paragraph_placeholder)
        elements.append(
            f'<paragraph Alignment="0" LeftIndent="0.0" RightIndent="0.0"><content startOffset="{current_offset}" length="1" /></paragraph>'
        )

    udf_content = UDF_TEMPLATE.format(
        content=''.join(content),
        elements='\n'.join(elements)
    )

    try:
        with zipfile.ZipFile(udf_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('content.xml', udf_content)
    except Exception as exc:
        raise RuntimeError(f"Error creating UDF file: {exc}") from exc
