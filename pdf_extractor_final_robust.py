import PyPDF2
import re
import csv
import os
from datetime import datetime

def extract_pdf_info(pdf_path):
    """Extract information from PDF with robust revision detection"""
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
            
            # Enhanced drawing title extraction
            found_title = None
            
            # Method 1: Look for "Drawing Title" label and find the actual title nearby
            for i, line in enumerate(lines):
                if 'DRAWING TITLE' in line.upper():
                    # Found "Drawing Title" label, look for the actual title in surrounding lines
                    # Check lines after the label (within reasonable range)
                    for j in range(i+1, min(len(lines), i+50)):
                        candidate = lines[j].strip()
                        
                        # Look for lines that could be drawing titles
                        if (len(candidate) > 10 and 
                            len(candidate) < 100 and
                            any(keyword in candidate.upper() for keyword in ['MOCK-UP', 'MOCKUP', 'PLAN', 'LAYOUT', 'SECTION', 'DETAIL', 'ELEVATION']) and
                            not re.match(r'^[A-Z0-9\-\s\/]+$', candidate) and
                            not any(word in candidate.upper() for word in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED', 'APPROVED', 'REVISION'])):
                            
                            found_title = candidate
                            break
                    
                    if found_title:
                        break
            
            # Method 2: Look for title block pattern (multiple consecutive lines) - for first PDF type
            if not found_title:
                title_parts = []
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    
                    # Look for title block indicators
                    if any(keyword in line_clean.upper() for keyword in ['MOCKUP', 'MOCK-UP']):
                        # Found start of title, collect next few lines
                        potential_parts = [line_clean]
                        
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j].strip()
                            if (len(next_line) > 5 and 
                                len(next_line) < 50 and
                                not re.match(r'^[A-Z0-9\-\s]+$', next_line) and
                                not any(word in next_line.upper() for word in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED'])):
                                potential_parts.append(next_line)
                            elif len(next_line) < 3:  # Empty or very short line
                                continue
                            else:
                                break
                        
                        if len(potential_parts) >= 2:
                            title_parts = potential_parts
                            break
                
                if title_parts:
                    found_title = ' '.join(title_parts)
            
            # Method 3: Look for single comprehensive title line
            if not found_title:
                for line in lines:
                    line_clean = line.strip()
                    if (len(line_clean) > 15 and 
                        len(line_clean) < 150 and
                        any(keyword in line_clean.upper() for keyword in ['PLAN', 'SECTION', 'DETAIL', 'LAYOUT', 'ELEVATION']) and
                        not re.match(r'^[A-Z0-9\-\s\/]+$', line_clean) and
                        not any(word in line_clean.upper() for word in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED', 'APPROVED', 'REVISION'])):
                        
                        # Clean up the title
                        clean_title = re.sub(r'[^\w\s\-\(\)\/]', ' ', line_clean)
                        clean_title = ' '.join(clean_title.split())
                        
                        if len(clean_title) > 15:
                            found_title = clean_title
                            break
            
            # Set the drawing title
            if found_title:
                result['drawing_title'] = found_title
            
            # Enhanced revision detection
            revisions = []
            
            # Method 1: Look for clear revision table patterns
            for i, line in enumerate(lines):
                # Pattern for standard revision entries: REV DATE REASON
                rev_match = re.search(r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+|[A-Z\s]+FOR\s+[A-Z\s]+)', line, re.IGNORECASE)
                if rev_match:
                    rev = rev_match.group(1)
                    date = rev_match.group(2)
                    reason = rev_match.group(3).strip()
                    
                    # Clean up reason
                    reason = re.sub(r'\s+', ' ', reason)
                    reason = re.sub(r'^(ISSUED?\s+FOR\s+)', 'ISSUED FOR ', reason, flags=re.IGNORECASE)
                    
                    revisions.append({
                        'revision': rev,
                        'date': date,
                        'reason': reason,
                        'line_index': i
                    })
            
            # Method 2: Look for embedded revisions in complex lines
            for i, line in enumerate(lines):
                # Look for patterns like "T1 07/11/2024 ISSUED FOR TENDER"
                embedded_matches = re.finditer(r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z]+)', line, re.IGNORECASE)
                for match in embedded_matches:
                    rev = match.group(1)
                    date = match.group(2)
                    reason = match.group(3).strip()
                    
                    # Avoid duplicates
                    if not any(r['revision'] == rev and r['date'] == date for r in revisions):
                        revisions.append({
                            'revision': rev,
                            'date': date,
                            'reason': reason,
                            'line_index': i
                        })
            
            # Method 3: Look for table-style revisions (separate columns)
            for i in range(len(lines) - 2):
                current_line = lines[i]
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                
                # Check if current line has revision code
                rev_match = re.match(r'^([A-Z0-9]{1,3})$', current_line)
                if rev_match:
                    rev = rev_match.group(1)
                    
                    # Look for date in nearby lines
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', lines[j])
                        if date_match:
                            date = date_match.group(1)
                            
                            # Look for reason in nearby lines
                            for k in range(max(0, i-2), min(len(lines), i+3)):
                                reason_match = re.search(r'(ISSUED?\s+FOR\s+[A-Z\s]+)', lines[k], re.IGNORECASE)
                                if reason_match:
                                    reason = reason_match.group(1).strip()
                                    
                                    # Avoid duplicates
                                    if not any(r['revision'] == rev and r['date'] == date for r in revisions):
                                        revisions.append({
                                            'revision': rev,
                                            'date': date,
                                            'reason': reason,
                                            'line_index': i
                                        })
                                    break
                            break
            
            # Find the latest revision
            if revisions:
                # Sort by line index (later in document = more recent)
                revisions.sort(key=lambda x: x['line_index'])
                
                # Get the last revision
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
            
            # Apply business rules for table_title - must be one of the predefined values
            valid_table_titles = [
                'Concept Design',
                'Schematic Design', 
                'Design Development',
                'Construction Documents',
                'Construction Procurement'
            ]
            
            # Look for table title in document text
            found_title = None
            for line in lines:
                line_upper = line.upper()
                
                # Check for each valid title
                for valid_title in valid_table_titles:
                    if valid_title.upper() in line_upper:
                        found_title = valid_title
                        break
                
                if found_title:
                    break
            
            # If no specific title found, default based on revision type
            if not found_title:
                revision_to_check = result['latest_revision'] or result['revision']
                if revision_to_check:
                    if revision_to_check.startswith('T'):
                        found_title = 'Construction Procurement'
                    elif revision_to_check.startswith('N'):
                        found_title = 'Construction Procurement'
                    else:
                        # For numeric revisions (00, 01, 02, etc.), try to determine from content
                        for line in lines:
                            line_upper = line.upper()
                            if 'DEVELOPMENT' in line_upper:
                                found_title = 'Design Development'
                                break
                            elif 'CONSTRUCTION' in line_upper and 'DOCUMENT' in line_upper:
                                found_title = 'Construction Documents'
                                break
                        
                        # Default fallback
                        if not found_title:
                            found_title = 'Design Development'
            
            result['table_title'] = found_title if found_title else ''
            
            result['status'] = 'SUCCESS'
            
    except Exception as e:
        result['status'] = f'ERROR: {str(e)}'
    
    return result

def main():
    # Find all PDF files
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in current directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file}")
        result = extract_pdf_info(pdf_file)
        
        # Print results for verification
        print(f"  ✓ Title: {result['drawing_title'][:50]}...")
        print(f"  ✓ Number: {result['drawing_number']}")
        print(f"  ✓ Revision: {result['revision']}")
        print(f"  ✓ Latest Rev: {result['latest_revision']}")
        print(f"  ✓ Latest Date: {result['latest_date']}")
        print(f"  ✓ Latest Reason: {result['latest_reason'][:30]}...")
        print(f"  ✓ Table Title: {result['table_title']}")
        
        results.append(result)
    
    # Save to CSV
    output_file = 'pdf_extraction_results_final_robust.csv'
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