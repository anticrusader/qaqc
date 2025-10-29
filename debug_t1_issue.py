import PyPDF2
import re

def debug_t1_revision_issue():
    """Debug why T1 is not being detected as latest revision"""
    pdf_path = "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf"
    
    print(f"=== DEBUGGING T1 REVISION ISSUE: {pdf_path} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            print("Looking for ALL revision entries:")
            revisions_found = []
            
            for i, line in enumerate(lines):
                # Look for T0, T1, or any revision patterns
                if re.search(r'\b[T][0-9]\b', line):
                    print(f"Line {i}: {line}")
                    
                    # Check if it's a revision entry
                    patterns = [
                        r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)',
                        r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z\s]*FOR\s+[A-Z\s]+)',
                        r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z]+)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            rev = match.group(1)
                            date = match.group(2)
                            reason = match.group(3).strip()
                            revisions_found.append({
                                'revision': rev,
                                'date': date,
                                'reason': reason,
                                'line_index': i,
                                'full_line': line
                            })
                            print(f"  -> FOUND REVISION: {rev} | {date} | {reason}")
            
            print(f"\n=== SUMMARY ===")
            print(f"Total revisions found: {len(revisions_found)}")
            
            for rev in revisions_found:
                print(f"Rev: {rev['revision']} | Date: {rev['date']} | Line: {rev['line_index']} | Reason: {rev['reason']}")
            
            # Determine latest
            if revisions_found:
                revisions_found.sort(key=lambda x: x['line_index'])
                latest = revisions_found[-1]
                print(f"\nLATEST (by line position): {latest['revision']} at line {latest['line_index']}")
                
                # Also check by revision number
                t_revisions = [r for r in revisions_found if r['revision'].startswith('T')]
                if t_revisions:
                    t_revisions.sort(key=lambda x: int(x['revision'][1:]) if x['revision'][1:].isdigit() else 0)
                    highest_t = t_revisions[-1]
                    print(f"HIGHEST T revision: {highest_t['revision']}")
                
    except Exception as e:
        print(f"Error: {e}")

debug_t1_revision_issue()