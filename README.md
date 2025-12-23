# UDF Toolkit
 UYAP UDF dosya formatı ile ilgili çalışmalar

[![Star History Chart](https://api.star-history.com/svg?repos=saidsurucu/udf-toolkit&type=Date)](https://www.star-history.com/#saidsurucu/udf-toolkit&Date)

## Installation / Kurulum

### Install from GitHub / GitHub'dan Kurulum
```bash
pip install git+https://github.com/tolgaerdonmez/UDF-Toolkit.git
```

### Install from source / Kaynaktan Kurulum
```bash
git clone https://github.com/tolgaerdonmez/UDF-Toolkit.git
cd UDF-Toolkit
pip install .
```

## Usage / Kullanım

### Command Line Interface / Komut Satırı

After installation, you can use the following commands:

Kurulumdan sonra aşağıdaki komutları kullanabilirsiniz:

## UDF dosyasını DOCX formatına çevirmek için
```
udf-to-docx input.udf
```
## UDF dosyasını PDF formatına çevirmek için
```
udf-to-pdf input.udf
```
## DOCX dosyasını UDF formatına çevirmek için
```
docx-to-udf input.docx
```
## UDF dosyasını Markdown formatına çevirmek için
```
udf-to-md input.udf
```
Not: En iyi sonucu almak için Windows'ta çalıştırılmalıdır. Bazı DOCX özelliklerini dönüştürmek için Windows kütüphaneleri gereklidir. MacOS ve Linux'ta sonuçlar farklı olabilir.
## PDF dosyasını (imaj olarak) UDF formatına çevirmek için
```
scanned-pdf-to-udf input.pdf
```

### Python Library / Python Kütüphanesi

The toolkit provides both in-memory conversion API and file-based functions.

Kütüphane hem bellek içi dönüşüm API'si hem de dosya tabanlı fonksiyonlar sunar.

#### In-Memory Conversion API (Recommended for Production)

The in-memory API accepts `str` (file path or XML content), or `bytes` as input and returns a `ConversionResult` object containing:
- `content`: The converted output as `bytes` or `str`
- `metadata`: `UDFMetadata` object preserving UDF-specific information for round-trip conversion
- `original_text`: The original text content from the UDF file

```python
from udf_toolkit import (
    convert_udf_to_docx,
    convert_udf_to_pdf,
    convert_udf_to_markdown,
    ConversionResult,
    UDFMetadata,
)

# Convert from file path
result = convert_udf_to_docx("document.udf")
docx_bytes = result.content  # bytes
metadata = result.metadata   # UDFMetadata object

# Convert from bytes (in-memory)
with open("document.udf", "rb") as f:
    udf_bytes = f.read()
result = convert_udf_to_pdf(udf_bytes)
pdf_bytes = result.content

# Convert to markdown
result = convert_udf_to_markdown("document.udf")
markdown_str = result.content  # str

# Save to file while also getting the result
result = convert_udf_to_docx("document.udf", output_path="output.docx")

# Get metadata for round-trip conversion back to UDF
metadata_json = result.get_metadata_json()
print(metadata_json)  # JSON string with all UDF-specific metadata
```

#### Working with UDF Metadata

The `UDFMetadata` class preserves all UDF-specific information that may be lost during conversion:

```python
from udf_toolkit import convert_udf_to_docx, UDFMetadata

result = convert_udf_to_docx("document.udf")
metadata = result.metadata

# Access page format settings
print(f"Left margin: {metadata.page_format.left_margin}")
print(f"Paper orientation: {metadata.page_format.paper_orientation}")

# Access style definitions
for style in metadata.styles:
    print(f"Style: {style.name}, Font: {style.family}, Size: {style.size}")

# Serialize metadata for storage
import json
metadata_dict = metadata.to_dict()
json_str = json.dumps(metadata_dict)

# Restore metadata later
restored_metadata = UDFMetadata.from_dict(json.loads(json_str))
```

#### Legacy File-Based API

For simple file-to-file conversions:

```python
from udf_toolkit import udf_to_docx, udf_to_pdf, udf_to_markdown, convert_docx_to_udf, pdf_to_udf

# Convert UDF to DOCX
udf_to_docx('input.udf', 'output.docx')

# Convert UDF to PDF
udf_to_pdf('input.udf', 'output.pdf')

# Convert UDF to Markdown
markdown_content = udf_to_markdown('input.udf')

# Convert DOCX to UDF
from udf_toolkit.main import convert
convert('input.docx', 'output.udf')

# Convert scanned PDF to UDF
pdf_to_udf('input.pdf', 'output.udf')
```
# Teknik Bilgiye Sahip Olmayanlar İçin Windows'ta Kullanım Talimatları

Bu scriptlerin düzgün çalışabilmesi için Python'un sisteminizde kurulu olması gerekmektedir. Aşağıdaki adımları takip ederek Python'u yükleyebilirsiniz:

1. [Python'un resmi web sitesine](https://www.python.org/downloads/) gidin.
2. Sisteminizin işletim sistemine uygun Python sürümünü indirin (genellikle en son sürüm önerilir).
3. Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin.

## Kodu İndirmek
Sağ üstteki yeşil renkli `Code` butonuna tıklayın. `Download ZIP`'e tıklayın. İnen sıkıştırılmış ZIP dosyasını bir klasöre çıkartın.

### 1. `install_requirements.bat`
- **Amaç**: `requirements.txt` dosyasında listelenen gerekli Python paketlerini yükler.
- **Nasıl Kullanılır**: `install_requirements.bat` scriptine çift tıklayın. Bu, `requirements.txt` dosyasında belirtilen tüm gerekli bağımlılıkları yükleyecektir.

### 1. `udf_to_docx.bat`
- **Amaç**: UDF dosyasını DOCX formatına dönüştürür.
- **Nasıl Kullanılır**: `.udf` dosyasını `udf_to_docx.bat` scriptinin üzerine sürükleyin. Script çalışacak ve girdi ile aynı dizinde bir `.docx` dosyası oluşturacaktır.

### 2. `udf_to_pdf.bat`
- **Amaç**: UDF dosyasını PDF formatına dönüştürür.
- **Nasıl Kullanılır**: `.udf` dosyasını `udf_to_pdf.bat` scriptinin üzerine sürükleyin. Script çalışacak ve girdi ile aynı dizinde bir `.pdf` dosyası oluşturacaktır.

### 3. `docx_to_udf.bat`
- **Amaç**: DOCX dosyasını UDF formatına dönüştürür.
- **Nasıl Kullanılır**: `.docx` dosyasını `docx_to_udf.bat` scriptinin üzerine sürükleyin. Script çalışacak ve girdi ile aynı dizinde bir `.udf` dosyası oluşturacaktır.

### 4. `scanned_pdf_to_udf.bat`
- **Amaç**: Tarama yapılmış bir PDF dosyasını UDF formatına dönüştürür.
- **Nasıl Kullanılır**: `.pdf` dosyasını `scanned_pdf_to_udf.bat` scriptinin üzerine sürükleyin. Script çalışacak ve girdi ile aynı dizinde bir `.udf` dosyası oluşturacaktır.


## UDF Formatı Dokümantasyonu
[Docs.md](./Docs.md)
