import PyPDF2
import re

def find_correct_title(pdf_path):
    """Find the correct drawing title"""
    print(f"\n=== FINDING CORRECT TITLE: {pdf_path} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Look for lines containing "Mockup" or "External Wall" or "Façade"
            print("Lines containing key title words:")
            for i, line in enumerate(lines):
                if any(word in line.upper() for word in ['MOCKUP', 'MOCK-UP', 'EXTERNAL WALL', 'FACADE', 'FAÇADE']):
                    print(f"Line {i}: {line}")
            
            print("\nLines containing 'MEP Door':")
            for i, line in enumerate(lines):
                if 'MEP DOOR' in line.upper():
                    print(f"Line {i}: {line}")
            
            print("\nLines containing 'Detail':")
            for i, line in enumerate(lines):
                if 'DETAIL' in line.upper() and len(line) > 20:
                    print(f"Line {i}: {line}")
            
            # Look for title block area
            print("\nLooking for title block (lines with drawing info):")
            for i, line in enumerate(lines):
                if any(pattern in line for pattern in ['L01-H01D01', 'FOS-00-XX', 'MUP-AR']):
                    print(f"Line {i}: {line}")
                    # Check surrounding lines
                    for j in range(max(0, i-3), min(len(lines), i+4)):
                        if j != i:
                            print(f"  Context {j}: {lines[j]}")
                    break
                
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

find_correct_title("L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf")