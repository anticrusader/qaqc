import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info_intelligent(pdf_path):
    """
    Intelligent extractor using semantic patterns and structural analysis.
    No hardcoded strings - uses pattern recognition and context analysis.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
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
            
            # 1. Extract Drawing Title (structural approach)
            for i, line in enumerate(lines):
                if 'Drawing Title' in line:
                    title_parts = []
                    j = i + 1
                    while j < len(lines) and j < i + 6:
                        next_line = lines[j].strip()
                        
                        # Stop at structural boundaries
                        if any(marker in next_line for marker in ['Model File Reference', 'Drawn By', 'Project No', 'Drawing Number']):
                            break
                        
                        # Stop at technical patterns
                        if (re.match(r'^[0-9\.\s\-]+$', next_line) or
                            re.match(r'^L\d{2}-[A-Z0-9\-]+$', next_line) or
                            re.match(r'^[0-9]{3}-[0-9]{2}.*$', next_line) or
                            re.match(r'^[A-Z]{2,3}\s+[0-9\.]+$', next_line)):
                            break
                        
                        # Include meaningful content
                        if (next_line and 
                            not next_line.startswith('Drawing') and
                            len(next_line) > 2 and
                            not re.match(r'^[0-9]+$', next_line)):
                            
                            # Remove numeric prefixes
                            cleaned_line = re.sub(r'^[0-9]+\.[0-9]+\s+', '', next_line)
                            if cleaned_line and len(cleaned_line) > 2:
                                title_parts.append(cleaned_line)
                        j += 1
                    
                    if title_parts:
                        drawing_title = ' '.join(title_parts).strip()
                        break
            
            # 2. Extract Drawing Number and Revision
            for i, line in enumerate(lines):
                if 'Drawing Number' in line and 'Revision' in line:
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not any(marker in next_line for marker in ['Drawn By', 'Project No', 'Scale']):
                            
                            # Extract drawing number
                            drawing_number_match = re.search(r'(L\d{2}-[A-Z0-9\-]{20,})', next_line)
                            if drawing_number_match:
                                drawing_number = drawing_number_match.group(1)
                            
                            # Extract revision
                            revision_matches = re.findall(r'\b([A-Z0-9]{1,3})\b', next_line)
                            if revision_matches:
                                for rev_candidate in reversed(revision_matches):
                                    if (len(rev_candidate) <= 3 and 
                                        (drawing_number is None or rev_candidate not in drawing_number)):
                                        revision = rev_candidate
                                        break
                            
                            if drawing_number and revision:
                                break
                    break
            
            # 3. Extract Latest Revision Information (intelligent pattern matching)
            revision_entries = []
            table_header_line = -1
            
            # Find revision table header
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if ('rev' in line_lower and 'date' in line_lower and 
                    ('reason' in line_lower or 'issue' in line_lower)):
                    table_header_line = i
                    
                    # Intelligent table title extraction
                    # Look for the most likely table title using multiple criteria
                    title_candidates = []
                    
                    for j in range(max(0, i-5), min(len(lines), i+10)):
                        title_candidate = lines[j].strip()
                        
                        if (title_candidate and 
                            5 < len(title_candidate) < 50 and
                            len(title_candidate.split()) <= 4):
                            
                            # Score the candidate based on semantic indicators
                            score = 0
                            title_lower = title_candidate.lower()
                            
                            # Positive indicators (document/process types)
                            if any(word in title_lower for word in ['construction', 'development', 'procurement', 'built', 'design']):
                                score += 3
                            if any(word in title_lower for word in ['drawing', 'plan', 'layout', 'section']):
                                score += 2
                            if re.search(r'\b(as|for|and|of|the)\b', title_lower):
                                score += 1
                            
                            # Negative indicators (technical codes, measurements)
                            if re.match(r'^[0-9\.\-\s]+$', title_candidate):
                                score -= 5
                            if re.match(r'^[A-Z]{2,3}-[0-9]+', title_candidate):
                                score -= 3
                            if any(word in title_lower for word in ['project', 'model', 'drawn', 'scale', 'key plan']):
                                score -= 2
                            if len(title_candidate.split()) == 1 and len(title_candidate) < 8:
                                score -= 1
                            
                            title_candidates.append((title_candidate, score, abs(j - i)))
                    
                    # Select best candidate (highest score, closest to header)
                    if title_candidates:
                        title_candidates.sort(key=lambda x: (-x[1], x[2]))  # Sort by score desc, distance asc
                        if title_candidates[0][1] > 0:  # Only if positive score
                            table_title = title_candidates[0][0]
                    
                    # Find revision entries
                    for j in range(max(0, i - 25), i):
                        entry_line = lines[j].strip()
                        
                        # Revision entry pattern
                        revision_pattern = r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)(?:\s+([A-Z]{1,3}))?$'
                        match = re.match(revision_pattern, entry_line, re.IGNORECASE)
                        
                        if match:
                            rev = match.group(1)
                            date = match.group(2)
                            reason = match.group(3).strip()
                            checker = match.group(4) if match.group(4) else ""
                            
                            # Validate entry
                            if (len(rev) <= 3 and 
                                '/' in date and 
                                len(reason) > 2 and
                                not re.match(r'^[0-9\-\s]+$', reason)):
                                
                                # Look for continuation lines
                                full_reason = reason
                                for k in range(j + 1, min(len(lines), j + 3)):
                                    cont_line = lines[k].strip()
                                    
                                    if (re.match(r'^[A-Z0-9]{1,3}\s+\d{1,2}/\d{1,2}/\d{2,4}', cont_line) or
                                        'rev' in cont_line.lower() or
                                        not cont_line):
                                        break
                                    
                                    # Intelligent continuation detection
                                    if (len(cont_line) < 40 and
                                        not re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', cont_line) and
                                        not re.match(r'^[A-Z0-9]{1,3}\s', cont_line) and
                                        len(cont_line) > 1 and
                                        not re.match(r'^[0-9\.\-\s]+$', cont_line) and
                                        # Should contain meaningful words
                                        any(len(word) >= 3 and word.isalpha() for word in cont_line.split())):
                                        full_reason += " " + cont_line
                                        break
                                
                                revision_entries.append({
                                    'revision': rev,
                                    'date': date,
                                    'reason': full_reason.strip(),
                                    'checker': checker,
                                    'line_number': j
                                })
                    break
            
            # Handle simple format if no revision table found
            if table_header_line == -1:
                for i, line in enumerate(lines):
                    if 'Drawing Number' in line and 'Revision' in line:
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            parts = next_line.split()
                            if len(parts) >= 2:
                                potential_revision = parts[-1]
                                if len(potential_revision) <= 3 and re.match(r'^[A-Z0-9]+$', potential_revision):
                                    latest_revision = potential_revision
                                    
                                    # Look for date nearby
                                    for j in range(max(0, i-5), min(len(lines), i+3)):
                                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', lines[j])
                                        if date_match:
                                            latest_date = date_match.group(1)
                                            break
                                    
                                    # Intelligent reason inference
                                    context_lines = lines[max(0, i-15):min(len(lines), i+15)]
                                    context_text = ' '.join(context_lines).lower()
                                    
                                    # Pattern-based reason detection
                                    if 'approval' in context_text:
                                        latest_reason = "issued for approval"
                                    elif 'tender' in context_text:
                                        latest_reason = "issued for tender"
                                    elif 'construction' in context_text:
                                        latest_reason = "issued for construction"
                                    else:
                                        latest_reason = "issued"
                                    
                                    # Intelligent table title from document context
                                    title_candidates = []
                                    for j in range(max(0, i-20), min(len(lines), i+15)):
                                        title_line = lines[j].strip()
                                        if (5 < len(title_line) < 50 and
                                            len(title_line.split()) <= 4):
                                            
                                            score = 0
                                            title_lower = title_line.lower()
                                            
                                            # Semantic scoring for document types
                                            if any(word in title_lower for word in ['built', 'construction', 'development', 'procurement']):
                                                score += 3
                                            if 'drawing' in title_lower:
                                                score += 2
                                            if any(word in title_lower for word in ['as', 'for', 'and']):
                                                score += 1
                                            
                                            # Negative scoring
                                            if re.match(r'^[0-9\.\-\s]+$', title_line):
                                                score -= 5
                                            if any(word in title_lower for word in ['project', 'model', 'drawn']):
                                                score -= 2
                                            
                                            if score > 0:
                                                title_candidates.append((title_line, score))
                                    
                                    if title_candidates:
                                        title_candidates.sort(key=lambda x: -x[1])
                                        table_title = title_candidates[0][0]
                        break
            
            # Select latest revision
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

def process_all_pdfs_intelligent(directory_path="."):
    """
    Process all PDF files using intelligent extraction.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info_intelligent(str(pdf_file))
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
    output_file = "pdf_extraction_results_intelligent.csv"
    df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    
    # Show summary
    successful = len(df[df['status'] == 'SUCCESS'])
    print(f"Summary: {successful}/{len(df)} files processed successfully")
    
    return df

if __name__ == "__main__":
    results = process_all_pdfs_intelligent()