import sys
import os
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
import base64
import io
import zipfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from typing import Union, Optional

from udf_toolkit.types import UDFMetadata, ConversionResult, UDFInput
from udf_toolkit.core import parse_udf_content, extract_udf_metadata

# Try to register DejaVu fonts that support Turkish characters
# Fall back to default fonts if DejaVuSerif is not available
_USE_DEJAVU_FONTS = False
try:
    pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', 'DejaVuSerif-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Italic', 'DejaVuSerif-Italic.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-BoldItalic', 'DejaVuSerif-BoldItalic.ttf'))
    pdfmetrics.registerFontFamily('DejaVuSerif', normal='DejaVuSerif', bold='DejaVuSerif-Bold',
                                 italic='DejaVuSerif-Italic', boldItalic='DejaVuSerif-BoldItalic')
    _USE_DEJAVU_FONTS = True
except Exception:
    # DejaVu fonts not available, will use Helvetica as fallback
    pass

def _get_font_name():
    """Get the appropriate font name based on availability."""
    return 'DejaVuSerif' if _USE_DEJAVU_FONTS else 'Helvetica'

def is_zip_file(file_path):
    """Check if the file is a valid ZIP file"""
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            return True
    except zipfile.BadZipFile:
        return False

def get_alignment_style(alignment_value):
    """Convert alignment value from XML to reportlab alignment constant"""
    if alignment_value == "1":
        return TA_CENTER
    elif alignment_value == "3":
        return TA_JUSTIFY
    elif alignment_value == "2":
        return TA_RIGHT
    else:
        return TA_LEFT

def convert_color(color_value):
    """Convert integer color value to reportlab color"""
    if color_value is None:
        return None
    
    try:
        # Convert from negative integer to positive hex
        color_int = int(color_value)
        if color_int < 0:
            color_int = 0xFFFFFFFF + color_int + 1
        
        # Extract RGB values
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        
        return colors.Color(r/255, g/255, b/255)
    except (ValueError, TypeError):
        return None

def process_background_image(bg_image_data, bg_image_source, output_file):
    """Process background image data and return Image object"""
    if bg_image_data:
        try:
            # Decode base64 image data
            image_bytes = base64.b64decode(bg_image_data)
            image_stream = io.BytesIO(image_bytes)
            
            # Create reportlab image
            img = Image(image_stream)
            return img
        except Exception as e:
            print(f"Error processing background image data: {e}")
    elif bg_image_source:
        # Try to load from source path if available
        try:
            # Check if the source path exists relative to the output file
            output_dir = os.path.dirname(output_file)
            # Normalize path
            source_path = bg_image_source.replace('/resources/', '')
            img_path = os.path.join(output_dir, source_path)
            
            if os.path.exists(img_path):
                return Image(img_path)
            else:
                print(f"Background image not found: {img_path}")
        except Exception as e:
            print(f"Error processing background image source: {e}")
    
    return None


def convert_udf_to_pdf(data: UDFInput, output_path: Optional[str] = None) -> ConversionResult:
    """
    Convert UDF content to PDF format with metadata extraction.
    
    This function supports in-memory conversion and extracts UDF metadata
    for potential round-trip conversion back to UDF.
    
    Args:
        data: UDF content as file path (str), bytes, or XML string
        output_path: Optional path to save the PDF file. If None, only returns bytes.
        
    Returns:
        ConversionResult containing:
            - content: PDF file as bytes
            - metadata: Extracted UDF metadata for round-trip conversion
            - original_text: The original text content from UDF
            
    Raises:
        ValueError: If the input cannot be parsed
        
    Example:
        >>> # From file path
        >>> result = convert_udf_to_pdf("document.udf")
        >>> pdf_bytes = result.content
        >>> metadata = result.metadata
        
        >>> # From bytes
        >>> with open("document.udf", "rb") as f:
        ...     result = convert_udf_to_pdf(f.read())
        
        >>> # Save to file and get result
        >>> result = convert_udf_to_pdf("document.udf", "output.pdf")
    """
    # Parse UDF content
    root, content_text = parse_udf_content(data)
    
    # Extract metadata for round-trip conversion
    metadata = extract_udf_metadata(root, content_text)
    
    # Build PDF to bytes
    buffer = io.BytesIO()
    _build_pdf_to_buffer(buffer, root, content_text, metadata)
    buffer.seek(0)
    pdf_bytes = buffer.read()
    
    # Optionally save to file
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
    
    return ConversionResult(
        content=pdf_bytes,
        metadata=metadata,
        original_text=content_text,
    )


