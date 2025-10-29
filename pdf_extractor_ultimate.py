import PyPDF2
import re
import csv
import os
from datetime import datetime

def extract_pdf_info(pdf_path):
    """Ultimate PDF extraction with comprehensive pattern matching"""
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
            title_candidates = []
            for i, line in enumerate(lines[:100]):  # Check first 100 lines
                if (len(line) > 15 and 
                    len(line) < 100 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', line) and  # Not all caps/numbers
                    not re.match(r'^\d+[\.\s]', line) and  # Not starting with numbers
                    not any(word in line.upper() for word in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED', 'APPROVED'])):
                    
                    # Score based on content
                    score = 0
                    line_lower = line.lower()
                    
                    # Positive indicators
                    if any(word in line_lower for word in ['plan', 'layout', 'section', 'detail', 'elevation']):
                        score += 3
                    if any(word in line_lower for word in ['room', 'wall', 'system', 'building']):
                        score += 2
                    if re.search(r'\b(and|of|for|the)\b', line_lower):
                        score += 1
                    
                    # Negative indicators
                    if any(word in line_lower for word in ['scale', 'date', 'project', 'drawing']):
                        score -= 2
                    if len(line.split()) < 3:
                        score -= 1
                    
                    title_candidates.append((line, score, i))
            
            # Select best title
            if title_candidates:
                title_candidates.sort(key=lambda x: (-x[1], x[2]))  # Best score, earliest position
                if title_candidates[0][1] > 0:
                    result['drawing_title'] = title_candidates[0][0]
            
            # Comprehensive revision detection
            revisions = []
            
            # Method 1: Direct revision patterns
            for i, line in enumerate(lines):
                # Pattern: REV DATE REASON (with optional checker)
                patterns = [
                    r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)(?:\s+([A-Z]{1,3}))?',
                    r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z\s]*FOR\s+[A-Z\s]+)(?:\s+([A-Z]{1,3}))?',
                    r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)(?:\s+([A-Z]{1,3}))?$'
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        rev = match.group(1)
                        date = match.group(2)
                        reason = match.group(3).strip()
                        
                        # Clean up reason
                        reason = re.sub(r'\s+', ' ', reason)
                        reason = re.sub(r'^(ISSUED?\s+FOR\s+)', 'ISSUED FOR ', reason, flags=re.IGNORECASE)
                        
                        # Validate
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
            
            # Method 2: Table-style revisions (separate lines)
            for i in range(len(lines) - 5):
                # Look for revision code on its own line
                if re.match(r'^([A-Z0-9]{1,3})$', lines[i]):
                    rev = lines[i]
                    
                    # Look for date in next few lines
                    for j in range(i+1, min(i+4, len(lines))):
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', lines[j])
                        if date_match:
                            date = date_match.group(1)
                            
                            # Look for reason in nearby lines
                            for k in range(i+1, min(i+6, len(lines))):
                                reason_match = re.search(r'(ISSUED?\s+FOR\s+[A-Z\s]+|[A-Z\s]*FOR\s+[A-Z\s]+)', lines[k], re.IGNORECASE)
                                if reason_match:
                                    reason = reason_match.group(1).strip()
                                    
                                    if not any(r['revision'] == rev and r['date'] == date for r in revisions):
                                        revisions.append({
                                            'revision': rev,
                                            'date': date,
                                            'reason': reason,
                                            'line_index': i
                                        })
                                    break
                            break
            
            # Method 3: Look for embedded revisions in complex lines
            for i, line in enumerate(lines):
                # Special patterns for embedded revisions
                embedded_patterns = [
                    r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z]+)',
                    r'N0\s*(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)',
                    r'([A-Z0-9]{1,3})\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*([A-Z\s]*CONSTRUCTION[A-Z\s]*)'
                ]
                
                for pattern in embedded_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 3:
                            rev = match.group(1) if match.group(1) else result['revision']
                            date = match.group(2)
                            reason = match.group(3).strip()
                            
                            # Clean reason
                            if 'CONSTRUCTION' in reason.upper():
                                reason = 'ISSUED FOR CONSTRUCTION'
                            
                            if not any(r['revision'] == rev and r['date'] == date for r in revisions):
                                revisions.append({
                                    'revision': rev,
                                    'date': date,
                                    'reason': reason,
                                    'line_index': i
                                })
            
            # Find the latest revision (by line position - later = more recent)
            if revisions:
                revisions.sort(key=lambda x: x['line_index'])
                latest = revisions[-1]
                result['latest_revision'] = latest['revision']
                result['latest_date'] = latest['date']
                result['latest_reason'] = latest['reason']
            
            # Enhanced table title detection
            table_title_candidates = []
            
            for line in lines:
                line_upper = line.upper()
                
                # Look for key phrases
                if any(keyword in line_upper for keyword in ['CONSTRUCTION', 'PROCUREMENT', 'DEVELOPMENT', 'DESIGN']):
                    # Clean the line extensively
                    clean_line = line.strip()
                    
                    # Remove various prefixes
                    clean_line = re.sub(r'^[A-Z]{1,3}\s+[A-Z]{1,3}\s+', '', clean_line)  # "W W "
                    clean_line = re.sub(r'^\d{2}/\d{2}/\d{4}\s+[A-Z]{1,3}\s+', '', clean_line)  # Date + code
                    clean_line = re.sub(r'^\d{2}/\d{2}/\d{2}\s+\d:\d+', '', clean_line)  # Date + time
                    clean_line = re.sub(r'^\d+[\-\s]+', '', clean_line)  # Leading numbers
                    clean_line = re.sub(r'^[A-Z]{1,3}\s+\d{2}/\d{2}/\d{2,4}\s+', '', clean_line)  # Rev + date
                    
                    # Remove trailing codes
                    clean_line = re.sub(r'\s+[A-Z]{1,3}$', '', clean_line)
                    
                    # Fix spacing issues
                    clean_line = re.sub(r'(\w)([A-Z])', r'\1 \2', clean_line)  # Add space before caps
                    clean_line = re.sub(r'\s+', ' ', clean_line)  # Normalize spaces
                    clean_line = clean_line.strip()
                    
                    # Score the candidate
                    score = 0
                    clean_upper = clean_line.upper()
                    
                    if 'CONSTRUCTION' in clean_upper and 'PROCUREMENT' in clean_upper:
                        score += 5
                    elif 'CONSTRUCTION' in clean_upper or 'PROCUREMENT' in clean_upper:
                        score += 3
                    if 'DEVELOPMENT' in clean_upper:
                        score += 2
                    if len(clean_line.split()) <= 4:  # Prefer concise titles
                        score += 1
                    
                    # Penalize unwanted content
                    if any(word in clean_upper for word in ['DATE', 'SCALE', 'PROJECT', 'DRAWN', 'SHEET']):
                        score -= 3
                    if re.search(r'\d{2}/\d{2}/\d{2,4}', clean_line):  # Contains dates
                        score -= 2
                    
                    if score > 0 and len(clean_line) > 5:
                        table_title_candidates.append((clean_line, score))
            
            # Select best table title
            if table_title_candidates:
                table_title_candidates.sort(key=lambda x: -x[1])  # Sort by score descending
                result['table_title'] = table_title_candidates[0][0]
            
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
    output_file = 'pdf_extraction_results_ultimate.csv'
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