import PyPDF2
import re
from datetime import datetime

def debug_specific_pdf(pdf_path):
    """Debug specific PDF extraction issues"""
    print(f"\n=== DEBUGGING: {pdf_path} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                print(f"\n--- PAGE {page_num + 1} ---")
                
                # Look for revision table patterns
                lines = text.split('\n')
                revision_section = False
                
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    
                    # Check if we're in revision section
                    if any(keyword in line_clean.upper() for keyword in ['REV', 'REVISION', 'DATE', 'REASON']):
                        revision_section = True
                        print(f"REVISION SECTION START: {line_clean}")
                        
                        # Print next 10 lines for context
                        for j in range(i, min(i+10, len(lines))):
                            context_line = lines[j].strip()
                            if context_line:
                                print(f"  {j-i}: {context_line}")
                        break
                
                # Look for table title patterns
                print(f"\n--- LOOKING FOR TABLE TITLES ---")
                for i, line in enumerate(lines):
                    line_clean = line.strip().upper()
                    if any(word in line_clean for word in ['CONSTRUCTION', 'PROCUREMENT', 'DEVELOPMENT']):
                        print(f"POTENTIAL TITLE: {line.strip()}")
                        # Show context
                        for j in range(max(0, i-2), min(i+3, len(lines))):
                            print(f"  Context {j-i}: {lines[j].strip()}")
                        print()
                
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

# Debug the problematic files
debug_specific_pdf("L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf")
debug_specific_pdf("L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0] - Sample Sketch.pdf")