import pdfplumber
import re

def analyze_drawing_title_issues():
    """
    Analyze the drawing title extraction issues for the two problematic files.
    """
    
    files_to_analyze = [
        "L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435[N0] - Sample Sketch.pdf",
        "L04-A04D02-CHP-16-00-DWG-SP-10001[N0].pdf"
    ]
    
    for pdf_file in files_to_analyze:
        print(f"\n{'='*100}")
        print(f"ANALYZING DRAWING TITLE: {pdf_file}")
        print(f"{'='*100}")
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = pdf.pages[0].extract_text()
                lines = text.split('\n')
                
                print(f"Total lines: {len(lines)}")
                
                # Find Drawing Title section
                print("\nDRAWING TITLE SECTION:")
                for i, line in enumerate(lines):
                    if 'Drawing Title' in line:
                        print(f"  Header at line {i}: '{line.strip()}'")
                        print("  Following 10 lines:")
                        for j in range(i+1, min(i+11, len(lines))):
                            print(f"    Line {j}: '{lines[j].strip()}'")
                        break
                
                # Look for potential title patterns
                print("\nSEARCHING FOR TITLE PATTERNS:")
                
                # For L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435 - should be "Grading and Drainage Plan 19/34"
                if "L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435" in pdf_file:
                    print("  Looking for 'Grading and Drainage Plan' patterns:")
                    for i, line in enumerate(lines):
                        if 'grading' in line.lower() and 'drainage' in line.lower():
                            print(f"    Line {i}: '{line.strip()}'")
                
                # For L04-A04D02-CHP-16-00-DWG-SP-10001 - should be "Main Pool Piping & Conduit Overall Layout"
                if "L04-A04D02-CHP-16-00-DWG-SP-10001" in pdf_file:
                    print("  Looking for 'Main Pool Piping' patterns:")
                    for i, line in enumerate(lines):
                        if 'main pool' in line.lower() or ('pool' in line.lower() and 'piping' in line.lower()):
                            print(f"    Line {i}: '{line.strip()}'")
                    
                    print("  Looking for 'Overall Layout' patterns:")
                    for i, line in enumerate(lines):
                        if 'overall layout' in line.lower():
                            print(f"    Line {i}: '{line.strip()}'")
                
                # Show lines around Drawing Title that might contain the actual title
                print("\nCONTEXT ANALYSIS - Lines that might be the actual title:")
                for i, line in enumerate(lines):
                    if 'Drawing Title' in line:
                        # Look at lines around the header
                        for j in range(max(0, i-5), min(len(lines), i+15)):
                            line_text = lines[j].strip()
                            # Look for lines that could be titles (not too technical, reasonable length)
                            if (line_text and 
                                len(line_text) > 5 and 
                                len(line_text) < 100 and
                                not re.match(r'^[0-9\.\s\-]+$', line_text) and
                                not re.match(r'^L\d{2}-', line_text) and
                                not any(skip in line_text.lower() for skip in ['model file', 'drawn by', 'project no', 'scale'])):
                                print(f"    Candidate at line {j}: '{line_text}'")
                        break
                
        except Exception as e:
            print(f"Error analyzing {pdf_file}: {e}")

analyze_drawing_title_issues()