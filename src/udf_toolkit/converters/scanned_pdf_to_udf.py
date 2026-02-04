import base64
import io
import zipfile

import fitz
from PIL import Image


UDF_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8" ?>
<template format_id="1.8">
<content><![CDATA[{content}]]></content>
<properties><pageFormat mediaSizeName="1" leftMargin="42.51968479156494" rightMargin="28.34645652770996" topMargin="14.17322826385498" bottomMargin="14.17322826385498" paperOrientation="1" headerFOffset="20.0" footerFOffset="20.0" /></properties>
<elements resolver="hvl-default">
{elements}
</elements>
<styles><style name="default" description="Geçerli" family="Dialog" size="12" bold="false" italic="false" foreground="-13421773" FONT_ATTRIBUTE_KEY="javax.swing.plaf.FontUIResource[family=Dialog,name=Dialog,style=plain,size=12]" /><style name="hvl-default" family="Times New Roman" size="12" description="Gövde" /></styles>
</template>'''


def convert(pdf_file: str, udf_file: str) -> None:
    try:
        pdf_document = fitz.open(pdf_file)
        content = []
        elements = []
        current_offset = 0

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            text = page.get_text()
            if text:
                content.append(text)
                elements.append(
                    f'<paragraph Alignment="0" LeftIndent="0.0" RightIndent="0.0">'
                    f'<content startOffset="{current_offset}" length="{len(text)}" /></paragraph>'
                )
                current_offset += len(text)

            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                image = Image.open(io.BytesIO(image_bytes))
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                placeholder = '\uFFFC'
                content.append(placeholder)

                elements.append(
                    f'<image family="Times New Roman" size="10" imageData="{img_str}" '
                    f'startOffset="{current_offset}" length="1" />'
                )
                current_offset += 1

            content.append('\n')
            elements.append(
                f'<paragraph Alignment="0" LeftIndent="0.0" RightIndent="0.0">'
                f'<content startOffset="{current_offset}" length="1" /></paragraph>'
            )
            current_offset += 1

        udf_content = UDF_TEMPLATE.format(
            content=''.join(content),
            elements='\n'.join(elements)
        )

        with zipfile.ZipFile(udf_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('content.xml', udf_content)
    except Exception as exc:
        raise RuntimeError(f"Error creating UDF file: {exc}") from exc
