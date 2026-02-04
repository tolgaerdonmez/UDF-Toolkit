import base64
import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ._udf_io import extract_content_text, load_udf_xml


def _register_dejavu_fonts() -> str:
    font_files = {
        'DejaVuSerif': 'DejaVuSerif.ttf',
        'DejaVuSerif-Bold': 'DejaVuSerif-Bold.ttf',
        'DejaVuSerif-Italic': 'DejaVuSerif-Italic.ttf',
        'DejaVuSerif-BoldItalic': 'DejaVuSerif-BoldItalic.ttf',
    }

    for file_name in font_files.values():
        if not os.path.exists(file_name):
            return 'Helvetica'

    for font_name, file_name in font_files.items():
        pdfmetrics.registerFont(TTFont(font_name, file_name))

    pdfmetrics.registerFontFamily(
        'DejaVuSerif',
        normal='DejaVuSerif',
        bold='DejaVuSerif-Bold',
        italic='DejaVuSerif-Italic',
        boldItalic='DejaVuSerif-BoldItalic',
    )

    return 'DejaVuSerif'


def get_alignment_style(alignment_value):
    if alignment_value == "1":
        return TA_CENTER
    elif alignment_value == "3":
        return TA_JUSTIFY
    elif alignment_value == "2":
        return TA_RIGHT
    else:
        return TA_LEFT


def convert_color(color_value):
    if color_value is None:
        return None

    try:
        color_int = int(color_value)
        if color_int < 0:
            color_int = 0xFFFFFFFF + color_int + 1

        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF

        return colors.Color(r / 255, g / 255, b / 255)
    except (ValueError, TypeError):
        return None


def process_background_image(bg_image_data, bg_image_source, output_file):
    if bg_image_data:
        try:
            image_bytes = base64.b64decode(bg_image_data)
            image_stream = io.BytesIO(image_bytes)
            return Image(image_stream)
        except Exception as exc:
            print(f"Error processing background image data: {exc}")
    elif bg_image_source:
        try:
            output_dir = os.path.dirname(output_file)
            source_path = bg_image_source.replace('/resources/', '')
            img_path = os.path.join(output_dir, source_path)

            if os.path.exists(img_path):
                return Image(img_path)
            else:
                print(f"Background image not found: {img_path}")
        except Exception as exc:
            print(f"Error processing background image source: {exc}")

    return None


def convert(udf_file: str, pdf_file: str) -> None:
    root = load_udf_xml(udf_file)
    content_text = extract_content_text(root)

    properties_element = root.find('properties')
    page_format = properties_element.find('pageFormat') if properties_element is not None else None

    left_margin = float(page_format.get('leftMargin', '42.5')) if page_format is not None else 42.5
    right_margin = float(page_format.get('rightMargin', '42.5')) if page_format is not None else 42.5
    top_margin = float(page_format.get('topMargin', '42.5')) if page_format is not None else 42.5
    bottom_margin = float(page_format.get('bottomMargin', '42.5')) if page_format is not None else 42.5

    bg_image = None
    if properties_element is not None:
        bg_image_elem = properties_element.find('bgImage')
        if bg_image_elem is not None:
            bg_image_data = bg_image_elem.get('bgImageData')
            bg_image_source = bg_image_elem.get('bgImageSource')
            bg_image = process_background_image(bg_image_data, bg_image_source, pdf_file)

    elements_element = root.find('elements')
    if elements_element is None:
        raise ValueError("No 'elements' found in UDF file.")

    pdf = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    pdf_elements = []
    styles = getSampleStyleSheet()

    base_font = _register_dejavu_fonts()
    base_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=base_font,
        encoding='utf-8',
    )

    styles_element = root.find('styles')
    if styles_element is not None:
        for style_elem in styles_element.findall('style'):
            style_name = style_elem.get('name', '')
            style_size = float(style_elem.get('size', '12'))
            style_foreground = convert_color(style_elem.get('foreground'))

            custom_style = ParagraphStyle(
                style_name,
                parent=base_style,
                fontName=base_font,
                fontSize=style_size,
                textColor=style_foreground if style_foreground else base_style.textColor,
            )
            styles.add(custom_style)

    for elem in elements_element:
        if elem.tag == 'paragraph':
            paragraph_text = ""
            paragraph_style = base_style

            alignment = elem.get('Alignment', '0')
            paragraph_style = ParagraphStyle(
                'CustomAlignment',
                parent=paragraph_style,
                alignment=get_alignment_style(alignment),
            )

            for child in elem:
                if child.tag == 'content':
                    start_offset = int(child.get('startOffset', '0'))
                    length = int(child.get('length', '0'))
                    text = content_text[start_offset:start_offset + length]

                    if child.get('bold', 'false') == 'true' and child.get('italic', 'false') == 'true':
                        text = f"<b><i>{text}</i></b>"
                    elif child.get('bold', 'false') == 'true':
                        text = f"<b>{text}</b>"
                    elif child.get('italic', 'false') == 'true':
                        text = f"<i>{text}</i>"

                    paragraph_text += text

                elif child.tag == 'space':
                    paragraph_text += " "
                elif child.tag == 'image':
                    paragraph_text += "[Image]"

            if paragraph_text:
                pdf_elements.append(Paragraph(paragraph_text, paragraph_style))
                pdf_elements.append(Spacer(1, 0.1 * inch))

        elif elem.tag == 'table':
            column_count = int(elem.get('columnCount', '1'))
            rows = elem.findall('row')

            table_data = []
            for row in rows:
                row_data = []
                cells = row.findall('cell')

                for cell in cells:
                    cell_text = ""
                    paragraphs = cell.findall('paragraph')

                    for para in paragraphs:
                        para_text = ""
                        for child in para:
                            if child.tag == 'content':
                                start_offset = int(child.get('startOffset', '0'))
                                length = int(child.get('length', '0'))
                                text = content_text[start_offset:start_offset + length]

                                if child.get('bold', 'false') == 'true' and child.get('italic', 'false') == 'true':
                                    text = f"<b><i>{text}</i></b>"
                                elif child.get('bold', 'false') == 'true':
                                    text = f"<b>{text}</b>"
                                elif child.get('italic', 'false') == 'true':
                                    text = f"<i>{text}</i>"

                                para_text += text
                            elif child.tag == 'space':
                                para_text += " "

                        cell_text += para_text + "\n"

                    row_data.append(cell_text.strip())

                while len(row_data) < column_count:
                    row_data.append("")

                table_data.append(row_data)

            if table_data:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                pdf_elements.append(table)
                pdf_elements.append(Spacer(1, 0.1 * inch))

        elif elem.tag == 'pageBreak':
            pdf_elements.append(PageBreak())

    if bg_image:
        pdf_elements.insert(0, bg_image)

    pdf.build(pdf_elements)