def _build_pdf_to_buffer(buffer: io.BytesIO, root: ET.Element, content_text: str, metadata: UDFMetadata):
    """Build PDF content to a buffer."""
    # Get page margins from metadata
    left_margin = metadata.page_format.left_margin
    right_margin = metadata.page_format.right_margin
    top_margin = metadata.page_format.top_margin
    bottom_margin = metadata.page_format.bottom_margin
    
    # Get background image if available
    bg_image = None
    if metadata.background_image_data:
        try:
            image_bytes = base64.b64decode(metadata.background_image_data)
            image_stream = io.BytesIO(image_bytes)
            bg_image = Image(image_stream)
        except Exception:
            pass
    
    # Process the 'elements' section
    elements_element = root.find('elements')
    if elements_element is None:
        raise ValueError("'elements' could not be found in the XML.")
    
    # Create the PDF document with specified margins
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )
    
    # Create elements list for the PDF
    pdf_elements = []
    styles = getSampleStyleSheet()
    
    # Define a base style that supports Turkish characters
    base_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=_get_font_name(),
        encoding='utf-8'
    )
    
    # Get header and footer elements
    header_element = elements_element.find('header')
    footer_element = elements_element.find('footer')
    
    # Function to process a text block and apply formatting
    def process_text_block(content_elem, current_style):
        start_offset = int(content_elem.get('startOffset', '0'))
        length = int(content_elem.get('length', '0'))
        text_content = content_text[start_offset:start_offset+length]
        
        bold = content_elem.get('bold', 'false') == 'true'
        italic = content_elem.get('italic', 'false') == 'true'
        underline = content_elem.get('underline', 'false') == 'true'
        family = content_elem.get('family')
        size = content_elem.get('size')
        foreground = convert_color(content_elem.get('foreground'))
        
        if family:
            current_style.fontName = _get_font_name()
        if size:
            current_style.fontSize = float(size)
        if foreground:
            current_style.textColor = foreground
        
        formatted_text = text_content
        if bold and italic and underline:
            formatted_text = f"<u><b><i>{formatted_text}</i></b></u>"
        elif bold and italic:
            formatted_text = f"<b><i>{formatted_text}</i></b>"
        elif bold and underline:
            formatted_text = f"<u><b>{formatted_text}</b></u>"
        elif italic and underline:
            formatted_text = f"<u><i>{formatted_text}</i></u>"
        elif bold:
            formatted_text = f"<b>{formatted_text}</b>"
        elif italic:
            formatted_text = f"<i>{formatted_text}</i>"
        elif underline:
            formatted_text = f"<u>{formatted_text}</u>"
        
        return formatted_text
    
    # Function to process a paragraph element
    def process_paragraph(para_elem, content_buffer, in_header_footer=False):
        alignment = para_elem.get('Alignment', '0')
        alignment_style = get_alignment_style(alignment)
        
        left_indent = float(para_elem.get('LeftIndent', '0'))
        right_indent = float(para_elem.get('RightIndent', '0'))
        first_line_indent = float(para_elem.get('FirstLineIndent', '0'))
        line_spacing = float(para_elem.get('LineSpacing', '1.2'))
        
        family = _get_font_name()
        size = float(para_elem.get('size', '12'))
        
        para_style = ParagraphStyle(
            f'Style{alignment}',
            parent=base_style,
            alignment=alignment_style,
            leftIndent=left_indent,
            rightIndent=right_indent,
            firstLineIndent=first_line_indent,
            fontName=family,
            fontSize=size,
            leading=size * line_spacing
        )
        
        paragraph_text = ''
        for child in para_elem:
            if child.tag == 'content':
                paragraph_text += process_text_block(child, para_style)
            elif child.tag == 'field':
                field_name = child.get('fieldName', '')
                if child.get('startOffset') and child.get('length'):
                    start_offset = int(child.get('startOffset', '0'))
                    length = int(child.get('length', '0'))
                    field_text = content_buffer[start_offset:start_offset+length]
                else:
                    field_text = field_name
                
                bold = child.get('bold', 'false') == 'true'
                italic = child.get('italic', 'false') == 'true'
                underline = child.get('underline', 'false') == 'true'
                
                if bold and italic and underline:
                    paragraph_text += f"<u><b><i>{field_text}</i></b></u>"
                elif bold and italic:
                    paragraph_text += f"<b><i>{field_text}</i></b>"
                elif bold and underline:
                    paragraph_text += f"<u><b>{field_text}</b></u>"
                elif italic and underline:
                    paragraph_text += f"<u><i>{field_text}</i></u>"
                elif bold:
                    paragraph_text += f"<b>{field_text}</b>"
                elif italic:
                    paragraph_text += f"<i>{field_text}</i>"
                elif underline:
                    paragraph_text += f"<u>{field_text}</u>"
                else:
                    paragraph_text += field_text
            elif child.tag == 'space':
                paragraph_text += ' '
            elif child.tag == 'image':
                image_data = child.get('imageData')
                if image_data:
                    try:
                        image_bytes = base64.b64decode(image_data)
                        image_stream = io.BytesIO(image_bytes)
                        img = Image(image_stream)
                        if not hasattr(img, 'drawWidth') or not img.drawWidth:
                            img.drawWidth = 100
                        if not hasattr(img, 'drawHeight') or not img.drawHeight:
                            img.drawHeight = 50
                        if not in_header_footer:
                            return Paragraph(paragraph_text, para_style), img
                    except Exception as e:
                        paragraph_text += "[GÖRSEL]"
        
        return Paragraph(paragraph_text, para_style), None
    
    # Define header and footer
    header_paragraphs = []
    footer_paragraphs = []
    header_bg_color = None
    footer_bg_color = None
    
    if header_element is not None:
        header_bg_color = convert_color(header_element.get('background'))
        for para in header_element.findall('paragraph'):
            header_para, _ = process_paragraph(para, content_text, True)
            header_paragraphs.append(header_para)
    
    if footer_element is not None:
        footer_bg_color = convert_color(footer_element.get('background'))
        for para in footer_element.findall('paragraph'):
            footer_para, _ = process_paragraph(para, content_text, True)
            footer_paragraphs.append(footer_para)
    
    # Create a function to draw the header and footer on each page
    def add_header_footer(canvas_obj, doc):
        canvas_obj.saveState()
        
        if header_paragraphs:
            if header_bg_color:
                canvas_obj.setFillColor(header_bg_color)
                canvas_obj.rect(doc.leftMargin, doc.height + doc.topMargin - 20,
                              doc.width, 20, fill=True, stroke=False)
            for i, para in enumerate(header_paragraphs):
                w, h = para.wrap(doc.width, doc.topMargin)
                para.drawOn(canvas_obj, doc.leftMargin, doc.height + doc.topMargin - 15 - i*h)
        
        if footer_paragraphs:
            if footer_bg_color:
                canvas_obj.setFillColor(footer_bg_color)
                canvas_obj.rect(doc.leftMargin, doc.bottomMargin - 20,
                              doc.width, 20, fill=True, stroke=False)
            for i, para in enumerate(footer_paragraphs):
                w, h = para.wrap(doc.width, doc.bottomMargin)
                para.drawOn(canvas_obj, doc.leftMargin, doc.bottomMargin - 15 - i*h)
        
        if bg_image:
            page_width = doc.width
            page_height = doc.height
            img_ratio = bg_image.imageWidth / bg_image.imageHeight
            page_ratio = page_width / page_height
            
            if img_ratio > page_ratio:
                bg_image.drawWidth = page_width
                bg_image.drawHeight = page_width / img_ratio
            else:
                bg_image.drawHeight = page_height
                bg_image.drawWidth = page_height * img_ratio
            
            x_offset = doc.leftMargin + (page_width - bg_image.drawWidth) / 2
            y_offset = doc.bottomMargin + (page_height - bg_image.drawHeight) / 2
            
            canvas_obj.saveState()
            canvas_obj.setFillAlpha(0.1)
            bg_image.drawOn(canvas_obj, x_offset, y_offset)
            canvas_obj.restoreState()
        
        canvas_obj.restoreState()
    
    # Process each element in the XML
    for elem in elements_element:
        if elem.tag == 'paragraph':
            para, img = process_paragraph(elem, content_text)
            pdf_elements.append(para)
            if img:
                pdf_elements.append(img)
            pdf_elements.append(Spacer(1, 5))
        elif elem.tag == 'page-break':
            pdf_elements.append(PageBreak())
        elif elem.tag == 'table':
            table_data = []
            rows = elem.findall('row')
            for row in rows:
                row_data = []
                cells = row.findall('cell')
                for cell in cells:
                    paragraphs = cell.findall('paragraph')
                    cell_paragraphs = []
                    for para in paragraphs:
                        cell_para, cell_img = process_paragraph(para, content_text)
                        cell_paragraphs.append(cell_para)
                        if cell_img:
                            cell_paragraphs.append(cell_img)
                    if cell_paragraphs:
                        row_data.append(cell_paragraphs)
                    else:
                        row_data.append(Paragraph("", base_style))
                table_data.append(row_data)
            
            col_count = int(elem.get('columnCount', '1'))
            col_spans = elem.get('columnSpans', '').split(',')
            border_style = elem.get('border', 'borderCell')
            
            col_widths = None
            if col_spans and len(col_spans) == col_count:
                try:
                    col_widths = [float(span) for span in col_spans]
                except ValueError:
                    pass
            
            table_style_list = [
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 3),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]
            
            if border_style in ['borderCell', 'border']:
                table_style_list.append(('GRID', (0,0), (-1,-1), 1, colors.black))
            elif border_style == 'borderOuter':
                table_style_list.append(('BOX', (0,0), (-1,-1), 1, colors.black))
            
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle(table_style_list))
            pdf_elements.append(table)
            pdf_elements.append(Spacer(1, 5))
    
    # Build the PDF document with header and footer
    pdf.build(pdf_elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)


