"""
Core conversion utilities for UDF Toolkit.

This module provides utility functions for parsing UDF content and
handling in-memory conversions.
"""

import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Union, Optional, Tuple

from udf_toolkit.types import (
    UDFMetadata, PageFormat, StyleDefinition, HeaderFooter,
    ParagraphElement, ContentElement, TextStyle, Alignment,
    TableElement, TableRow, TableCell,
)


def parse_udf_content(data: Union[str, bytes]) -> Tuple[ET.Element, str]:
    """
    Parse UDF content from either a file path, bytes, or string.
    
    Args:
        data: Either a file path (str), raw bytes, or XML string
        
    Returns:
        Tuple of (XML root element, content text)
        
    Raises:
        ValueError: If the content cannot be parsed
    """
    root = None
    
    # If it's a string, check if it's a file path or XML content
    if isinstance(data, str):
        if data.strip().startswith('<?xml') or data.strip().startswith('<template'):
            # It's XML content
            try:
                root = ET.fromstring(data)
            except ET.ParseError as e:
                raise ValueError(f"Failed to parse XML content: {e}")
        else:
            # Assume it's a file path
            import os
            if not os.path.isfile(data):
                raise ValueError(f"File not found: {data}")
            
            # Try to read as ZIP first
            if _is_zip_file_path(data):
                with zipfile.ZipFile(data, 'r') as z:
                    if 'content.xml' in z.namelist():
                        with z.open('content.xml') as content_file:
                            tree = ET.parse(content_file, parser=ET.XMLParser(encoding='utf-8'))
                            root = tree.getroot()
                    else:
                        raise ValueError("The 'content.xml' file could not be found in the UDF file.")
            else:
                # Try as raw XML file
                try:
                    tree = ET.parse(data, parser=ET.XMLParser(encoding='utf-8'))
                    root = tree.getroot()
                except ET.ParseError as e:
                    raise ValueError(f"The file is neither a valid ZIP nor a valid XML file: {e}")
    
    elif isinstance(data, bytes):
        # Check if it's a ZIP file
        if _is_zip_bytes(data):
            with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
                if 'content.xml' in z.namelist():
                    with z.open('content.xml') as content_file:
                        tree = ET.parse(content_file, parser=ET.XMLParser(encoding='utf-8'))
                        root = tree.getroot()
                else:
                    raise ValueError("The 'content.xml' file could not be found in the UDF data.")
        else:
            # Try as raw XML
            try:
                root = ET.fromstring(data.decode('utf-8'))
            except (ET.ParseError, UnicodeDecodeError) as e:
                raise ValueError(f"Failed to parse bytes as XML: {e}")
    else:
        raise ValueError(f"Invalid input type: {type(data)}. Expected str or bytes.")
    
    if root is None:
        raise ValueError("Failed to parse the UDF content.")
    
    # Extract content text
    content_element = root.find('content')
    if content_element is None:
        raise ValueError("'content' element could not be found in the XML.")
    
    content_text = content_element.text or ""
    if content_text.startswith('<![CDATA[') and content_text.endswith(']]>'):
        content_text = content_text[9:-3]
    
    return root, content_text


