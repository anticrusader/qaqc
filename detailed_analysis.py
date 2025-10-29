import pdfplumber
import re
from pathlib import Path

def detailed_pdf_analysis(pdf_path):
    """
    Comprehensive analysis to understand exact PDF structure and expected values.
    """
    print(f"\n{'='*100}")
    print(f"DETAILED ANALYSIS: {pdf_path}")
    print(f"{'='*100}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            lines = text.split('\n')
            
            print(f"Total lines: {len(lines)}")
            
            # 1. Analyze Drawing Title section
            print("\n1. DRAWING TITLE ANALYSIS:")
            for i, line in enumerate(lines):
                if 'Drawing Title' in line:
                    print(f"  Header at line {i}: '{line.strip()}'")
                    print("  Following lines:")
                    for j in range(i+1, min(i+8, len(lines))):
                        print(f"    Line {j}: '{lines[j].strip()}'")
                    break
            
            # 2. Analyze Drawing Number/Revision section
            print("\n2. DRAWING NUMBER & REVISION ANALYSIS:")
            for i, line in enumerate(lines):
                if 'Drawing Number' in line and 'Revision' in line:
                    print(f"  Header at line {i}: '{line.strip()}'")
                    print("  Following lines:")
                    for j in range(i+1, min(i+5, len(lines))):
                        print(f"    Line {j}: '{lines[j].strip()}'")
                    break
            
            # 3. Analyze Revision Table
            print("\n3. REVISION TABLE ANALYSIS:")
            table_found = False
            for i, line in enumerate(lines):
                if 'Rev.' in line and 'Date' in line and ('Reason' in line or 'Issue' in line):
                    print(f"  Table header at line {i}: '{line.strip()}'")
                    table_found = True
                    
                    # Show all revision entries
                    print("  All revision entries (scanning 25 lines before header):")
                    for j in range(max(0, i-25), i):
                        entry_line = lines[j].strip()
                        # Look for revision patterns
                        if re.match(r'^[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', entry_line):
                            print(f"    Line {j}: '{entry_line}'")
                            # Check for continuation
                            for k in range(j+1, min(j+4, len(lines))):
                                cont_line = lines[k].strip()
                                if (cont_line and 
                                    not re.match(r'^[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', cont_line) and
                                    'Rev.' not in cont_line and
                                    len(cont_line) < 50):
                                    print(f"      Continuation at line {k}: '{cont_line}'")
                    
                    # Show table title candidates
                    print("  Table title candidates (5 lines after header):")
                    for j in range(i+1, min(i+6, len(lines))):
                        title_line = lines[j].strip()
                        if title_line:
                            print(f"    Line {j}: '{title_line}'")
                    break
            
            if not table_found:
                print("  No standard revision table found.")
                # Look for simple format
                for i, line in enumerate(lines):
                    if 'Drawing Number' in line and 'Revision' in line:
                        print(f"  Simple format found at line {i}: '{line.strip()}'")
                        # Look for dates and context
                        print("  Context (10 lines before and after):")
                        for j in range(max(0, i-10), min(len(lines), i+11)):
                            marker = ">>>" if j == i else "   "
                            print(f"  {marker} Line {j}: '{lines[j].strip()}'")
                        break
            
            # 4. Look for specific patterns mentioned in feedback
            print("\n4. SPECIFIC PATTERN SEARCH:")
            
            # Search for "Construction Procurement"
            print("  Searching for 'Construction Procurement' patterns:")
            for i, line in enumerate(lines):
                if 'construction' in line.lower() and 'procurement' in line.lower():
                    print(f"    Line {i}: '{line.strip()}'")
            
            # Search for "issued for approval"
            print("  Searching for 'issued for approval' patterns:")
            for i, line in enumerate(lines):
                if 'issued' in line.lower() and 'approval' in line.lower():
                    print(f"    Line {i}: '{line.strip()}'")
            
            # Search for "issued for construction"
            print("  Searching for 'issued for construction' patterns:")
            for i, line in enumerate(lines):
                if 'issued' in line.lower() and 'construction' in line.lower():
                    print(f"    Line {i}: '{line.strip()}'")
            
            # Search for "As Built Drawing"
            print("  Searching for 'As Built Drawing' patterns:")
            for i, line in enumerate(lines):
                if 'as built' in line.lower() and 'drawing' in line.lower():
                    print(f"    Line {i}: '{line.strip()}'")
            
    except Exception as e:
        print(f"Error analyzing {pdf_path}: {e}")

# Analyze specific problematic files
problematic_files = [
    "L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf",
    "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf", 
    "L01-O01C01-AIC-XX-XX-ABD-ST-10031[AA] - Sample of AS-BUILT Drawing.pdf"
]

for pdf_file in problematic_files:
    if Path(pdf_file).exists():
        detailed_pdf_analysis(pdf_file)