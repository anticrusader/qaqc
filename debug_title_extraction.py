import PyPDF2
import re

def debug_title_extraction(pdf_path):
    """Debug title extraction for specific PDF"""
    print(f"\n=== DEBUGGING TITLE EXTRACTION: {pdf_path} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                print(f"\n--- PAGE {page_num + 1} ---")
                
                lines = text.split('\n')
                
                print("First 30 lines of text:")
                for i, line in enumerate(lines[:30]):
                    line_clean = line.strip()
                    if line_clean:
                        print(f"{i:2d}: {line_clean}")
                
                # Look for potential titles
                print(f"\n--- POTENTIAL TITLES ---")
                for i, line in enumerate(lines[:50]):
                    line_clean = line.strip()
                    if (len(line_clean) > 15 and 
                        len(line_clean) < 100 and
                        not re.match(r'^[A-Z0-9\-\s\/]+$', line_clean) and
                        not re.match(r'^\d+[\.\s]', line_clean) and
                        not any(word in line_clean.upper() for word in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED', 'APPROVED'])):
                        
                        print(f"Line {i}: {line_clean}")
                
                break  # Only check first page
                
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

# Debug the specific file
debug_title_extraction("L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf")