import pdfplumber
import re

# Debug the T1 file specifically
pdf_path = "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf"

with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    lines = text.split('\n')
    
    print("=== DEBUGGING T1 FILE ===")
    print(f"Total lines: {len(lines)}")
    
    # Find all T1 occurrences
    print("\n1. ALL T1 OCCURRENCES:")
    for i, line in enumerate(lines):
        if 'T1' in line:
            print(f"Line {i}: '{line.strip()}'")
    
    # Find all T0 occurrences  
    print("\n2. ALL T0 OCCURRENCES:")
    for i, line in enumerate(lines):
        if 'T0' in line:
            print(f"Line {i}: '{line.strip()}'")
    
    # Find revision table header and surrounding context
    print("\n3. REVISION TABLE CONTEXT:")
    for i, line in enumerate(lines):
        if 'Rev.' in line and 'Date' in line and 'Reason For Issue' in line:
            print(f"Header at line {i}: '{line.strip()}'")
            print("Context (10 lines before and after):")
            for j in range(max(0, i-10), min(len(lines), i+11)):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {j:3d}: '{lines[j].strip()}'")
            break
    
    # Look for revision entries with dates
    print("\n4. REVISION ENTRIES WITH DATES:")
    for i, line in enumerate(lines):
        if re.search(r'[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', line):
            print(f"Line {i}: '{line.strip()}'")
            # Check if this contains T1 or T0
            if 'T1' in line:
                print(f"  *** T1 ENTRY FOUND ***")
            elif 'T0' in line:
                print(f"  *** T0 ENTRY FOUND ***")
    
    # Look for "CONSTRUCTION PROCUREMENT" patterns
    print("\n5. CONSTRUCTION PROCUREMENT PATTERNS:")
    for i, line in enumerate(lines):
        if 'CONSTRUCTION' in line.upper() and 'PROCUREMENT' in line.upper():
            print(f"Line {i}: '{line.strip()}'")
            # Show context
            for j in range(max(0, i-2), min(len(lines), i+3)):
                if j != i:
                    print(f"    {j}: '{lines[j].strip()}'")