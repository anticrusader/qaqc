import PyPDF2
import re
import csv
import os
from datetime import datetime

def extract_pdf_info(pdf_path):
    """Perfect PDF extraction with precise pattern matching"""
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
            for i, line in enumerate(lines[:100]):
                if (len(line) > 15 and 
                    len(line) < 100 and
                    not re.match(r'^[A-Z0-9\-\s\/]+$', line) and
                    not re.match(r'^\d+[\.\s]', line) and
                    not any(word in line.upper() for word in ['PROJECT', 'CLIENT', 'SCALE', 'DATE', 'DRAWN', 'CHECKED', 'APPROVED', 'SYMBOL', 'MOUNTING'])):
                    
                    score = 0
                    line_lower = line.lower()
                    
                    if any(word in line_lower for word in ['plan', 'layout', 'section', 'detail', 'elevation', 'mockup', 'mock-up']):
                        score += 3
                    if any(word in line_lower for word in ['room', 'wall', 'system', 'building', 'pool', 'grading', 'drainage']):
                        score += 2
                    if re.search(r'\b(and|of|for|the)\b', line_lower):
                        score += 1
                    
                    if any(word in line_lower for word in ['scale', 'date', 'project', 'drawing', 'symbol', 'mounting']):
                        score -= 2
                    if len(line.split()) < 3:
                        score -= 1
                    
                    title_candidates.append((line, score, i))
            
            if title_candidates:
                title_candidates.sort(key=lambda x: (-x[1], x[2]))
                if title_candidates[0][1] > 0:
                    result['drawing_title'] = title_candidates[0][0]
            
            # Precise revision detection
            revisions = []
            
            # Look for revision table patterns
            for i, line in enumerate(lines):
                # Clean the line for better matching
                clean_line = line.strip()
                
                # Pattern 1: Standard format "REV DATE REASON CHECKER"
                pattern1 = r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+((?:ISSUED?\s+FOR\s+)?[A-Z\s]+?)(?:\s+([A-Z]{1,3}))?$'
                match1 = re.match(pattern1, clean_line, re.IGNORECASE)
                
                if match1:
                    rev = match1.group(1)
                    date = match1.group(2)
                    reason = match1.group(3).strip()
                    
                    # Clean up reason
                    reason = re.sub(r'\s+', ' ', reason)
                    if not reason.upper().startswith('ISSUED'):
                        reason = 'ISSUED FOR ' + reason
                    
                    revisions.append({
                        'revision': rev,
                        'date': date,
                        'reason': reason,
                        'line_index': i
                    })
                    continue
                
                # Pattern 2: Embedded in complex lines
                pattern2 = r'\b([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z]+)'
                matches2 = re.finditer(pattern2, clean_line, re.IGNORECASE)
                
                for match in matches2:
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
                
                # Pattern 3: Special case for N0 revisions
                if result['revision'] == 'N0':
                    pattern3 = r'N0?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s+(ISSUED?\s+FOR\s+[A-Z\s]+)'
                    match3 = re.search(pattern3, clean_line, re.IGNORECASE)
                    
                    if match3:
                        date = match3.group(1)
                        reason = match3.group(2).strip()
                        
                        if not any(r['revision'] == 'N0' and r['date'] == date for r in revisions):
                            revisions.append({
                                'revision': 'N0',
                                'date': date,
                                'reason': reason,
                                'line_index': i
                            })
            
            # Find the latest revision (by line position)
            if revisions:
                # Remove duplicates and sort by line index
                unique_revisions = []
                seen = set()
                
                for rev in revisions:
                    key = (rev['revision'], rev['date'])
                    if key not in seen:
                        seen.add(key)
                        unique_revisions.append(rev)
                
                unique_revisions.sort(key=lambda x: x['line_index'])
                
                if unique_revisions:
                    latest = unique_revisions[-1]
                    result['latest_revision'] = latest['revision']
                    result['latest_date'] = latest['date']
                    result['latest_reason'] = latest['reason']
            
            # Clean table title detection
            table_title_candidates = []
            
            for line in lines:
                line_upper = line.upper()
                
                if any(keyword in line_upper for keyword in ['CONSTRUCTION', 'PROCUREMENT', 'DEVELOPMENT']):
                    clean_line = line.strip()
                    
                    # Remove prefixes systematically
                    clean_line = re.sub(r'^[A-Z]{1,3}\s+[A-Z]{1,3}\s+', '', clean_line)  # "W W "
                    clean_line = re.sub(r'^\d{2}/\d{2}/\d{2,4}\s+[A-Z]{1,3}\s+', '', clean_line)  # Date + code
                    clean_line = re.sub(r'^\d{2}/\d{2}/\d{2,4}\s+\d:\d+\s*', '', clean_line)  # Date + time
                    clean_line = re.sub(r'^\d+[\-\s]+', '', clean_line)  # Leading numbers
                    
                    # Fix spacing
                    clean_line = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_line)
                    clean_line = re.sub(r'\s+', ' ', clean_line)
                    clean_line = clean_line.strip()
                    
                    # Score
                    score = 0
                    clean_upper = clean_line.upper()
                    
                    if 'CONSTRUCTION' in clean_upper and 'PROCUREMENT' in clean_upper:
                        score += 5
                    elif 'CONSTRUCTION' in clean_upper or 'PROCUREMENT' in clean_upper:
                        score += 3
                    if 'DEVELOPMENT' in clean_upper:
                        score += 2
                    if len(clean_line.split()) <= 3:
                        score += 1
                    
                    # Penalties
                    if any(word in clean_upper for word in ['DATE', 'SCALE', 'PROJECT', 'DRAWN']):
                        score -= 3
                    if re.search(r'\d{2}/\d{2}/\d{2,4}', clean_line):
                        score -= 2
                    if len(clean_line) > 50:
                        score -= 1
                    
                    if score > 2 and len(clean_line) > 5:
                        table_title_candidates.append((clean_line, score))
            
            if table_title_candidates:
                table_title_candidates.sort(key=lambda x: -x[1])
                result['table_title'] = table_title_candidates[0][0]
            
            result['status'] = 'SUCCESS'
            
    except Exception as e:
        result['status'] = f'ERROR: {str(e)}'
    
    return result

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
    
    output_file = 'pdf_extraction_results_perfect.csv'
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