import PyPDF2
import re

def debug_numeric_revision():
    """Debug the numeric revision file L02-R02D01-FOS-00-XX-DWG-AR-00001[07]"""
    
    pdf_path = "L02-R02D01-FOS-00-XX-DWG-AR-00001[07].pdf"
    
    print(f"🔍 DEBUGGING NUMERIC REVISION: {pdf_path}")
    print("=" * 80)
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Look for "07" revision code
            print("🎯 SEARCHING FOR '07' REVISION:")
            found_07 = []
            
            for i, line in enumerate(lines):
                if '07' in line:
                    found_07.append((i, line))
            
            print(f"Found '07' in {len(found_07)} locations:")
            for i, (line_num, content) in enumerate(found_07[:10]):  # Show first 10
                print(f"\n📍 Location {i+1} - Line {line_num}:")
                print(f"   {content}")
            
            # Look for Drawing Number area
            print(f"\n📋 LOOKING FOR DRAWING NUMBER AREA:")
            for i, line in enumerate(lines):
                if 'Drawing Number' in line:
                    print(f"\nFound 'Drawing Number' at line {i}:")
                    print(f"Line {i}: {line}")
                    
                    # Show context
                    print(f"\nContext (lines {max(0, i-3)} to {min(len(lines), i+6)}):")
                    for j in range(max(0, i-3), min(len(lines), i+6)):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j:3d}: {lines[j]}")
                    break
            
            # Look for revision table/history
            print(f"\n📊 LOOKING FOR REVISION HISTORY:")
            revision_indicators = ['Rev', 'Date', 'Reason', 'Issue', 'Revision']
            
            for i, line in enumerate(lines):
                if any(indicator in line for indicator in revision_indicators):
                    print(f"\nFound revision indicator at line {i}: {line}")
                    
                    # Show context
                    for j in range(i, min(len(lines), i+10)):
                        print(f"  {j:3d}: {lines[j]}")
                    
                    # Look for numeric patterns in this area
                    for j in range(i, min(len(lines), i+10)):
                        if re.search(r'\b\d{2}\b', lines[j]):  # Look for 2-digit numbers
                            numbers = re.findall(r'\b\d{2}\b', lines[j])
                            print(f"    -> Found numbers: {numbers} in line {j}")
                    
                    print("-" * 40)
            
            # Look for any numeric revision patterns
            print(f"\n🔢 LOOKING FOR NUMERIC REVISION PATTERNS:")
            for i, line in enumerate(lines):
                # Look for patterns like "07 date reason" or "Rev 07"
                numeric_patterns = [
                    r'\b(0[0-9]|[0-9]{2})\s+(\d{1,2}/\d{1,2}/\d{2,4})',  # 07 07/03/2024
                    r'Rev[:\s]+(\d{2})',  # Rev: 07
                    r'Revision[:\s]+(\d{2})',  # Revision: 07
                ]
                
                for pattern in numeric_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        print(f"Line {i}: Found numeric pattern '{match.group()}' in: {line}")
            
            # Look for dates that might be associated with revision 07
            print(f"\n📅 LOOKING FOR DATES (potential revision dates):")
            for i, line in enumerate(lines):
                dates = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', line)
                if dates:
                    print(f"Line {i}: Found dates {dates} in: {line}")
                    
                    # Check if 07 is nearby
                    if '07' in line:
                        print(f"  -> This line also contains '07'!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_numeric_revision()