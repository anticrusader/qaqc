import PyPDF2
import re

def debug_second_pdf(pdf_path):
    """Debug the second PDF title extraction"""
    print(f"\n=== DEBUGGING: {pdf_path} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                print(f"\n--- PAGE {page_num + 1} ---")
                
                lines = text.split('\n')
                
                print("First 50 lines of text:")
                for i, line in enumerate(lines[:50]):
                    line_clean = line.strip()
                    if line_clean:
                        print(f"{i:2d}: {line_clean}")
                
                # Look for "Drawing Title" pattern
                print(f"\n--- LOOKING FOR DRAWING TITLE PATTERN ---")
                for i, line in enumerate(lines):
                    if 'DRAWING TITLE' in line.upper() or 'DRAWING TITLE' in line:
                        print(f"Found 'Drawing Title' at line {i}: {line}")
                        # Check next few lines
                        for j in range(i+1, min(i+5, len(lines))):
                            print(f"  Next line {j}: {lines[j].strip()}")
                        break
                
                # Look for "Mock-up" or "GRMS"
                print(f"\n--- LOOKING FOR MOCK-UP OR GRMS ---")
                for i, line in enumerate(lines):
                    if any(word in line.upper() for word in ['MOCK-UP', 'MOCKUP', 'GRMS']):
                        print(f"Found at line {i}: {line.strip()}")
                
                break  # Only check first page
                
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

# Debug the specific file
debug_second_pdf("L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf")