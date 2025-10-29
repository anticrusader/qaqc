import PyPDF2
import re
import csv
import os
from datetime import datetime

def extract_pdf_info(pdf_path):
    """Hybrid dynamic PDF extraction"""
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
            
            # Extract drawing number and revision from filename
            filename = os.path.basename(pdf_path)
            filename_match = re.search(r'([A-Z0-9\-]+)\[([A-Z0-9]+)\]', filename)
            if filename_match:
                result['drawing_number'] = filename_match.group(1)
                result['revision'] = filename_match.group(2)
            
            # HYBRID DYNAMIC TITLE EXTRACTION
            result['drawing_title'] = extract_title_hybrid_dynamic(lines)
            
            # REVISION DETECTION
            revisions = extract_revisions(lines)
            
            # Find the latest revision
            if revisions:
                revisions.sort(key=lambda x: x['line_index'])
                latest = revisions[-1]
                result['latest_revision'] = latest['revision']
                result['latest_date'] = latest['date']
                result['latest_reason'] = latest['reason']
            
            # Apply business rules for latest_reason based on revision code
            if result['latest_revision']:
                if result['latest_revision'].startswith('T'):
                    result['latest_reason'] = 'Issued for Tender'
                elif result['latest_revision'].startswith('N'):
                    result['latest_reason'] = 'Issued for Construction'
            elif result['revision']:  # Fallback to main revision if no latest found
                if result['revision'].startswith('T'):
                    result['latest_revision'] = result['revision']
                    result['latest_reason'] = 'Issued for Tender'
                elif result['revision'].startswith('N'):
                    result['latest_revision'] = result['revision']
                    result['latest_reason'] = 'Issued for Construction'
            
            # Apply business rules for table_title
            result['table_title'] = determine_table_title(lines, result['latest_revision'] or result['revision'])
            
            result['status'] = 'SUCCESS'
            
    except Exception as e:
        result['status'] = f'ERROR: {str(e)}'
    
    return result

def extract_title_hybrid_dynamic(lines):
    """Hybrid dynamic title extraction - combines structure-based and content-based approaches"""
    
    # Method 1: Enhanced "Drawing Title" approach with better filtering
    drawing_title_result = extract_title_from_label(lines)
    if drawing_title_result and is_valid_title_result(drawing_title_result):
        return drawing_title_result
    
    # Method 2: Content-based multi-line title detection (for cases like "Mockup External Wall...")
    content_based_result = extract_title_content_based(lines)
    if content_based_result and is_valid_title_result(content_based_result):
        return content_based_result
    
    # Method 3: Single comprehensive line detection
    single_line_result = extract_title_single_line(lines)
    if single_line_result and is_valid_title_result(single_line_result):
        return single_line_result
    
    return ''

def extract_title_from_label(lines):
    """Extract title using 'Drawing Title' label with improved filtering"""
    for i, line in enumerate(lines):
        if 'Drawing Title' in line:
            title_parts = []
            j = i + 1
            
            while j < len(lines) and j < i + 15:  # Extended search range
                next_line = lines[j].strip()
                
                # Enhanced stop conditions
                stop_patterns = [
                    'Model File Reference', 'Drawn By', 'Project No', 'Drawing Number', 
                    'Revision', 'Key Plan', 'Scale at ISO', 'Issue Date', 'Foster + Partners',
                    '© Foster', 'Riverside', 'London', 'www.', '.com'
                ]
                
                if any(pattern in next_line for pattern in stop_patterns):
                    break
                
                # Enhanced exclusion patterns
                if (re.match(r'^[0-9\.\s\-]+$', next_line) or
                    re.match(r'^L\d{2}-[A-Z0-9\-]+$', next_line) or
                    re.match(r'^[0-9]{3}-[0-9]{2}.*$', next_line) or
                    re.match(r'^HP\s+[0-9\.]+$', next_line) or
                    re.match(r'^[A-Z]{1,3}\s+[A-Z]{1,3}$', next_line) or
                    re.match(r'^[0-9]{2}/[0-9]{2}/[0-9]{2,4}', next_line) or
                    re.match(r'^Rev\.\s+Date', next_line) or
                    next_line.startswith('©')):
                    break
                
                # Include meaningful content with better validation
                if (next_line and 
                    len(next_line) > 8 and  # Minimum meaningful length
                    len(next_line) < 80 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', next_line) and  # Not all caps/codes
                    contains_title_like_content(next_line)):
                    
                    # Clean the line
                    cleaned_line = clean_title_line(next_line)
                    if cleaned_line and len(cleaned_line) > 5:
                        title_parts.append(cleaned_line)
                
                j += 1
            
            if title_parts:
                return ' '.join(title_parts).strip()
    
    return None

def extract_title_content_based(lines):
    """Extract title based on content patterns (multi-line titles like 'Mockup External Wall...')"""
    
    # Look for title starting patterns
    title_starters = ['Mockup', 'Mock-up']
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        
        if any(starter in line_clean for starter in title_starters):
            title_parts = [line_clean]
            
            # Collect subsequent title lines
            for j in range(i+1, min(i+6, len(lines))):
                next_line = lines[j].strip()
                
                # Stop at clear boundaries
                if (not next_line or
                    any(stop in next_line for stop in ['F+P', 'L01-', 'L02-', 'L04-', 'Drawing Number', '©']) or
                    re.match(r'^[0-9]{2}/[0-9]{2}/[0-9]{2,4}', next_line)):
                    break
                
                # Include if it looks like title content
                if (len(next_line) > 3 and 
                    len(next_line) < 60 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', next_line) and
                    contains_title_like_content(next_line)):
                    title_parts.append(next_line)
            
            if len(title_parts) >= 2:  # Multi-part title
                return ' '.join(title_parts)
    
    return None

def extract_title_single_line(lines):
    """Extract single comprehensive title lines"""
    for line in lines[:150]:  # Check more lines
        candidate = line.strip()
        
        if (candidate and 
            len(candidate) > 20 and 
            len(candidate) < 120 and
            contains_multiple_title_elements(candidate) and
            not contains_metadata_patterns(candidate)):
            return candidate
    
    return None

def contains_title_like_content(text):
    """Check if text contains title-like content (dynamic approach)"""
    text_upper = text.upper()
    
    # Title indicators (architectural/engineering terms)
    title_indicators = [
        # Building elements
        'WALL', 'SYSTEM', 'DOOR', 'WINDOW', 'FACADE', 'FAÇADE',
        # Drawing types
        'PLAN', 'SECTION', 'DETAIL', 'ELEVATION', 'LAYOUT', 'MOCKUP', 'MOCK-UP',
        # Technical terms
        'MEP', 'GRMS', 'PIPING', 'CONDUIT', 'POOL', 'ROOM',
        # Descriptors
        'TYPICAL', 'EXTERNAL', 'INTERNAL', 'OVERALL', 'GENERAL'
    ]
    
    return any(indicator in text_upper for indicator in title_indicators)

def contains_multiple_title_elements(text):
    """Check if text contains multiple title elements (for comprehensive titles)"""
    text_upper = text.upper()
    
    title_elements = [
        'MOCKUP', 'MOCK-UP', 'EXTERNAL', 'WALL', 'SYSTEM', 'TYPICAL', 
        'FACADE', 'FAÇADE', 'SECTION', 'DETAIL', 'MEP', 'DOOR', 
        'ROOM', 'GRMS', 'LAYOUT', 'POOL', 'PIPING', 'CONDUIT', 'PLAN'
    ]
    
    element_count = sum(1 for element in title_elements if element in text_upper)
    return element_count >= 2

def contains_metadata_patterns(text):
    """Check if text contains metadata patterns to exclude"""
    text_upper = text.upper()
    
    metadata_patterns = [
        'PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'REVISION', 
        'FOSTER', 'PARTNERS', 'RIVERSIDE', 'LONDON', '©', 'WWW', '.COM',
        'KEY PLAN', 'GENERAL NOTES', 'DRAWING NUMBER'
    ]
    
    return any(pattern in text_upper for pattern in metadata_patterns)

def clean_title_line(line):
    """Clean title line by removing prefixes and artifacts"""
    # Remove numeric prefixes
    cleaned = re.sub(r'^[0-9]+\.[0-9]+\s+', '', line)
    cleaned = re.sub(r'^[0-9]+\s+', '', cleaned)
    
    # Remove common artifacts
    cleaned = re.sub(r'^\W+', '', cleaned)  # Remove leading non-word chars
    cleaned = ' '.join(cleaned.split())  # Normalize spaces
    
    return cleaned.strip()

def is_valid_title_result(title):
    """Validate if the extracted title is reasonable"""
    if not title or len(title) < 10 or len(title) > 150:
        return False
    
    # Should not be mostly metadata
    if contains_metadata_patterns(title):
        return False
    
    # Should contain some title-like content
    return contains_title_like_content(title)

def extract_revisions(lines):
    """Extract revision information (same as before)"""
    revisions = []
    
    for i, line in enumerate(lines):
        patterns = [
            r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)',
            r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z\s]*FOR\s+[A-Z\s]+)',
            r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)(?:\s+([A-Z]{1,3}))?$'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                rev = match.group(1)
                date = match.group(2)
                reason = match.group(3).strip()
                
                if (len(rev) <= 3 and 
                    '/' in date and 
                    len(reason) > 3 and
                    not any(r['revision'] == rev and r['date'] == date for r in revisions)):
                    
                    revisions.append({
                        'revision': rev,
                        'date': date,
                        'reason': reason,
                        'line_index': i
                    })
    
    return revisions

def determine_table_title(lines, revision):
    """Determine table title based on business rules (same as before)"""
    valid_titles = [
        'Concept Design',
        'Schematic Design', 
        'Design Development',
        'Construction Documents',
        'Construction Procurement'
    ]
    
    for line in lines:
        line_upper = line.upper()
        for valid_title in valid_titles:
            if valid_title.upper() in line_upper:
                return valid_title
    
    if revision:
        if revision.startswith('T') or revision.startswith('N'):
            return 'Construction Procurement'
        else:
            for line in lines:
                line_upper = line.upper()
                if 'DEVELOPMENT' in line_upper:
                    return 'Design Development'
                elif 'CONSTRUCTION' in line_upper and 'DOCUMENT' in line_upper:
                    return 'Construction Documents'
            
            return 'Design Development'
    
    return ''

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
    
    output_file = 'pdf_extraction_results_hybrid_dynamic.csv'
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