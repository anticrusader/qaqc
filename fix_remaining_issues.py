import pdfplumber
import re

def analyze_specific_issues():
    """
    Analyze specific issues mentioned in feedback.
    """
    
    # Issue 1: L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf - missing T1 revision and wrong latest_revision
    print("="*80)
    print("ANALYZING L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf")
    print("="*80)
    
    with pdfplumber.open("L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf") as pdf:
        text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        
        print("Looking for T1 revision in Drawing Number Revision section:")
        for i, line in enumerate(lines):
            if 'Drawing Number' in line and 'Revision' in line:
                print(f"Header at line {i}: {line}")
                for j in range(i+1, min(i+5, len(lines))):
                    print(f"  Line {j}: '{lines[j]}'")
                    if 'T1' in lines[j]:
                        print(f"    *** T1 FOUND at line {j} ***")
        
        print("\nLooking for T1 in revision table:")
        for i, line in enumerate(lines):
            if 'T1' in line:
                print(f"Line {i}: '{line}'")
                # Check if this is a revision entry
                if re.match(r'^T1\s+\d{1,2}/\d{1,2}/\d{4}', line.strip()):
                    print(f"  *** T1 REVISION ENTRY FOUND at line {i} ***")
    
    # Issue 2: L02-R02DXX-RSG-00-ZZ-SKT-LS-12801[N0] - missing revision table entries
    print("\n" + "="*80)
    print("ANALYZING L02-R02DXX-RSG-00-ZZ-SKT-LS-12801[N0].pdf")
    print("="*80)
    
    with pdfplumber.open("L02-R02DXX-RSG-00-ZZ-SKT-LS-12801[N0] - Sample Sketch.pdf") as pdf:
        text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        
        print("Looking for revision table with N0 and 31/07/25:")
        for i, line in enumerate(lines):
            if 'N0' in line and '31/07' in line:
                print(f"Line {i}: '{line}'")
            elif 'issued for construction' in line.lower():
                print(f"Line {i}: '{line}' - FOUND 'issued for construction'")
        
        print("\nLooking for any date pattern 31/07/25:")
        for i, line in enumerate(lines):
            if '31/07' in line or '31/7' in line:
                print(f"Line {i}: '{line}'")
    
    # Issue 3: Drawing title issues
    print("\n" + "="*80)
    print("ANALYZING DRAWING TITLE ISSUES")
    print("="*80)
    
    # L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0]
    with pdfplumber.open("L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0] - Sample Sketch.pdf") as pdf:
        text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        
        print("L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0] - Looking for 'Grading and Drainage Plan 19/34':")
        for i, line in enumerate(lines):
            if 'Drawing Title' in line:
                print(f"Header at line {i}: {line}")
                for j in range(i+1, min(i+8, len(lines))):
                    print(f"  Line {j}: '{lines[j]}'")
                    if 'Grading and Drainage Plan' in lines[j]:
                        print(f"    *** FOUND at line {j} ***")

analyze_specific_issues()