def extract_udf_metadata(root: ET.Element, content_text: str) -> UDFMetadata:
    """
    Extract UDF metadata from parsed XML.
    
    Args:
        root: The XML root element
        content_text: The content text extracted from the UDF
        
    Returns:
        UDFMetadata object containing all extracted metadata
    """
    metadata = UDFMetadata()
    
    # Extract format_id from template
    metadata.format_id = root.get('format_id', '1.8')
    
    # Extract page format
    properties_element = root.find('properties')
    if properties_element is not None:
        page_format_elem = properties_element.find('pageFormat')
        if page_format_elem is not None:
            metadata.page_format = PageFormat(
                media_size_name=page_format_elem.get('mediaSizeName', '1'),
                left_margin=float(page_format_elem.get('leftMargin', '42.52')),
                right_margin=float(page_format_elem.get('rightMargin', '28.35')),
                top_margin=float(page_format_elem.get('topMargin', '14.17')),
                bottom_margin=float(page_format_elem.get('bottomMargin', '14.17')),
                paper_orientation=page_format_elem.get('paperOrientation', '1'),
                header_offset=float(page_format_elem.get('headerFOffset', '20.0')),
                footer_offset=float(page_format_elem.get('footerFOffset', '20.0')),
            )
        
        # Extract background image
        bg_image_elem = properties_element.find('bgImage')
        if bg_image_elem is not None:
            metadata.background_image_data = bg_image_elem.get('bgImageData')
            metadata.background_image_source = bg_image_elem.get('bgImageSource')
    
    # Extract styles
    styles_element = root.find('styles')
    if styles_element is not None:
        for style_elem in styles_element.findall('style'):
            style = StyleDefinition(
                name=style_elem.get('name', ''),
                description=style_elem.get('description'),
                family=style_elem.get('family', 'Times New Roman'),
                size=float(style_elem.get('size', '12')),
                bold=style_elem.get('bold', 'false') == 'true',
                italic=style_elem.get('italic', 'false') == 'true',
                foreground=int(style_elem.get('foreground', '-13421773')) if style_elem.get('foreground') else None,
            )
            metadata.styles.append(style)
    
    # Extract elements resolver
    elements_element = root.find('elements')
    if elements_element is not None:
        metadata.resolver = elements_element.get('resolver', 'hvl-default')
        
        # Extract header
        header_elem = elements_element.find('header')
        if header_elem is not None:
            metadata.header = _parse_header_footer(header_elem, content_text)
        
        # Extract footer
        footer_elem = elements_element.find('footer')
        if footer_elem is not None:
            metadata.footer = _parse_header_footer(footer_elem, content_text)
    
    return metadata


def _parse_header_footer(elem: ET.Element, content_text: str) -> HeaderFooter:
    """Parse header or footer element."""
    hf = HeaderFooter()
    
    bg = elem.get('background')
    if bg:
        try:
            hf.background_color = int(bg)
        except ValueError:
            pass
    
    fg = elem.get('foreground')
    if fg:
        try:
            hf.foreground_color = int(fg)
        except ValueError:
            pass
    
    for para_elem in elem.findall('paragraph'):
        para = _parse_paragraph_element(para_elem, content_text)
        hf.paragraphs.append(para)
    
    return hf


