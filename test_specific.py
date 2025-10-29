import pdfplumber
import re

# Test the specific problematic PDF
pdf_path = "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf"

with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    
    print("Looking for drawing number pattern...")
    # Test the specific pattern for this drawing number
    pattern = r'(L01-H01D02-WSP-75-XX-MUP-IC-80301)'
    match = re.search(pattern, text)
    if match:
        print(f"Found drawing number: {match.group(1)}")
    else:
        print("Drawing number pattern not found")
        
    print("\nLooking for revision pattern...")
    # Test for T1 revision
    pattern = r'\b(T1)\b'
    match = re.search(pattern, text)
    if match:
        print(f"Found revision: {match.group(1)}")
    else:
        print("T1 revision not found")
        
    # Let's also check what's at the end of the text
    lines = text.split('\n')
    print(f"\nLast few lines:")
    for i, line in enumerate(lines[-5:]):
        print(f"{len(lines)-5+i}: {line}")
        
    # Check for the exact drawing number in the text
    if "L01-H01D02-WSP-75-XX-MUP-IC-80301" in text:
        print("\n✓ Drawing number IS in the text")
    else:
        print("\n✗ Drawing number NOT in text")
        
    if "T1" in text:
        print("✓ T1 IS in the text")
    else:
        print("✗ T1 NOT in text")