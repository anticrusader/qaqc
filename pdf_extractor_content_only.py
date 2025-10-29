import PyPDF2
import re
import csv
import os
from datetime import datetime

def extract_pdf_info(pdf_path):
    """Extract ALL information from PDF content only - NO filename parsing"""
    result = {
        'file_name': os.path.basename(pdf_path),
        'drawing_title': '',
        'drawing_number': '',
        'revision': '',
        'latest_revision': '',
        'latest_date': '',
        'latest_reason': '',
        'table_title': '',
        'status': 'FAILED'
    }
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page in reader.pages:
                all_text += page.extract_text() + "\n"
            
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Extract ALL information from PDF content only
            result['drawing_title'] = extract_title_from_content(lines)
            result['drawing_number'] = extract_drawing_number_from_content(lines)
            result['revision'] = extract_current_revision_from_content(lines)
            
            # Extract revision history and find latest
            revisions = extract_all_revisions_from_content(lines)
            if revisions:
                # Sort by line position (later = more recent) and by revision logic
                latest_revision = find_latest_revision(revisions)
                if latest_revision:
                    result['latest_revision'] = latest_revision['revision']
                    result['latest_date'] = latest_revision['date']
                    result['latest_reason'] = latest_revision['reason']
            
            # Apply business rules for latest_reason
            if result['latest_revision']:
                if result['latest_revision'].startswith('T'):
                    result['latest_reason'] = 'Issued for Tender'
                elif result['latest_revision'].startswith('N'):
                    result['latest_reason'] = 'Issued for Construction'
            
            # Extract table title from content
            result['table_title'] = extract_table_title_from_content(lines)
            
            result['status'] = 'SUCCESS'
            
    except Exception as e:
        result['status'] = f'ERROR: {str(e)}'
    
    return result

def extract_title_from_content(lines):
    """Extract drawing title from PDF content using multiple dynamic strategies"""
    
    # Strategy 1: Find "Drawing Title" label and extract following content
    for i, line in enumerate(lines):
        if 'Drawing Title' in line:
            title_parts = []
            j = i + 1
            
            while j < len(lines) and j < i + 15:
                next_line = lines[j].strip()
                
                # Stop at clear section boundaries
                if (not next_line or
                    any(boundary in next_line for boundary in [
                        'Model File Reference', 'Drawn By', 'Project No', 'Drawing Number',
                        'Revision', 'Key Plan', 'Scale at ISO', 'Issue Date', '© Foster',
                        'Riverside', 'London', 'www.', '.com', '+44'
                    ])):
                    break
                
                # Stop at technical patterns
                if (re.match(r'^[0-9\.\s\-]+$', next_line) or
                    re.match(r'^L\d{2}-[A-Z0-9\-]+$', next_line) or
                    re.match(r'^[0-9]{2}/[0-9]{2}/[0-9]{2,4}', next_line) or
                    re.match(r'^Rev\.\s+Date', next_line) or
                    next_line.startswith('©')):
                    break
                
                # Include meaningful title content
                if (len(next_line) > 5 and 
                    len(next_line) < 100 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', next_line) and
                    not any(exclude in next_line for exclude in ['©', 'Foster', 'Partners', 'Riverside', 'London'])):
                    
                    # Clean the line
                    cleaned = re.sub(r'^[0-9]+[\.\s]+', '', next_line)
                    if cleaned and len(cleaned) > 5:
                        title_parts.append(cleaned)
                
                j += 1
            
            if title_parts:
                return ' '.join(title_parts).strip()
    
    # Strategy 2: Look for multi-line title patterns
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        # Look for title starting indicators
        if any(starter in line_clean for starter in ['Mockup', 'Mock-up', 'Pool', 'Grading', 'Main']):
            title_parts = [line_clean]
            
            # Collect related lines
            for j in range(i+1, min(i+6, len(lines))):
                next_line = lines[j].strip()
                
                if (next_line and 
                    len(next_line) > 3 and 
                    len(next_line) < 80 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', next_line) and
                    not any(stop in next_line for stop in ['F+P', 'L01-', 'L02-', 'L04-', '©', 'Drawing Number'])):
                    title_parts.append(next_line)
                elif any(stop in next_line for stop in ['F+P', 'L01-', 'L02-', 'L04-', '©']):
                    break
            
            if len(title_parts) >= 2:
                return ' '.join(title_parts)
    
    # Strategy 3: Look for comprehensive single-line titles
    for line in lines[:200]:
        candidate = line.strip()
        if (candidate and 
            len(candidate) > 20 and 
            len(candidate) < 150 and
            not re.match(r'^[A-Z0-9\-\s\/]+$', candidate) and
            not any(exclude in candidate.upper() for exclude in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'REVISION', 'FOSTER', 'PARTNERS']) and
            any(indicator in candidate.upper() for indicator in ['PLAN', 'LAYOUT', 'SECTION', 'DETAIL', 'ELEVATION', 'ROOM', 'POOL', 'PIPING', 'CONDUIT'])):
            return candidate
    
    return ''

def extract_drawing_number_from_content(lines):
    """Extract drawing number from PDF content"""
    
    # Look for drawing number patterns in the content
    for line in lines:
        # Pattern: L##-######-###-##-##-###-##-##### (common architectural drawing number format)
        drawing_number_patterns = [
            r'(L\d{2}-[A-Z0-9]{6}-[A-Z0-9]{3}-[A-Z0-9]{2}-[A-Z0-9]{2}-[A-Z0-9]{3}-[A-Z0-9]{2}-[A-Z0-9]{5})',
            r'(L\d{2}-[A-Z0-9\-]+)',  # More flexible pattern
        ]
        
        for pattern in drawing_number_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
    
    return ''

