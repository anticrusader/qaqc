import pdfplumber
import re

# Debug the revision table extraction
pdf_path = "L02-R02D01-FOS-00-XX-DWG-AR-00001[07].pdf"

with pdfplumber.open(pdf_path) as pdf:
    # Try both pages
    text = ""
    for page_num, page in enumerate(pdf.pages):
        page_text = page.extract_text()
        print(f"=== PAGE {page_num + 1} TEXT ===")
        if page_text:
            text += f"\n--- PAGE {page_num + 1} ---\n" + page_text
        else:
            print(f"No text found on page {page_num + 1}")
    
    lines = text.split('\n')
    
    print("Looking for revision table...")
    
    # Find lines containing revision information
    revision_lines = []
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in ['T1', 'T0', 'ISSUED FOR TENDER', 'Issue for Tender', 'Rev.', 'Date', 'Reason For Issue', 'CONSTRUCTION', 'PROCUREMENT']):
            revision_lines.append((i, line.strip()))
    
    print("\nRevision-related lines:")
    for line_num, line_text in revision_lines:
        print(f"{line_num:3d}: {line_text}")
    
    print("\nAnalyzing lines around Rev. header...")
    header_found = False
    for i, line in enumerate(lines):
        if 'Rev.' in line and 'Date' in line and 'Reason For Issue' in line:
            print(f"Header found at line {i}: {line.strip()}")
            print("Lines around header:")
            for j in range(max(0, i-5), min(len(lines), i+8)):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {j:3d}: {lines[j].strip()}")
            header_found = True
            break
    
    if not header_found:
        print("Standard revision header not found. Looking for alternative patterns...")
        # Look for lines containing revision-like information
        print("\nLines with revision-related keywords:")
        for i, line in enumerate(lines):
            if any(keyword in line.upper() for keyword in ['REV', 'REVISION', 'DATE', 'ISSUE']):
                print(f"{i:3d}: {line.strip()}")
        
        print("\nLooking for potential revision entries (AA, numbers, dates)...")
        for i, line in enumerate(lines):
            # Look for patterns that might be revision entries
            if re.search(r'[A-Z]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', line) or 'AA' in line:
                print(f"{i:3d}: {line.strip()}")
        
        print("\nSearching for any approval-related terms...")
        approval_terms = ['approval', 'issued', 'built', 'drawing']
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(term in line_lower for term in approval_terms):
                print(f"{i:3d}: {line.strip()}")
        
        print("\nFull text search for 'AA' entries...")
        for i, line in enumerate(lines):
            if 'AA' in line and len(line.strip()) > 2:
                print(f"{i:3d}: {line.strip()}")
                # Show context
                for j in range(max(0, i-1), min(len(lines), i+2)):
                    if j != i:
                        print(f"    {j:3d}: {lines[j].strip()}")
        
        print("\nExamining lines around Drawing Number Revision...")
        for i, line in enumerate(lines):
            if 'Drawing Number' in line and 'Revision' in line:
                print(f"Found Drawing Number Revision header at line {i}")
                for j in range(max(0, i-3), min(len(lines), i+10)):
                    marker = ">>>" if j == i else "   "
                    print(f"{marker} {j:3d}: {lines[j].strip()}")
                break
    
    print("\nTrying to extract revision entries...")
    
    # Look for revision entry patterns
    revision_entries = []
    for i, line in enumerate(lines):
        # Multiple flexible patterns for revision entries
        patterns = [
            # Pattern 1: REV DATE REASON CHK (with checker)
            r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+([A-Z]{1,3})$',
            # Pattern 2: REV DATE REASON (no checker)
            r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+)$',
            # Pattern 3: Embedded in other text
            r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(Issue for Tender|ISSUED FOR TENDER|Design Development|100% Design Development|50% Design Development|100% Concept Design|100% Schematic Design|50% Schematic Design)',
        ]
        
        match = None
        for pattern in patterns:
            match = re.search(pattern, line.strip(), re.IGNORECASE)
            if match:
                break
        
        if match:
            print(f"Found revision entry at line {i}: {line.strip()}")
            print(f"  Rev: {match.group(1)}")
            print(f"  Date: {match.group(2)}")
            print(f"  Reason: {match.group(3)}")
            checker = match.group(4) if len(match.groups()) >= 4 else ""
            print(f"  Checker: {checker}")
            revision_entries.append({
                'line': i,
                'rev': match.group(1),
                'date': match.group(2),
                'reason': match.group(3),
                'checker': checker
            })
    
    print(f"\nFound {len(revision_entries)} revision entries")
    
    # Look for table title (like "Design Development")
    print("\nLooking for table title...")
    for i, line in enumerate(lines):
        if 'Rev.' in line and 'Date' in line and 'Reason For Issue' in line and 'Chk' in line:
            # Look for title below the header
            for j in range(i + 1, min(i + 5, len(lines))):
                title_line = lines[j].strip()
                if title_line and not any(keyword in title_line for keyword in ['Project', 'Drawing', 'Model', 'Drawn']):
                    print(f"Potential table title at line {j}: '{title_line}'")
            break
    
    if revision_entries:
        # Sort by line number
        sorted_entries = sorted(revision_entries, key=lambda x: x['line'])
        print("\nEntries sorted by line number (first = latest):")
        for entry in sorted_entries:
            print(f"Line {entry['line']}: {entry['rev']} - {entry['date']} - {entry['reason']}")
        
        print(f"\nLatest revision should be: {sorted_entries[0]['rev']}")
        print(f"Latest date should be: {sorted_entries[0]['date']}")
        print(f"Latest reason should be: {sorted_entries[0]['reason']}")
    else:
        print("No revision entries found with the current pattern")