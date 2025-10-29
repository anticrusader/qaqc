import PyPDF2
import re

def find_all_revision_codes():
    """Find all T0, T1, N0 codes in the documents"""
    
    pdf_files = [
        ("L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf", "T0"),
        ("L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf", "T1"),
        ("L04-A04D02-CHP-16-00-DWG-SP-10001[N0].pdf", "N0")
    ]
    
    for pdf_path, expected_rev in pdf_files:
        print(f"\n{'='*60}")
        print(f"🔍 SEARCHING FOR '{expected_rev}' in: {pdf_path}")
        print(f"{'='*60}")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                all_text = ""
                
                for page in reader.pages:
                    all_text += page.extract_text() + "\n"
                
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                
                # Search for the expected revision code
                found_locations = []
                
                for i, line in enumerate(lines):
                    if expected_rev in line:
                        found_locations.append((i, line))
                
                print(f"📍 Found '{expected_rev}' in {len(found_locations)} locations:")
                
                for i, (line_num, line_content) in enumerate(found_locations):
                    print(f"\n🎯 Location {i+1} - Line {line_num}:")
                    print(f"   Content: {line_content}")
                    
                    # Show context
                    print(f"   Context:")
                    for j in range(max(0, line_num-2), min(len(lines), line_num+3)):
                        marker = ">>> " if j == line_num else "    "
                        print(f"   {marker}{j:3d}: {lines[j]}")
                
                # Also search for any T/N digit patterns
                print(f"\n🔍 All T/N digit patterns found:")
                all_patterns = []
                
                for i, line in enumerate(lines):
                    patterns = re.findall(r'\b([TN]\d+)\b', line)
                    if patterns:
                        all_patterns.extend([(i, line, patterns)])
                
                for line_num, line_content, patterns in all_patterns:
                    print(f"   Line {line_num}: {patterns} in: {line_content[:100]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_all_revision_codes()