def _parse_paragraph_element(para_elem: ET.Element, content_text: str) -> ParagraphElement:
    """Parse a paragraph element."""
    alignment_val = para_elem.get('Alignment', '0')
    alignment_map = {'0': Alignment.LEFT, '1': Alignment.CENTER, '2': Alignment.RIGHT, '3': Alignment.JUSTIFY}
    
    para = ParagraphElement(
        alignment=alignment_map.get(alignment_val, Alignment.LEFT),
        left_indent=float(para_elem.get('LeftIndent', '0')),
        right_indent=float(para_elem.get('RightIndent', '0')),
        first_line_indent=float(para_elem.get('FirstLineIndent', '0')),
        line_spacing=float(para_elem.get('LineSpacing', '1.0')),
    )
    
    # Check for list properties
    if para_elem.get('Bulleted') == 'true':
        para.is_bulleted = True
        para.list_id = para_elem.get('ListId')
        para.list_level = int(para_elem.get('ListLevel', '1')) if para_elem.get('ListLevel') else None
        para.bullet_type = para_elem.get('BulletType')
    elif para_elem.get('Numbered') == 'true':
        para.is_numbered = True
        para.list_id = para_elem.get('ListId')
        para.list_level = int(para_elem.get('ListLevel', '1')) if para_elem.get('ListLevel') else None
        para.number_type = para_elem.get('NumberType')
    
    # Parse content elements
    for child in para_elem:
        if child.tag == 'content':
            start_offset = int(child.get('startOffset', '0'))
            length = int(child.get('length', '0'))
            text = content_text[start_offset:start_offset+length]
            
            style = TextStyle(
                font_family=child.get('family', 'Times New Roman'),
                font_size=float(child.get('size', '12')),
                bold=child.get('bold', 'false') == 'true',
                italic=child.get('italic', 'false') == 'true',
                underline=child.get('underline', 'false') == 'true',
            )
            fg = child.get('foreground')
            if fg:
                try:
                    style.foreground_color = int(fg)
                except ValueError:
                    pass
            
            content = ContentElement(
                text=text,
                start_offset=start_offset,
                length=length,
                style=style,
                element_type='content',
            )
            para.contents.append(content)
        
        elif child.tag == 'field':
            start_offset = int(child.get('startOffset', '0'))
            length = int(child.get('length', '0'))
            text = content_text[start_offset:start_offset+length] if length > 0 else child.get('fieldName', '')
            
            style = TextStyle(
                font_family=child.get('family', 'Times New Roman'),
                font_size=float(child.get('size', '12')),
                bold=child.get('bold', 'false') == 'true',
                italic=child.get('italic', 'false') == 'true',
                underline=child.get('underline', 'false') == 'true',
            )
            
            content = ContentElement(
                text=text,
                start_offset=start_offset,
                length=length,
                style=style,
                element_type='field',
                field_name=child.get('fieldName'),
            )
            para.contents.append(content)
        
        elif child.tag == 'space':
            content = ContentElement(
                text=' ',
                start_offset=int(child.get('startOffset', '0')),
                length=1,
                element_type='space',
            )
            para.contents.append(content)
        
        elif child.tag == 'tab':
            content = ContentElement(
                text='\t',
                start_offset=int(child.get('startOffset', '0')),
                length=1,
                element_type='tab',
            )
            para.contents.append(content)
        
        elif child.tag == 'image':
            content = ContentElement(
                text='\uFFFC',  # Object Replacement Character
                start_offset=int(child.get('startOffset', '0')),
                length=1,
                element_type='image',
                image_data=child.get('imageData'),
                image_width=int(child.get('width', '100')) if child.get('width') else None,
                image_height=int(child.get('height', '100')) if child.get('height') else None,
            )
            para.contents.append(content)
    
    return para


def _parse_table_element(table_elem: ET.Element, content_text: str) -> TableElement:
    """Parse a table element."""
    table = TableElement(
        column_count=int(table_elem.get('columnCount', '1')),
        column_spans=table_elem.get('columnSpans'),
        border=table_elem.get('border', 'borderCell'),
        table_name=table_elem.get('tableName', 'Sabit'),
    )
    
    for row_elem in table_elem.findall('row'):
        row = TableRow(
            row_name=row_elem.get('rowName'),
            row_type=row_elem.get('rowType', 'dataRow'),
        )
        if row_elem.get('height_min'):
            row.height_min = float(row_elem.get('height_min'))
        
        for cell_elem in row_elem.findall('cell'):
            cell = TableCell()
            for para_elem in cell_elem.findall('paragraph'):
                para = _parse_paragraph_element(para_elem, content_text)
                cell.paragraphs.append(para)
            row.cells.append(cell)
        
        table.rows.append(row)
    
    return table


def create_udf_bytes(content_xml: str) -> bytes:
    """
    Create UDF file bytes from content XML.
    
    Args:
        content_xml: The content.xml content as string
        
    Returns:
        bytes: The UDF file as ZIP bytes
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr('content.xml', content_xml.encode('utf-8'))
    buffer.seek(0)
    return buffer.read()


def _is_zip_file_path(file_path: str) -> bool:
    """Check if a file path points to a valid ZIP file."""
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            return True
    except (zipfile.BadZipFile, FileNotFoundError):
        return False


def _is_zip_bytes(data: bytes) -> bool:
    """Check if bytes represent a ZIP file."""
    try:
        with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
            return True
    except zipfile.BadZipFile:
        return False
