import PyPDF2
import re

def debug_complete_title(pdf_path):
    """Debug complete title extraction"""
    print(f"\n=== COMPLETE TITLE DEBUG: {pdf_path} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Find all lines with title components
            print("Lines containing title components:")
            title_components = ['MOCKUP', 'MOCK-UP', 'EXTERNAL', 'WALL', 'SYSTEM', 'TYPICAL', 'FACADE', 'FAÇADE', 'SECTION', 'DETAIL', 'MEP', 'DOOR']
            
            for i, line in enumerate(lines):
                for component in title_components:
                    if component in line.upper():
                        print(f"Line {i}: {line} (contains: {component})")
                        break
            
            print("\n=== LOOKING FOR CONSECUTIVE TITLE LINES ===")
            # Look for consecutive lines that form the complete title
            for i in range(len(lines) - 4):
                window = lines[i:i+5]  # Check 5 consecutive lines
                
                # Check if this window contains multiple title components
                combined_text = ' '.join(window).upper()
                component_count = sum(1 for comp in title_components if comp in combined_text)
                
                if component_count >= 4:  # If it has 4+ title components
                    print(f"\nPotential complete title block starting at line {i}:")
                    for j, line in enumerate(window):
                        print(f"  {i+j}: {line}")
                    print(f"Combined: {' '.join(window)}")
                    print(f"Component count: {component_count}")
            
            print("\n=== LOOKING NEAR DRAWING TITLE LABEL ===")
            for i, line in enumerate(lines):
                if 'DRAWING TITLE' in line.upper():
                    print(f"Found 'Drawing Title' at line {i}: {line}")
                    
                    # Check a wider range around this
                    start = max(0, i-10)
                    end = min(len(lines), i+50)
                    
                    print(f"Checking lines {start} to {end}:")
                    for j in range(start, end):
                        if any(comp in lines[j].upper() for comp in title_components):
                            print(f"  {j}: {lines[j]}")
                    break
                
    except Exception as e:
        print(f"Error: {e}")

debug_complete_title("L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf")