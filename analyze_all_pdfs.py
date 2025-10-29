import pdfplumber
import re
from pathlib import Path

def analyze_pdf_structure(pdf_path):
    """
    Analyze PDF structure to understand the exact layout and content.
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING: {pdf_path}")
    print(f"{'='*80}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            lines = text.split('\n')
            
            # Find Drawing Title
            print("\n1. DRAWING TITLE:")
            for i, line in enumerate(lines):
                if 'Drawing Title' in line:
                    print(f"  Header at line {i}: {line.strip()}")
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() and not any(keyword in lines[j] for keyword in ['Model File', 'Drawn By', 'Project No']):
                            print(f"  Content at line {j}: {lines[j].strip()}")
                    break
            
            # Find Drawing Number and Revision
            print("\n2. DRAWING NUMBER & REVISION:")
            for i, line in enumerate(lines):
                if 'Drawing Number' in line and 'Revision' in line:
                    print(f"  Header at line {i}: {line.strip()}")
                    for j in range(i+1, min(i+3, len(lines))):
                        if lines[j].strip():
                            print(f"  Content at line {j}: {lines[j].strip()}")
                    break
            
            # Find Revision Table
            print("\n3. REVISION TABLE:")
            table_found = False
            for i, line in enumerate(lines):
                if 'Rev.' in line and 'Date' in line and 'Reason For Issue' in line:
                    print(f"  Table header at line {i}: {line.strip()}")
                    table_found = True
                    
                    # Show entries above the header
                    print("  Revision entries:")
                    for j in range(max(0, i-15), i):
                        entry_line = lines[j].strip()
                        # Look for revision entry pattern
                        if re.match(r'^[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', entry_line):
                            print(f"    Line {j}: {entry_line}")
                            # Check next few lines for continuation
                            for k in range(j+1, min(j+3, len(lines))):
                                next_line = lines[k].strip()
                                if (next_line and 
                                    not re.match(r'^[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', next_line) and
                                    'Rev.' not in next_line and
                                    len(next_line) < 50):
                                    print(f"      Continuation at line {k}: {next_line}")
                    
                    # Show table title below header
                    print("  Table title candidates:")
                    for j in range(i+1, min(i+5, len(lines))):
                        title_line = lines[j].strip()
                        if (title_line and len(title_line) < 50 and 
                            not any(skip in title_line.lower() for skip in ['project', 'drawing', 'model', 'key plan'])):
                            print(f"    Line {j}: {title_line}")
                    break
            
            if not table_found:
                print("  No standard revision table found. Looking for simple format...")
                # Check for simple Drawing Number Revision format
                for i, line in enumerate(lines):
                    if 'Drawing Number' in line and 'Revision' in line:
                        print(f"  Simple format header at line {i}: {line.strip()}")
                        if i+1 < len(lines):
                            print(f"  Values at line {i+1}: {lines[i+1].strip()}")
                        
                        # Look for any date nearby
                        for j in range(max(0, i-3), min(i+3, len(lines))):
                            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', lines[j]):
                                print(f"  Date found at line {j}: {lines[j].strip()}")
                        break
            
    except Exception as e:
        print(f"Error analyzing {pdf_path}: {e}")

# Analyze all PDFs
# Focus on the problematic L02 file
analyze_pdf_structure("L02-R02D01-FOS-00-XX-DWG-AR-00001[07].pdf")