"""
Data types and classes for UDF Toolkit.

This module provides data classes for representing UDF documents and their components,
enabling in-memory conversions while preserving document integrity for round-trip conversions.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class Alignment(Enum):
    """Text alignment options."""
    LEFT = "0"
    CENTER = "1"
    RIGHT = "2"
    JUSTIFY = "3"


class BulletType(Enum):
    """Bullet point types."""
    ELLIPSE = "BULLET_TYPE_ELLIPSE"
    RECTANGLE = "BULLET_TYPE_RECTANGLE"
    RECTANGLE_D = "BULLET_TYPE_RECTANGLE_D"
    ARROW = "BULLET_TYPE_ARROW"
    DIAMOND = "BULLET_TYPE_DIAMOND"
    TRIANGLE = "BULLET_TYPE_TRIANGLE"


@dataclass
class TextStyle:
    """Text styling information."""
    font_family: str = "Times New Roman"
    font_size: float = 12.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    foreground_color: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "foreground_color": self.foreground_color,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextStyle":
        """Create from dictionary."""
        return cls(
            font_family=data.get("font_family", "Times New Roman"),
            font_size=data.get("font_size", 12.0),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
            underline=data.get("underline", False),
            foreground_color=data.get("foreground_color"),
        )


@dataclass
class ContentElement:
    """A content element within a paragraph."""
    text: str
    start_offset: int
    length: int
    style: TextStyle = field(default_factory=TextStyle)
    element_type: str = "content"  # content, field, space, image, tab
    
    # For field elements
    field_name: Optional[str] = None
    
    # For image elements
    image_data: Optional[str] = None  # Base64 encoded
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "text": self.text,
            "start_offset": self.start_offset,
            "length": self.length,
            "style": self.style.to_dict(),
            "element_type": self.element_type,
        }
        if self.field_name:
            result["field_name"] = self.field_name
        if self.image_data:
            result["image_data"] = self.image_data
            result["image_width"] = self.image_width
            result["image_height"] = self.image_height
        return result


@dataclass
class ParagraphElement:
    """A paragraph element in the UDF document."""
    alignment: Alignment = Alignment.LEFT
    left_indent: float = 0.0
    right_indent: float = 0.0
    first_line_indent: float = 0.0
    line_spacing: float = 1.0
    contents: List[ContentElement] = field(default_factory=list)
    
    # List properties
    is_bulleted: bool = False
    is_numbered: bool = False
    list_id: Optional[str] = None
    list_level: Optional[int] = None
    bullet_type: Optional[str] = None
    number_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "alignment": self.alignment.value,
            "left_indent": self.left_indent,
            "right_indent": self.right_indent,
            "first_line_indent": self.first_line_indent,
            "line_spacing": self.line_spacing,
            "contents": [c.to_dict() for c in self.contents],
            "is_bulleted": self.is_bulleted,
            "is_numbered": self.is_numbered,
            "list_id": self.list_id,
            "list_level": self.list_level,
            "bullet_type": self.bullet_type,
            "number_type": self.number_type,
        }


@dataclass
class TableCell:
    """A cell in a table."""
    paragraphs: List[ParagraphElement] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "paragraphs": [p.to_dict() for p in self.paragraphs],
        }


@dataclass
class TableRow:
    """A row in a table."""
    cells: List[TableCell] = field(default_factory=list)
    row_name: Optional[str] = None
    row_type: str = "dataRow"
    height_min: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cells": [c.to_dict() for c in self.cells],
            "row_name": self.row_name,
            "row_type": self.row_type,
            "height_min": self.height_min,
        }


@dataclass
class TableElement:
    """A table element in the UDF document."""
    rows: List[TableRow] = field(default_factory=list)
    column_count: int = 1
    column_spans: Optional[str] = None
    border: str = "borderCell"
    table_name: str = "Sabit"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rows": [r.to_dict() for r in self.rows],
            "column_count": self.column_count,
            "column_spans": self.column_spans,
            "border": self.border,
            "table_name": self.table_name,
        }


@dataclass
class PageFormat:
    """Page format settings."""
    media_size_name: str = "1"
    left_margin: float = 42.52
    right_margin: float = 28.35
    top_margin: float = 14.17
    bottom_margin: float = 14.17
    paper_orientation: str = "1"  # 1=portrait, 2=landscape
    header_offset: float = 20.0
    footer_offset: float = 20.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "media_size_name": self.media_size_name,
            "left_margin": self.left_margin,
            "right_margin": self.right_margin,
            "top_margin": self.top_margin,
            "bottom_margin": self.bottom_margin,
            "paper_orientation": self.paper_orientation,
            "header_offset": self.header_offset,
            "footer_offset": self.footer_offset,
        }


@dataclass
class HeaderFooter:
    """Header or footer element."""
    paragraphs: List[ParagraphElement] = field(default_factory=list)
    background_color: Optional[int] = None
    foreground_color: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "background_color": self.background_color,
            "foreground_color": self.foreground_color,
        }


@dataclass
class StyleDefinition:
    """A style definition from the UDF document."""
    name: str
    description: Optional[str] = None
    family: str = "Times New Roman"
    size: float = 12.0
    bold: bool = False
    italic: bool = False
    foreground: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "family": self.family,
            "size": self.size,
            "bold": self.bold,
            "italic": self.italic,
            "foreground": self.foreground,
        }


@dataclass
class UDFMetadata:
    """
    Complete UDF document metadata extracted during conversion.
    
    This class preserves all UDF-specific information that may be lost during
    conversion to other formats, enabling accurate round-trip conversions.
    """
    format_id: str = "1.8"
    resolver: str = "hvl-default"
    page_format: PageFormat = field(default_factory=PageFormat)
    styles: List[StyleDefinition] = field(default_factory=list)
    header: Optional[HeaderFooter] = None
    footer: Optional[HeaderFooter] = None
    background_image_data: Optional[str] = None
    background_image_source: Optional[str] = None
    
    # Raw XML for elements that couldn't be fully parsed
    raw_elements_xml: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "format_id": self.format_id,
            "resolver": self.resolver,
            "page_format": self.page_format.to_dict(),
            "styles": [s.to_dict() for s in self.styles],
            "header": self.header.to_dict() if self.header else None,
            "footer": self.footer.to_dict() if self.footer else None,
            "background_image_data": self.background_image_data,
            "background_image_source": self.background_image_source,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "UDFMetadata":
        """Deserialize from JSON string."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UDFMetadata":
        """Create from dictionary."""
        page_format_data = data.get("page_format", {})
        page_format = PageFormat(
            media_size_name=page_format_data.get("media_size_name", "1"),
            left_margin=page_format_data.get("left_margin", 42.52),
            right_margin=page_format_data.get("right_margin", 28.35),
            top_margin=page_format_data.get("top_margin", 14.17),
            bottom_margin=page_format_data.get("bottom_margin", 14.17),
            paper_orientation=page_format_data.get("paper_orientation", "1"),
            header_offset=page_format_data.get("header_offset", 20.0),
            footer_offset=page_format_data.get("footer_offset", 20.0),
        )
        
        styles = []
        for style_data in data.get("styles", []):
            styles.append(StyleDefinition(
                name=style_data.get("name", ""),
                description=style_data.get("description"),
                family=style_data.get("family", "Times New Roman"),
                size=style_data.get("size", 12.0),
                bold=style_data.get("bold", False),
                italic=style_data.get("italic", False),
                foreground=style_data.get("foreground"),
            ))
        
        return cls(
            format_id=data.get("format_id", "1.8"),
            resolver=data.get("resolver", "hvl-default"),
            page_format=page_format,
            styles=styles,
            background_image_data=data.get("background_image_data"),
            background_image_source=data.get("background_image_source"),
        )


@dataclass
class ConversionResult:
    """
    Result of a UDF conversion operation.
    
    Contains both the converted output and the original UDF metadata,
    enabling round-trip conversions back to UDF format.
    """
    # The converted content
    content: Union[bytes, str]
    
    # Original UDF metadata for round-trip conversion
    metadata: UDFMetadata
    
    # The original content text from UDF
    original_text: str = ""
    
    # Elements that were extracted
    elements: List[Union[ParagraphElement, TableElement]] = field(default_factory=list)
    
    def get_metadata_json(self) -> str:
        """Get metadata as JSON string for storage/transmission."""
        return self.metadata.to_json()


# Type aliases for convenience
UDFInput = Union[str, bytes]  # File path or bytes content
