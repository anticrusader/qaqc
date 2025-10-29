# PDF Extractor for Architectural/Engineering Drawings

A comprehensive Python tool for extracting key information from architectural and engineering PDF drawings using Excel files as the source of truth.

## 🎯 Overview

This project extracts the following information from PDF drawings:
- **Drawing Title** - Complete descriptive title of the drawing
- **Drawing Number** - Standardized drawing identification number
- **Revision** - Current revision code (T0, T1, N0, 07, etc.)
- **Latest Revision** - Validated against PDF revision history table
- **Table Title** - Project phase (Concept Design, Schematic Design, Design Development, Construction Documents, Construction Procurement)

## 🚀 Key Features

- **Excel-Based Source of Truth**: Reads drawing metadata from Excel files (row 12)
- **PDF Content Validation**: Verifies all extracted data exists in PDF content
- **Smart Revision Formatting**: Handles single digits (7 → 07) automatically
- **UTF-8 Character Support**: Properly handles special characters (ç, é, etc.)
- **Excel-Friendly Output**: Preserves leading zeros in CSV files
- **100% Dynamic Extraction**: No hardcoded values, fully scalable
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## 📁 Project Structure

### Main Production Files
- **`pdf_extractor_excel_based.py`** - Main production extractor (RECOMMENDED)
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

### Development History Files
- `pdf_extractor_*.py` - Various development iterations
- `debug_*.py` - Debugging and analysis scripts
- `analyze_*.py` - Data analysis utilities
- `create_*.py` - CSV formatting utilities

### Output Files
- `pdf_extraction_results_*.csv` - Various extraction results
- `*.log` - Extraction logs

## 🛠 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd pdf-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 📋 Requirements

- Python 3.7+
- PyMuPDF (fitz)
- pandas
- openpyxl
- pathlib
- logging
- re

## 🎮 Usage

### Basic Usage

1. **Prepare your files**:
   - Place PDF files in the working directory
   - Ensure corresponding Excel files exist with same names (e.g., `drawing.pdf` → `drawing.xlsx`)
   - Excel files should have drawing metadata in row 12:
     - Column 1: Document Number
     - Column 2: Revision
     - Column 3: Title

2. **Run the extractor**:
   ```bash
   python pdf_extractor_excel_based.py
   ```

3. **Check results**:
   - Output: `pdf_extraction_results_excel_based_fixed.csv`
   - Logs: `pdf_extraction_excel_based.log`

### Advanced Usage

```python
from pdf_extractor_excel_based import process_single_pdf, process_all_pdfs_with_excel

# Process single PDF
result = process_single_pdf("drawing.pdf")

# Process all PDFs in directory
results = process_all_pdfs_with_excel()
```

## 📊 Input Format

### Excel File Structure (Row 12)
| Column | Field | Example |
|--------|-------|---------|
| A (1) | Document Number | L01-H01D01-FOS-00-XX-MUP-AR-80050 |
| B (2) | Revision | T0, N0, 7 (becomes 07) |
| C (3) | Title | Mockup External Wall Systems Typical Façade Section Details |

### Supported Revision Formats
- **Alphanumeric**: T0, T1, N0, N1, etc.
- **Numeric**: 1 → 01, 7 → 07, 15 → 15
- **Mixed**: Any combination of letters and numbers

## 📈 Output Format

### CSV Structure
```csv
file_name,drawing_title,drawing_number,revision,latest_revision,latest_date,latest_reason,table_title,status
drawing.pdf,Title Here,L01-H01D01-FOS-00-XX-MUP-AR-80050,'T0,'T0,,,Construction Procurement,SUCCESS
```

### Status Values
- **SUCCESS**: All fields extracted and validated
- **FAILED - Missing {field}**: Required field not found
- **FAILED - Revision mismatch**: Current revision ≠ latest revision
- **ERROR**: Processing error occurred

## 🔧 Configuration

### Logging Levels
Modify logging level in the script:
```python
logging.basicConfig(level=logging.INFO)  # INFO, DEBUG, WARNING, ERROR
```

### Table Title Options
The extractor recognizes these 5 standard project phases:
1. Concept Design
2. Schematic Design
3. Design Development
4. Construction Documents
5. Construction Procurement

## 🎯 Validation Logic

1. **Excel Data Reading**: Extracts Document Number, Revision, Title from row 12
2. **PDF Content Validation**: Verifies each field exists in PDF content
3. **Revision History Check**: Confirms revision exists in PDF revision table
4. **Format Validation**: Ensures all required fields are present
5. **Consistency Check**: Validates revision matches latest_revision

## 🚀 Production Features

- **Scalable**: Handles millions of PDFs with corresponding Excel files
- **Robust Error Handling**: Graceful failure with detailed error messages
- **Character Encoding**: Proper UTF-8 support for international characters
- **Excel Compatibility**: Leading zeros preserved in CSV output
- **Comprehensive Logging**: Full audit trail of extraction process

## 🐛 Troubleshooting

### Common Issues

1. **"Permission denied" error**:
   - Close Excel/CSV files before running
   - Check file permissions

2. **Character encoding issues**:
   - Use `pdf_results_method1_apostrophe.csv` for Excel
   - Try different encoding options provided

3. **Revision showing as number instead of "07"**:
   - Use files with apostrophe prefix (`'07`)
   - Open CSV in text editor to verify format

4. **Missing Excel file error**:
   - Ensure Excel file exists with same name as PDF
   - Check file extensions (.xlsx)

### Debug Mode
Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Development History

This project evolved through multiple iterations:

1. **Initial Extraction** (`pdf_extractor.py`) - Basic PDF text extraction
2. **Dynamic Approach** (`pdf_extractor_dynamic.py`) - Content-based extraction
3. **Validation Logic** (`pdf_extractor_with_tests.py`) - Added validation
4. **Production Ready** (`pdf_extractor_production_ready.py`) - Scalable version
5. **Excel-Based** (`pdf_extractor_excel_based.py`) - Final production version

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- PyMuPDF team for excellent PDF processing capabilities
- pandas team for data manipulation tools
- openpyxl team for Excel file handling

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for detailed error messages
3. Create an issue in the repository

---

**Version**: 4.0 Excel-Based Production Ready  
**Last Updated**: October 2025  
**Status**: Production Ready ✅