def extract_current_revision_from_content(lines):
    """Extract current revision from PDF content"""
    
    # Look for revision indicators in title blocks or headers
    for line in lines[:100]:  # Check first 100 lines
        # Look for patterns like "Revision: T1" or "Rev: N0"
        rev_patterns = [
            r'Revision[:\s]+([A-Z0-9]{1,3})',
            r'Rev[:\s]+([A-Z0-9]{1,3})',
            r'Current Revision[:\s]+([A-Z0-9]{1,3})'
        ]
        
        for pattern in rev_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
    
    return ''

def extract_all_revisions_from_content(lines):
    """Extract all revisions from PDF content with enhanced detection"""
    revisions = []
    
    # Method 1: Standard revision table patterns
    for i, line in enumerate(lines):
        # Enhanced patterns for revision detection
        patterns = [
            # Standard format: REV DATE REASON
            r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)',
            r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z\s]*FOR\s+[A-Z\s]+)',
            # More flexible format
            r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)(?:\s+([A-Z]{1,3}))?$'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                rev = match.group(1)
                date = match.group(2)
                reason = match.group(3).strip()
                
                if is_valid_revision_entry(rev, date, reason):
                    # Avoid duplicates
                    if not any(r['revision'] == rev and r['date'] == date for r in revisions):
                        revisions.append({
                            'revision': rev,
                            'date': date,
                            'reason': reason,
                            'line_index': i
                        })
    
    # Method 2: Look for embedded revisions in complex lines
    for i, line in enumerate(lines):
        # Look for embedded patterns like "T1 07/11/2024 ISSUED FOR TENDER"
        embedded_patterns = [
            r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z]+)',
            r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)',
        ]
        
        for pattern in embedded_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                rev = match.group(1)
                date = match.group(2)
                reason = match.group(3).strip()
                
                if is_valid_revision_entry(rev, date, reason):
                    # Avoid duplicates
                    if not any(r['revision'] == rev and r['date'] == date for r in revisions):
                        revisions.append({
                            'revision': rev,
                            'date': date,
                            'reason': reason,
                            'line_index': i
                        })
    
    return revisions

def find_latest_revision(revisions):
    """Find the latest revision using multiple criteria"""
    if not revisions:
        return None
    
    # Sort by line index (later in document = more recent)
    revisions.sort(key=lambda x: x['line_index'])
    
    # For revisions with same prefix, prefer higher number/letter
    # T0 < T1 < T2, N0 < N1 < N2, etc.
    def revision_sort_key(rev_str):
        if len(rev_str) >= 2:
            prefix = rev_str[0]
            suffix = rev_str[1:]
            try:
                # Try to convert suffix to number for proper sorting
                return (prefix, int(suffix))
            except ValueError:
                # If suffix is not a number, use alphabetical sorting
                return (prefix, suffix)
        return (rev_str, 0)
    
    # Group by revision prefix and find the latest in each group
    revision_groups = {}
    for rev in revisions:
        prefix = rev['revision'][0] if rev['revision'] else ''
        if prefix not in revision_groups:
            revision_groups[prefix] = []
        revision_groups[prefix].append(rev)
    
    # Find the latest revision overall
    latest_candidates = []
    for prefix, group in revision_groups.items():
        # Sort within group and take the latest
        group.sort(key=lambda x: (revision_sort_key(x['revision']), x['line_index']))
        latest_candidates.append(group[-1])
    
    # Return the revision that appears latest in the document
    latest_candidates.sort(key=lambda x: x['line_index'])
    return latest_candidates[-1]

def is_valid_revision_entry(rev, date, reason):
    """Validate revision entry components"""
    return (len(rev) <= 3 and 
            '/' in date and 
            len(reason) > 3 and
            not any(word in reason.upper() for word in ['PROJECT', 'SCALE', 'DRAWN', 'MODEL']))

def extract_table_title_from_content(lines):
    """Extract table title from PDF content"""
    valid_titles = [
        'Concept Design',
        'Schematic Design', 
        'Design Development',
        'Construction Documents',
        'Construction Procurement'
    ]
    
    # Look for explicit title in document
    for line in lines:
        line_upper = line.upper()
        for valid_title in valid_titles:
            if valid_title.upper() in line_upper:
                return valid_title
    
    # Default based on content analysis
    for line in lines:
        line_upper = line.upper()
        if 'DEVELOPMENT' in line_upper and 'DESIGN' in line_upper:
            return 'Design Development'
        elif 'CONSTRUCTION' in line_upper and 'DOCUMENT' in line_upper:
            return 'Construction Documents'
        elif 'CONSTRUCTION' in line_upper and 'PROCUREMENT' in line_upper:
            return 'Construction Procurement'
    
    # Final fallback - assume Construction Procurement for T/N revisions
    return 'Construction Procurement'

def main():
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in current directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file}")
        result = extract_pdf_info(pdf_file)
        
        print(f"  ✓ Title: {result['drawing_title'][:50]}...")
        print(f"  ✓ Number: {result['drawing_number']}")
        print(f"  ✓ Revision: {result['revision']}")
        print(f"  ✓ Latest Rev: {result['latest_revision']}")
        print(f"  ✓ Latest Date: {result['latest_date']}")
        print(f"  ✓ Latest Reason: {result['latest_reason'][:30]}...")
        print(f"  ✓ Table Title: {result['table_title']}")
        
        results.append(result)
    
    output_file = 'pdf_extraction_results_content_only.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['file_name', 'drawing_title', 'drawing_number', 'revision', 
                     'latest_revision', 'latest_date', 'latest_reason', 'table_title', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Summary: {len([r for r in results if r['status'] == 'SUCCESS'])}/{len(results)} files processed successfully")

if __name__ == "__main__":
    main()