def udf_to_pdf(udf_file, pdf_file):
    """Convert a UDF file to PDF format.
    
    Args:
        udf_file: Path to the input UDF file
        pdf_file: Path to the output PDF file
    """
    root = None
    
    # Check if the file is a ZIP file
    if is_zip_file(udf_file):
        # Process as a ZIP file
        with zipfile.ZipFile(udf_file, 'r') as z:
            if 'content.xml' in z.namelist():
                with z.open('content.xml') as content_file:
                    tree = ET.parse(content_file, parser=ET.XMLParser(encoding='utf-8'))
                    root = tree.getroot()
            else:
                print("The 'content.xml' file could not be found in the UDF file.")
                exit()
    else:
        # Process as an XML file directly
        try:
            tree = ET.parse(udf_file, parser=ET.XMLParser(encoding='utf-8'))
            root = tree.getroot()
        except ET.ParseError:
            print(f"The file {udf_file} is neither a valid ZIP nor a valid XML file.")
            exit()

    if root is None:
        print("Failed to parse the file.")
        exit()

    # Retrieve content text
    content_element = root.find('content')
    if content_element is not None:
        content_text = content_element.text
        if content_text.startswith('<![CDATA[') and content_text.endswith(']]>'):
            content_text = content_text[9:-3]
    else:
        print("'content' could not be found in the XML.")
        exit()

    # Extract page properties
    properties_element = root.find('properties')
    page_format = properties_element.find('pageFormat') if properties_element is not None else None
    
    # Get page margins
    left_margin = float(page_format.get('leftMargin', '42.5')) if page_format is not None else 42.5
    right_margin = float(page_format.get('rightMargin', '42.5')) if page_format is not None else 42.5
    top_margin = float(page_format.get('topMargin', '42.5')) if page_format is not None else 42.5
    bottom_margin = float(page_format.get('bottomMargin', '42.5')) if page_format is not None else 42.5
    
    # Get background image if available
    bg_image = None
    if properties_element is not None:
        bg_image_elem = properties_element.find('bgImage')
        if bg_image_elem is not None:
            bg_image_data = bg_image_elem.get('bgImageData')
            bg_image_source = bg_image_elem.get('bgImageSource')
            bg_image = process_background_image(bg_image_data, bg_image_source, pdf_file)

    # Process the 'elements' section
    elements_element = root.find('elements')
    if elements_element is not None:
        # Create the PDF document with specified margins
        pdf = SimpleDocTemplate(
            pdf_file, 
            pagesize=A4,
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        
        # Create elements list for the PDF
        pdf_elements = []
        styles = getSampleStyleSheet()
        
        # Define a base style that supports Turkish characters
        base_style = ParagraphStyle(
            'CustomNormal', 
            parent=styles['Normal'],
            fontName=_get_font_name(),
            encoding='utf-8'
        )
        
        # Process styles from the XML
        styles_element = root.find('styles')
        if styles_element is not None:
            for style_elem in styles_element.findall('style'):
                style_name = style_elem.get('name', '')
                style_family = _get_font_name()
                style_size = float(style_elem.get('size', '12'))
                style_bold = style_elem.get('bold', 'false') == 'true'
                style_italic = style_elem.get('italic', 'false') == 'true'
                style_foreground = convert_color(style_elem.get('foreground'))
                    
                custom_style = ParagraphStyle(
                    style_name,
                    parent=base_style,
                    fontName=style_family,
                    fontSize=style_size,
                    textColor=style_foreground if style_foreground else base_style.textColor
                )
                
                # Set bold and italic based on font family
                if style_bold and style_italic:
                    custom_style.fontName = f"{style_family}-BoldItalic"
                elif style_bold:
                    custom_style.fontName = f"{style_family}-Bold"
                elif style_italic:
                    custom_style.fontName = f"{style_family}-Italic"

        # Get header and footer elements
        header_element = elements_element.find('header')
        footer_element = elements_element.find('footer')
        
        # Function to process a text block and apply formatting
        def process_text_block(content_elem, current_style):
            text = ""
            
            # Get basic attributes
            start_offset = int(content_elem.get('startOffset', '0'))
            length = int(content_elem.get('length', '0'))
            text_content = content_text[start_offset:start_offset+length]
            
            # Get formatting attributes
            bold = content_elem.get('bold', 'false') == 'true'
            italic = content_elem.get('italic', 'false') == 'true'
            underline = content_elem.get('underline', 'false') == 'true'
            family = content_elem.get('family')
            size = content_elem.get('size')
            foreground = convert_color(content_elem.get('foreground'))
            
            # Apply text formatting
            if family:
                current_style.fontName = _get_font_name()
            if size:
                current_style.fontSize = float(size)
            if foreground:
                current_style.textColor = foreground
            
            # Apply emphasis formatting
            formatted_text = text_content
            if bold and italic and underline:
                formatted_text = f"<u><b><i>{formatted_text}</i></b></u>"
            elif bold and italic:
                formatted_text = f"<b><i>{formatted_text}</i></b>"
            elif bold and underline:
                formatted_text = f"<u><b>{formatted_text}</b></u>"
            elif italic and underline:
                formatted_text = f"<u><i>{formatted_text}</i></u>"
            elif bold:
                formatted_text = f"<b>{formatted_text}</b>"
            elif italic:
                formatted_text = f"<i>{formatted_text}</i>"
            elif underline:
                formatted_text = f"<u>{formatted_text}</u>"
            
            return formatted_text
        
        # Function to process a paragraph element
        def process_paragraph(para_elem, content_buffer, in_header_footer=False):
            # Get paragraph alignment
            alignment = para_elem.get('Alignment', '0')
            alignment_style = get_alignment_style(alignment)
            
            # Get paragraph indentation
            left_indent = float(para_elem.get('LeftIndent', '0'))
            right_indent = float(para_elem.get('RightIndent', '0'))
            first_line_indent = float(para_elem.get('FirstLineIndent', '0'))
            line_spacing = float(para_elem.get('LineSpacing', '1.2'))
            
            # Get paragraph font family
            family = _get_font_name()
            size = float(para_elem.get('size', '12'))
            
            # Create a custom style for this paragraph
            para_style = ParagraphStyle(
                f'Style{alignment}',
                parent=base_style,
                alignment=alignment_style,
                leftIndent=left_indent,
                rightIndent=right_indent,
                firstLineIndent=first_line_indent,
                fontName=family,
                fontSize=size,
                leading=size * line_spacing  # Leading is the line spacing
            )
            
            # Process the paragraph content
            paragraph_text = ''
            for child in para_elem:
                if child.tag == 'content':
                    paragraph_text += process_text_block(child, para_style)
                elif child.tag == 'field':
                    # Process field element (labels like DAVACI, VEKİLİ, etc.)
                    field_name = child.get('fieldName', '')
                    
                    # Get the text from the content buffer if startOffset and length are provided
                    if child.get('startOffset') and child.get('length'):
                        start_offset = int(child.get('startOffset', '0'))
                        length = int(child.get('length', '0'))
                        field_text = content_buffer[start_offset:start_offset+length]
                    else:
                        # Use the fieldName as fallback
                        field_text = field_name
                    
                    # Apply styling 
                    bold = child.get('bold', 'false') == 'true'
                    italic = child.get('italic', 'false') == 'true'
                    underline = child.get('underline', 'false') == 'true'
                    
                    # Format text with style
                    if bold and italic and underline:
                        paragraph_text += f"<u><b><i>{field_text}</i></b></u>"
                    elif bold and italic:
                        paragraph_text += f"<b><i>{field_text}</i></b>"
                    elif bold and underline:
                        paragraph_text += f"<u><b>{field_text}</b></u>"
                    elif italic and underline:
                        paragraph_text += f"<u><i>{field_text}</i></u>"
                    elif bold:
                        paragraph_text += f"<b>{field_text}</b>"
                    elif italic:
                        paragraph_text += f"<i>{field_text}</i>"
                    elif underline:
                        paragraph_text += f"<u>{field_text}</u>"
                    else:
                        paragraph_text += field_text
                elif child.tag == 'space':
                    paragraph_text += ' '
                elif child.tag == 'image':
                    # Add the image
                    image_data = child.get('imageData')
                    if image_data:
                        try:
                            # Decode base64 image data
                            image_bytes = base64.b64decode(image_data)
                            image_stream = io.BytesIO(image_bytes)
                            
                            # Create reportlab image
                            img = Image(image_stream)
                            
                            # Set a reasonable width/height if not specified
                            if not hasattr(img, 'drawWidth') or not img.drawWidth:
                                img.drawWidth = 100
                            if not hasattr(img, 'drawHeight') or not img.drawHeight:
                                img.drawHeight = 50
                            
                            # For images in paragraphs, we'll handle them specially
                            if not in_header_footer:
                                return Paragraph(paragraph_text, para_style), img
                        except Exception as e:
                            print(f"Error processing image: {e}")
                            # Add a placeholder text instead
                            paragraph_text += "[GÖRSEL]"
            
            # Return the paragraph
            return Paragraph(paragraph_text, para_style), None
        
        # Define header and footer
        header_paragraphs = []
        footer_paragraphs = []
        
        if header_element is not None:
            header_bg_color = convert_color(header_element.get('background'))
            header_fg_color = convert_color(header_element.get('foreground'))
            
            for para in header_element.findall('paragraph'):
                header_para, _ = process_paragraph(para, content_text, True)
                header_paragraphs.append(header_para)
        
        if footer_element is not None:
            footer_bg_color = convert_color(footer_element.get('background'))
            footer_fg_color = convert_color(footer_element.get('foreground'))
            
            for para in footer_element.findall('paragraph'):
                footer_para, _ = process_paragraph(para, content_text, True)
                footer_paragraphs.append(footer_para)
        
        # Create a function to draw the header and footer on each page
        def add_header_footer(canvas, doc):
            canvas.saveState()
            
            # Draw header
            if header_paragraphs:
                # Draw header background if color specified
                if header_bg_color:
                    canvas.setFillColor(header_bg_color)
                    canvas.rect(
                        doc.leftMargin, 
                        doc.height + doc.topMargin - 20, 
                        doc.width, 
                        20, 
                        fill=True, 
                        stroke=False
                    )
                
                # Draw header text
                for i, para in enumerate(header_paragraphs):
                    w, h = para.wrap(doc.width, doc.topMargin)
                    para.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 15 - i*h)
            
            # Draw footer
            if footer_paragraphs:
                # Draw footer background if color specified
                if footer_bg_color:
                    canvas.setFillColor(footer_bg_color)
                    canvas.rect(
                        doc.leftMargin, 
                        doc.bottomMargin - 20, 
                        doc.width, 
                        20, 
                        fill=True, 
                        stroke=False
                    )
                
                # Draw footer text
                for i, para in enumerate(footer_paragraphs):
                    w, h = para.wrap(doc.width, doc.bottomMargin)
                    para.drawOn(canvas, doc.leftMargin, doc.bottomMargin - 15 - i*h)
            
            # Draw background image if available
            if bg_image:
                # Scale image to fit page with margins
                page_width = doc.width
                page_height = doc.height
                
                # Preserve aspect ratio
                img_ratio = bg_image.imageWidth / bg_image.imageHeight
                page_ratio = page_width / page_height
                
                if img_ratio > page_ratio:
                    # Image is wider than page
                    bg_image.drawWidth = page_width
                    bg_image.drawHeight = page_width / img_ratio
                else:
                    # Image is taller than page
                    bg_image.drawHeight = page_height
                    bg_image.drawWidth = page_height * img_ratio
                
                # Center the image
                x_offset = doc.leftMargin + (page_width - bg_image.drawWidth) / 2
                y_offset = doc.bottomMargin + (page_height - bg_image.drawHeight) / 2
                
                # Draw the image with transparency
                canvas.saveState()
                canvas.setFillAlpha(0.1)  # Set transparency
                bg_image.drawOn(canvas, x_offset, y_offset)
                canvas.restoreState()
            
            canvas.restoreState()
        
        content_buffer = content_text
        
        # Process each element in the XML
        for elem in elements_element:
            if elem.tag == 'paragraph':
                para, img = process_paragraph(elem, content_buffer)
                pdf_elements.append(para)
                if img:
                    pdf_elements.append(img)
                pdf_elements.append(Spacer(1, 5))
            elif elem.tag == 'page-break':
                pdf_elements.append(PageBreak())
            elif elem.tag == 'table':
                # Create the table
                table_data = []
                rows = elem.findall('row')
                for row in rows:
                    row_data = []
                    cells = row.findall('cell')
                    for cell in cells:
                        # Process the cell content
                        paragraphs = cell.findall('paragraph')
                        cell_paragraphs = []
                        
                        for para in paragraphs:
                            cell_para, cell_img = process_paragraph(para, content_buffer)
                            cell_paragraphs.append(cell_para)
                            if cell_img:
                                cell_paragraphs.append(cell_img)
                        
                        # Check if we have any paragraphs
                        if cell_paragraphs:
                            row_data.append(cell_paragraphs)
                        else:
                            # If no content, add an empty Paragraph
                            row_data.append(Paragraph("", base_style))
                    table_data.append(row_data)
                
                # Get table properties
                col_count = int(elem.get('columnCount', '1'))
                col_spans = elem.get('columnSpans', '').split(',')
                row_spans = elem.get('rowSpans', '').split(',')
                border_style = elem.get('border', 'borderCell')
                
                # Set column widths if available
                col_widths = None
                if col_spans and len(col_spans) == col_count:
                    try:
                        col_widths = [float(span) for span in col_spans]
                    except ValueError:
                        pass
                
                # Set the table style
                table_style = [
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 3),
                    ('RIGHTPADDING', (0,0), (-1,-1), 3),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]
                
                # Add grid/border based on style
                if border_style == 'borderCell' or border_style == 'border':
                    table_style.append(('GRID', (0,0), (-1,-1), 1, colors.black))
                elif border_style == 'borderOuter':
                    table_style.append(('BOX', (0,0), (-1,-1), 1, colors.black))
                
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle(table_style))
                pdf_elements.append(table)
                pdf_elements.append(Spacer(1, 5))
            # Skip header and footer here as they're handled separately
            elif elem.tag not in ['header', 'footer']:
                pass
        
        # Build the PDF document with header and footer
        pdf.build(pdf_elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        print(f"PDF file created: {pdf_file}")
    else:
        print("'elements' could not be found in the XML.")

def main():
    """CLI entry point for converting UDF files to PDF format."""
    if len(sys.argv) < 2:
        print("Usage: udf-to-pdf input.udf")
        exit()

    udf_file = sys.argv[1]

    if not os.path.isfile(udf_file):
        print(f"Input file not found: {udf_file}")
        exit()

    filename, ext = os.path.splitext(udf_file)

    if ext.lower() == '.udf':
        pdf_file = filename + '.pdf'
        udf_to_pdf(udf_file, pdf_file)
    else:
        print("Please provide a .udf file.")

if __name__ == '__main__':
    main()
