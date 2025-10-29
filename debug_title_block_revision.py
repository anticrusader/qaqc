import PyPDF2
import re

def debug_title_block_revision():
    """Debug revision detection in title blocks"""
    
    pdf_files = [
        "L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].pdf",
        "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf", 
        "L04-A04D02-CHP-16-00-DWG-SP-10001[N0].pdf"
    ]
    
    for pdf_path in pdf_files:
        print(f"\n{'='*60}")
        print(f"🔍 DEBUGGING: {pdf_path}")
        print(f"{'='*60}")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                all_text = ""
                
                for page in reader.pages:
                    all_text += page.extract_text() + "\n"
                
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                
                # Find "Drawing Number" and show surrounding context
                for i, line in enumerate(lines):
                    if 'Drawing Number' in line:
                        print(f"\n📋 Found 'Drawing Number' at line {i}:")
                        print(f"Line {i}: {line}")
                        
                        # Show context around Drawing Number
                        print(f"\n🔍 CONTEXT (lines {max(0, i-3)} to {min(len(lines), i+6)}):")
                        for j in range(max(0, i-3), min(len(lines), i+6)):
                            marker = ">>> " if j == i else "    "
                            print(f"{marker}{j:3d}: {lines[j]}")
                        
                        # Look for revision patterns in this area
                        print(f"\n🎯 REVISION SEARCH in title block area:")
                        for j in range(max(0, i-2), min(len(lines), i+5)):
                            candidate = lines[j].strip()
                            
                            # Check for revision patterns
                            if re.search(r'\b([TN]\d+)\b', candidate):
                                rev_matches = re.findall(r'\b([TN]\d+)\b', candidate)
                                print(f"  ✅ Line {j}: Found revisions {rev_matches} in: {candidate}")
                            
                            # Check for standalone revision
                            if re.match(r'^([TN]\d+)$', candidate):
                                print(f"  🎯 Line {j}: STANDALONE REVISION: {candidate}")
                        
                        break
                
                # Also look for "Revision" labels
                print(f"\n📝 Looking for 'Revision' labels:")
                for i, line in enumerate(lines):
                    if 'Revision' in line and 'Drawing Number' not in line and 'Key Plan' not in line:
                        print(f"  Line {i}: {line}")
                        
                        # Check surrounding lines
                        for j in range(max(0, i-1), min(len(lines), i+3)):
                            if j != i:
                                candidate = lines[j].strip()
                                if re.search(r'\b([TN]\d+)\b', candidate):
                                    rev_matches = re.findall(r'\b([TN]\d+)\b', candidate)
                                    print(f"    -> Line {j}: {rev_matches} in: {candidate}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_title_block_revision()