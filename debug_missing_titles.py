import PyPDF2
import re

def debug_missing_titles():
    """Debug why some PDFs have missing titles"""
    
    pdf_files = [
        "L02-R02DXX-RSG-00-ZZ-SKT-LS-12801[N0] - Sample Sketch.pdf",
        "L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0] - Sample Sketch.pdf"
    ]
    
    for pdf_path in pdf_files:
        print(f"\n=== DEBUGGING MISSING TITLE: {pdf_path} ===")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                all_text = ""
                
                for page in reader.pages:
                    all_text += page.extract_text() + "\n"
                
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                
                print("Looking for 'Drawing Title' label:")
                for i, line in enumerate(lines):
                    if 'Drawing Title' in line:
                        print(f"Found at line {i}: {line}")
                        
                        # Show next 10 lines
                        print("Following lines:")
                        for j in range(i+1, min(i+11, len(lines))):
                            print(f"  {j}: {lines[j]}")
                        break
                else:
                    print("No 'Drawing Title' label found")
                
                print("\nLooking for potential title content (first 50 lines):")
                for i, line in enumerate(lines[:50]):
                    if (len(line) > 15 and 
                        not re.match(r'^[A-Z0-9\-\s\/]+$', line) and
                        any(word in line.upper() for word in ['PLAN', 'LAYOUT', 'SECTION', 'DETAIL', 'POOL', 'GRADING', 'DRAINAGE', 'PIPING', 'CONDUIT'])):
                        print(f"  Potential title at line {i}: {line}")
                
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

debug_missing_titles()