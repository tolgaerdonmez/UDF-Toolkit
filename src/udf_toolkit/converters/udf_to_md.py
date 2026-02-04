from ._udf_io import extract_content_text, load_udf_xml


def convert(udf_file: str, md_file: str) -> None:
    root = load_udf_xml(udf_file)

    markdown_output = ""

    styles = {}

    styles_element = root.find('styles')
    if styles_element is not None:
        for style in styles_element.findall('style'):
            style_name = style.get('name')
            style_attributes = {
                'family': style.get('family'),
                'size': int(style.get('size', 12)),
                'bold': style.get('bold', 'false') == 'true',
                'italic': style.get('italic', 'false') == 'true',
                'foreground': int(style.get('foreground', '-13421773')),
            }
            styles[style_name] = style_attributes

    content_text = extract_content_text(root)

    elements_element = root.find('elements')
    if elements_element is not None:
        for elem in elements_element:
            if elem.tag == 'paragraph':
                paragraph_text = ""

                alignment = elem.get('Alignment', '0')
                alignment_tag = ""
                if alignment == '1':
                    alignment_tag = "<div align='center'>"
                elif alignment == '2':
                    alignment_tag = "<div align='right'>"
                elif alignment == '3':
                    alignment_tag = "<div align='justify'>"

                for child in elem:
                    if child.tag == 'content':
                        start_offset = int(child.get('startOffset', '0'))
                        length = int(child.get('length', '0'))
                        text = content_text[start_offset:start_offset+length]

                        if child.get('bold', 'false') == 'true' and child.get('italic', 'false') == 'true':
                            text = f"***{text}***"
                        elif child.get('bold', 'false') == 'true':
                            text = f"**{text}**"
                        elif child.get('italic', 'false') == 'true':
                            text = f"*{text}*"

                        paragraph_text += text

                    elif child.tag == 'space':
                        paragraph_text += " "
                    elif child.tag == 'image':
                        paragraph_text += "[Image]"

                if alignment_tag:
                    paragraph_text = f"{alignment_tag}{paragraph_text}</div>"

                markdown_output += paragraph_text + "\n\n"

            elif elem.tag == 'table':
                column_count = int(elem.get('columnCount', '1'))
                rows = elem.findall('row')

                markdown_output += "| " + " | ".join(["Column"] * column_count) + " |\n"
                markdown_output += "| " + " | ".join(["---"] * column_count) + " |\n"

                for row in rows:
                    cells = row.findall('cell')
                    row_text = "| "

                    for cell in cells:
                        cell_text = ""
                        paragraphs = cell.findall('paragraph')

                        for para in paragraphs:
                            para_text = ""

                            for child in para:
                                if child.tag == 'content':
                                    start_offset = int(child.get('startOffset', '0'))
                                    length = int(child.get('length', '0'))
                                    text = content_text[start_offset:start_offset+length]

                                    if child.get('bold', 'false') == 'true' and child.get('italic', 'false') == 'true':
                                        text = f"***{text}***"
                                    elif child.get('bold', 'false') == 'true':
                                        text = f"**{text}**"
                                    elif child.get('italic', 'false') == 'true':
                                        text = f"*{text}*"

                                    para_text += text

                                elif child.tag == 'space':
                                    para_text += " "

                            cell_text += para_text + " "

                        row_text += cell_text.strip() + " | "

                    markdown_output += row_text + "\n"

                markdown_output += "\n"

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(markdown_output)
