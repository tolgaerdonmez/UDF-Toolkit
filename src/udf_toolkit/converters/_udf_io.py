import zipfile
import xml.etree.ElementTree as ET


def is_zip_file(file_path: str) -> bool:
    try:
        with zipfile.ZipFile(file_path, 'r'):
            return True
    except zipfile.BadZipFile:
        return False


def load_udf_xml(file_path: str) -> ET.Element:
    root = None

    if is_zip_file(file_path):
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'content.xml' not in z.namelist():
                raise FileNotFoundError("The 'content.xml' file could not be found in the UDF file.")
            with z.open('content.xml') as content_file:
                tree = ET.parse(content_file, parser=ET.XMLParser(encoding='utf-8'))
                root = tree.getroot()
    else:
        try:
            tree = ET.parse(file_path, parser=ET.XMLParser(encoding='utf-8'))
            root = tree.getroot()
        except ET.ParseError as exc:
            raise ValueError(f"The file {file_path} is neither a valid ZIP nor a valid XML file.") from exc

    if root is None:
        raise ValueError("Failed to parse the file.")

    return root


def extract_content_text(root: ET.Element) -> str:
    content_element = root.find('content')
    if content_element is None:
        raise ValueError("'content' could not be found in the XML.")

    content_text = content_element.text or ""
    if content_text.startswith('<![CDATA[') and content_text.endswith(']]>'):
        content_text = content_text[9:-3]

    return content_text
