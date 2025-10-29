import PyPDF2
import re
import csv
import os
from datetime import datetime

def extract_pdf_info(pdf_path):
    """Extract ALL information from PDF content only - FIXED VERSION"""
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
            result['drawing_title'] = extract_title_from_content_fixed(lines)
            result['drawing_number'] = extract_drawing_number_from_content(lines)
            result['revision'] = extract_current_revision_from_content(lines)
            
            # Extract revision history and find latest (FIXED)
            revisions = extract_all_revisions_from_content_fixed(lines)
            if revisions:
                latest_revision = find_latest_revision_fixed(revisions)
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

def extract_title_from_content_fixed(lines):
    """FIXED: Extract drawing title from PDF content"""
    
    # Strategy 1: Look for actual title content in the document (not just after "Drawing Title" label)
    # Check the entire document for meaningful titles
    for line in lines:
        candidate = line.strip()
        
        # Look for comprehensive titles that contain multiple meaningful elements
        if (candidate and 
            len(candidate) > 20 and 
            len(candidate) < 150 and
            not re.match(r'^[A-Z0-9\-\s\/]+$', candidate) and  # Not all caps/codes
            not any(exclude in candidate.upper() for exclude in [
                'PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'REVISION', 'FOSTER', 'PARTNERS',
                'DRAWING NUMBER', 'KEY PLAN', 'GENERAL NOTES', 'MODEL FILE', 'RIVERSIDE', 'LONDON'
            ])):
            
            # Check if it contains title-like elements
            title_elements = ['POOL', 'ENLARGEMENT', 'PLAN', 'GRADING', 'DRAINAGE', 'PIPING', 'CONDUIT', 
                            'LAYOUT', 'MOCKUP', 'MOCK-UP', 'ROOM', 'GRMS', 'WALL', 'SYSTEM', 'FACADE', 
                            'SECTION', 'DETAIL', 'MEP', 'DOOR', 'MAIN', 'OVERALL']
            
            element_count = sum(1 for element in title_elements if element in candidate.upper())
            
            if element_count >= 2:  # Must have at least 2 title elements
                return candidate
    
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
    
    # Strategy 3: Look near "Drawing Title" label but with better filtering
    for i, line in enumerate(lines):
        if 'Drawing Title' in line:
            # Look in a wider range around the label
            for j in range(max(0, i-10), min(len(lines), i+20)):
                candidate = lines[j].strip()
                
                if (candidate and 
                    len(candidate) > 15 and 
                    len(candidate) < 100 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', candidate) and
                    not any(exclude in candidate for exclude in [
                        'Drawing Title', 'Project No', 'Drawing Number', 'Model File', 
                        'Drawn By', 'Checked By', 'Approved By', '©', 'Foster', 'Partners'
                    ]) and
                    any(indicator in candidate.upper() for indicator in [
                        'PLAN', 'LAYOUT', 'SECTION', 'DETAIL', 'POOL', 'GRADING', 'DRAINAGE', 
                        'PIPING', 'CONDUIT', 'MOCKUP', 'MOCK-UP', 'ROOM', 'GRMS'
                    ])):
                    return candidate
    
    return ''

def extract_all_revisions_from_content_fixed(lines):
    """FIXED: Extract all revisions with better duplicate handling"""
    revisions = []
    processed_entries = set()  # Track processed entries to avoid duplicates
    
    for i, line in enumerate(lines):
        # Look for revision entries in the line
        # Pattern for entries like "T0 26/10/2023 ISSUED FOR TENDER AK T1 07/11/2024 ISSUED FOR TENDER NQ"
        
        # Split complex lines that contain multiple revisions
        revision_segments = re.findall(r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]*?)(?=\s+[A-Z]{1,3}\s+\d{1,2}/\d{1,2}/\d{2,4}|$)', line, re.IGNORECASE)
        
        for match in revision_segments:
            rev = match[0]
            date = match[1]
            reason = match[2].strip()
            
            # Create unique key to avoid duplicates
            entry_key = f"{rev}_{date}_{reason[:20]}"
            
            if (entry_key not in processed_entries and
                is_valid_revision_entry(rev, date, reason)):
                
                processed_entries.add(entry_key)
                revisions.append({
                    'revision': rev,
                    'date': date,
                    'reason': reason,
                    'line_index': i
                })
        
        # Also try standard patterns
        standard_patterns = [
            r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+?)(?:\s+([A-Z]{1,3}))?$',
        ]
        
        for pattern in standard_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                rev = match.group(1)
                date = match.group(2)
                reason = match.group(3).strip()
                
                entry_key = f"{rev}_{date}_{reason[:20]}"
                
                if (entry_key not in processed_entries and
                    is_valid_revision_entry(rev, date, reason)):
                    
                    processed_entries.add(entry_key)
                    revisions.append({
                        'revision': rev,
                        'date': date,
                        'reason': reason,
                        'line_index': i
                    })
    
    return revisions

def find_latest_revision_fixed(revisions):
    """FIXED: Find the latest revision with proper logic"""
    if not revisions:
        return None
    
    # Remove any duplicates based on revision and date
    unique_revisions = []
    seen = set()
    
    for rev in revisions:
        key = (rev['revision'], rev['date'])
        if key not in seen:
            seen.add(key)
            unique_revisions.append(rev)
    
    if not unique_revisions:
        return None
    
    # Sort by revision number within same prefix (T0 < T1, N0 < N1, etc.)
    def revision_sort_key(rev_entry):
        rev_str = rev_entry['revision']
        line_idx = rev_entry['line_index']
        
        if len(rev_str) >= 2:
            prefix = rev_str[0]
            suffix = rev_str[1:]
            try:
                # Convert suffix to number for proper sorting
                return (prefix, int(suffix), line_idx)
            except ValueError:
                # If suffix is not a number, use alphabetical sorting
                return (prefix, suffix, line_idx)
        return (rev_str, 0, line_idx)
    
    # Sort all revisions
    unique_revisions.sort(key=revision_sort_key)
    
    # Return the highest revision (last in sorted order)
    return unique_revisions[-1]

def extract_drawing_number_from_content(lines):
    """Extract drawing number from PDF content"""
    for line in lines:
        # Look for drawing number patterns
        patterns = [
            r'(L\d{2}-[A-Z0-9]{6}-[A-Z0-9]{3}-[A-Z0-9]{2}-[A-Z0-9]{2}-[A-Z0-9]{3}-[A-Z0-9]{2}-[A-Z0-9]{5})',
            r'(L\d{2}-[A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
    
    return ''

def extract_current_revision_from_content(lines):
    """Extract current revision from PDF content"""
    for line in lines[:100]:
        rev_patterns = [
            r'Revision[:\s]+([A-Z0-9]{1,3})',
            r'Rev[:\s]+([A-Z0-9]{1,3})',
        ]
        
        for pattern in rev_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
    
    return ''

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
    
    # Default fallback
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
    
    output_file = 'pdf_extraction_results_fixed_final.csv'
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