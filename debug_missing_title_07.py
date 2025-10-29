import PyPDF2
import re

def debug_missing_title():
    """Debug why title is missing for L02-R02D01-FOS-00-XX-DWG-AR-00001[07].pdf"""
    
    pdf_path = "L02-R02D01-FOS-00-XX-DWG-AR-00001[07].pdf"
    
    print(f"🔍 DEBUGGING MISSING TITLE: {pdf_path}")
    print("=" * 80)
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Look for "Drawing Title" label
            print("📋 LOOKING FOR 'Drawing Title' LABEL:")
            for i, line in enumerate(lines):
                if 'Drawing Title' in line:
                    print(f"\nFound 'Drawing Title' at line {i}: {line}")
                    
                    # Show extensive context
                    print(f"\nContext (lines {max(0, i-5)} to {min(len(lines), i+20)}):")
                    for j in range(max(0, i-5), min(len(lines), i+20)):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j:3d}: {lines[j]}")
                    break
            
            # Look for potential title content in first 100 lines
            print(f"\n📝 POTENTIAL TITLE CONTENT (first 100 lines):")
            potential_titles = []
            
            for i, line in enumerate(lines[:100]):
                if (len(line) > 15 and 
                    len(line) < 100 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', line) and
                    not re.match(r'^\d+[\.\s]', line) and
                    not any(exclude in line.upper() for exclude in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED', 'APPROVED', 'FOSTER', 'PARTNERS'])):
                    
                    potential_titles.append((i, line))
            
            print(f"Found {len(potential_titles)} potential titles:")
            for i, (line_num, content) in enumerate(potential_titles[:10]):  # Show first 10
                print(f"  {i+1}. Line {line_num}: {content}")
            
            # Look for specific title patterns
            print(f"\n🎯 LOOKING FOR SPECIFIC TITLE PATTERNS:")
            title_keywords = ['Technical', 'Project', 'Information', 'Cover', 'Sheet', 'Plan', 'Layout', 'Section', 'Detail']
            
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in title_keywords):
                    # Check if it looks like a title (not metadata)
                    if (len(line) > 10 and 
                        len(line) < 100 and
                        not any(exclude in line.upper() for exclude in ['FOSTER', 'PARTNERS', 'RIVERSIDE', 'LONDON', '©'])):
                        print(f"  Line {i}: {line}")
            
            # Look for lines that might be the actual title
            print(f"\n📖 COMPREHENSIVE TITLE SEARCH:")
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Look for lines that could be drawing titles
                if (line_clean and 
                    len(line_clean) > 20 and 
                    len(line_clean) < 150 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', line_clean) and
                    not any(exclude in line_clean.upper() for exclude in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'REVISION', 'FOSTER', 'PARTNERS', 'RIVERSIDE', 'LONDON', '©', 'WWW', '.COM'])):
                    
                    # Score based on title-like content
                    score = 0
                    line_upper = line_clean.upper()
                    
                    # Positive indicators
                    if any(word in line_upper for word in ['TECHNICAL', 'PROJECT', 'INFORMATION', 'COVER', 'SHEET']):
                        score += 3
                    if any(word in line_upper for word in ['PLAN', 'LAYOUT', 'SECTION', 'DETAIL', 'DRAWING']):
                        score += 2
                    if re.search(r'\b(AND|OF|FOR|THE)\b', line_upper):
                        score += 1
                    
                    if score >= 2:
                        print(f"  CANDIDATE (score {score}): Line {i}: {line_clean}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_missing_title()