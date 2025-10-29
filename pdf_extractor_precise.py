import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info_precise(pdf_path):
    """
    Precise extractor based on detailed analysis of PDF structures.
    No hardcoding - uses dynamic pattern recognition.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            lines = text.split('\n')
            
            # Initialize results
            drawing_title = ""
            drawing_number = ""
            revision = ""
            latest_revision = ""
            latest_date = ""
            latest_reason = ""
            table_title = ""
            
            # 1. Extract Drawing Title
            for i, line in enumerate(lines):
                if 'Drawing Title' in line:
                    title_parts = []
                    j = i + 1
                    while j < len(lines) and j < i + 6:
                        next_line = lines[j].strip()
                        # Stop at section boundaries
                        if any(keyword in next_line for keyword in ['Model File Reference', 'Drawn By', 'Project No', 'Drawing Number']):
                            break
                        # Skip lines that look like references or codes
                        if (next_line and 
                            not next_line.startswith('Drawing') and
                            not re.match(r'^L\d{2}-[A-Z0-9\-]+$', next_line)):
                            title_parts.append(next_line)
                        j += 1
                    
                    if title_parts:
                        drawing_title = ' '.join(title_parts).strip()
                        break
            
            # 2. Extract Drawing Number and Revision from main table
            for i, line in enumerate(lines):
                if 'Drawing Number' in line and 'Revision' in line:
                    # Look at next few lines for values
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not any(keyword in next_line for keyword in ['Drawn By', 'Project No', 'Scale']):
                            # Try to extract both drawing number and revision
                            
                            # Pattern 1: Both on same line (DRAWING_NUMBER REVISION)
                            parts = next_line.split()
                            if len(parts) >= 2:
                                # Look for drawing number (long pattern with dashes)
                                for part in parts:
                                    if re.match(r'L\d{2}-[A-Z0-9\-]{20,}', part):
                                        drawing_number = part
                                        break
                                
                                # Look for revision (short alphanumeric at end)
                                if drawing_number:
                                    for part in reversed(parts):
                                        if (len(part) <= 3 and 
                                            re.match(r'^[A-Z0-9]+$', part) and 
                                            part != drawing_number.split('-')[-1]):
                                            revision = part
                                            break
                            
                            # Pattern 2: Separate lines
                            if not drawing_number or not revision:
                                # Check if this line has drawing number
                                if re.match(r'L\d{2}-[A-Z0-9\-]{20,}', next_line):
                                    drawing_number = next_line
                                # Check if this line has revision
                                elif len(next_line) <= 3 and re.match(r'^[A-Z0-9]+$', next_line):
                                    revision = next_line
                            
                            if drawing_number and revision:
                                break
                    break
            
            # 3. Extract Latest Revision Information from revision table
            revision_entries = []
            table_header_found = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                # Find revision table header
                if ('rev' in line_lower and 'date' in line_lower and 
                    ('reason' in line_lower or 'issue' in line_lower)):
                    table_header_found = True
                    
                    # Extract table title (look after header)
                    for j in range(i + 1, min(len(lines), i + 8)):
                        title_candidate = lines[j].strip()
                        # Table title characteristics: short, meaningful, not technical codes
                        if (title_candidate and 
                            2 < len(title_candidate) < 50 and
                            len(title_candidate.split()) <= 4 and
                            not re.match(r'^[0-9\.\-\s]+$', title_candidate) and
                            not any(skip in title_candidate.lower() for skip in 
                                   ['project', 'model', 'drawn', 'key plan', 'cover sheet', 'n/a', 'nts', 'scale'])):
                            table_title = title_candidate
                            break
                    
                    # Find revision entries (look before header)
                    for j in range(max(0, i - 20), i):
                        entry_line = lines[j].strip()
                        
                        # Match revision entry pattern: REV DATE REASON [CHK]
                        match = re.match(r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)(?:\s+([A-Z]{1,3}))?$', 
                                       entry_line, re.IGNORECASE)
                        
                        if match:
                            rev = match.group(1)
                            date = match.group(2)
                            reason = match.group(3).strip()
                            checker = match.group(4) if match.group(4) else ""
                            
                            # Validate entry
                            if len(rev) <= 3 and '/' in date and len(reason) > 2:
                                
                                # Look for continuation lines
                                full_reason = reason
                                for k in range(j + 1, min(len(lines), j + 4)):
                                    cont_line = lines[k].strip()
                                    
                                    # Stop at next revision entry or table boundary
                                    if (re.match(r'^[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{4}', cont_line) or
                                        'rev' in cont_line.lower() or
                                        not cont_line):
                                        break
                                    
                                    # Check if this is a valid continuation
                                    if (len(cont_line) < 40 and
                                        not re.search(r'\d{1,2}/\d{1,2}/\d{4}', cont_line) and
                                        not re.match(r'^[A-Z0-9]{1,3}\s', cont_line) and
                                        len(cont_line) > 1 and
                                        not any(skip in cont_line.lower() for skip in 
                                               ['project', 'drawing', 'model', 'key', 'cover', 'plan'])):
                                        full_reason += " " + cont_line
                                        break  # Only take first continuation line
                                
                                revision_entries.append({
                                    'revision': rev,
                                    'date': date,
                                    'reason': full_reason.strip(),
                                    'checker': checker,
                                    'line_number': j
                                })
                    break
            
            # Handle simple format if no revision table found
            if not table_header_found:
                for i, line in enumerate(lines):
                    if 'Drawing Number' in line and 'Revision' in line:
                        # Simple format - get revision from main table
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            parts = next_line.split()
                            if len(parts) >= 2:
                                # Last part is likely revision
                                potential_revision = parts[-1]
                                if len(potential_revision) <= 3 and re.match(r'^[A-Z0-9]+$', potential_revision):
                                    latest_revision = potential_revision
                                    
                                    # Look for date nearby
                                    for j in range(max(0, i-5), min(len(lines), i+3)):
                                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', lines[j])
                                        if date_match:
                                            latest_date = date_match.group(1)
                                            break
                                    
                                    # Infer reason from context
                                    context = ' '.join(lines[max(0, i-10):min(len(lines), i+10)]).lower()
                                    if 'approval' in context:
                                        latest_reason = "issued for approval"
                                    elif 'tender' in context:
                                        latest_reason = "issued for tender"
                                    else:
                                        latest_reason = "issued"
                                    
                                    # Find table title from context
                                    for j in range(max(0, i-15), min(len(lines), i+10)):
                                        title_line = lines[j].strip()
                                        if (len(title_line.split()) <= 4 and 5 < len(title_line) < 50 and
                                            any(word in title_line.lower() for word in ['built', 'construction', 'development'])):
                                            table_title = title_line
                                            break
                        break
            
            # Select latest revision (first entry = most recent)
            if revision_entries:
                latest_entry = min(revision_entries, key=lambda x: x['line_number'])
                latest_revision = latest_entry['revision']
                latest_date = latest_entry['date']
                latest_reason = latest_entry['reason']
            
            return {
                'file_name': os.path.basename(pdf_path),
                'drawing_title': drawing_title,
                'drawing_number': drawing_number,
                'revision': revision,
                'latest_revision': latest_revision,
                'latest_date': latest_date,
                'latest_reason': latest_reason,
                'table_title': table_title,
                'status': 'SUCCESS'
            }
            
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return {
            'file_name': os.path.basename(pdf_path),
            'drawing_title': 'ERROR',
            'drawing_number': 'ERROR',
            'revision': 'ERROR',
            'latest_revision': 'ERROR',
            'latest_date': 'ERROR',
            'latest_reason': 'ERROR',
            'table_title': 'ERROR',
            'status': f'ERROR: {str(e)}'
        }

def process_all_pdfs_precise(directory_path="."):
    """
    Process all PDF files using precise extraction.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info_precise(str(pdf_file))
        results.append(result)
        
        # Show progress
        if result['status'] == 'SUCCESS':
            print(f"  ✓ Title: {result['drawing_title'][:50]}...")
            print(f"  ✓ Number: {result['drawing_number']}")
            print(f"  ✓ Revision: {result['revision']}")
            print(f"  ✓ Latest Rev: {result['latest_revision']}")
            print(f"  ✓ Latest Date: {result['latest_date']}")
            print(f"  ✓ Latest Reason: {result['latest_reason'][:60]}...")
            print(f"  ✓ Table Title: {result['table_title']}")
        else:
            print(f"  ✗ Failed: {result['status']}")
        print()
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    
    # Save to CSV
    output_file = "pdf_extraction_results_precise.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    
    # Show summary
    successful = len(df[df['status'] == 'SUCCESS'])
    print(f"Summary: {successful}/{len(df)} files processed successfully")
    
    return df

if __name__ == "__main__":
    results = process_all_pdfs_precise()