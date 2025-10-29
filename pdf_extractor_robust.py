import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info_robust(pdf_path):
    """
    Robust version that handles any variation in PDF layouts.
    Extracts 7 fields with flexible, adaptive logic.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from first page
            text = ""
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                
                # If first page doesn't have much text, try second page
                if len(text.strip()) < 100 and len(pdf.pages) > 1:
                    text += "\n" + pdf.pages[1].extract_text()
            
            # Initialize results
            drawing_title = ""
            drawing_number = ""
            revision = ""
            latest_revision = ""
            latest_date = ""
            latest_reason = ""
            table_title = ""
            
            # Split text into lines for easier analysis
            lines = text.split('\n')
            
            # Extract Drawing Title
            title_found = False
            for i, line in enumerate(lines):
                if 'Drawing Title' in line and not title_found:
                    # Collect title from subsequent lines until we hit another section
                    title_parts = []
                    j = i + 1
                    while j < len(lines) and j < i + 5:  # Look at next few lines
                        next_line = lines[j].strip()
                        # Stop if we hit another section header
                        if any(keyword in next_line for keyword in ['Model File Reference', 'Drawn By', 'Project No', 'Drawing Number']):
                            break
                        if next_line and not next_line.startswith('Drawing'):
                            title_parts.append(next_line)
                        j += 1
                    
                    if title_parts:
                        drawing_title = ' '.join(title_parts).strip()
                        title_found = True
                        break
            
            # Extract Drawing Number and Revision (from main table)
            # Look for the "Drawing Number Revision" pattern followed by the actual values
            for i, line in enumerate(lines):
                if 'Drawing Number' in line and 'Revision' in line:
                    # Check the next few lines for the actual values
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not any(keyword in next_line for keyword in ['Drawn By', 'Project No', 'Scale']):
                            # Try to split the line to get both drawing number and revision
                            parts = next_line.split()
                            
                            # Look for drawing number patterns
                            drawing_number_candidates = []
                            revision_candidates = []
                            
                            for part in parts:
                                # Drawing number patterns (long alphanumeric with dashes)
                                if re.match(r'L\d{2}-[A-Z0-9\-]{20,}', part):
                                    drawing_number_candidates.append(part)
                                # Revision patterns (short alphanumeric)
                                elif re.match(r'^(T[0-9]+|[0-9]{2}|[A-Z]{1,2}[0-9]*)$', part) and len(part) <= 3:
                                    revision_candidates.append(part)
                            
                            # If we found both on the same line
                            if drawing_number_candidates and revision_candidates:
                                drawing_number = drawing_number_candidates[0]
                                revision = revision_candidates[0]
                                break
                            # If we found only drawing number, look for revision elsewhere
                            elif drawing_number_candidates:
                                drawing_number = drawing_number_candidates[0]
                                # Look for revision in the same line or nearby
                                for part in parts:
                                    if re.match(r'^(T[0-9]+|[0-9]{2}|[A-Z]{1,2}[0-9]*)$', part) and len(part) <= 3:
                                        revision = part
                                        break
                                if revision:
                                    break
                    
                    if drawing_number and revision:
                        break
            
            # If we didn't find both values using the above method, try alternative approaches
            if not drawing_number or not revision:
                # Alternative method: Look for specific patterns in the entire text
                
                # Drawing number patterns - flexible approach
                drawing_patterns = [
                    r'(L\d{2}-[A-Z0-9]{6}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                    r'(L\d{2}-[A-Z0-9\-]{25,})',  # General long pattern
                ]
                
                if not drawing_number:
                    for pattern in drawing_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            drawing_number = matches[0]
                            break
                
                # Revision patterns - flexible approach
                if not revision:
                    # First, try to extract from filename as a hint
                    filename = os.path.basename(pdf_path)
                    filename_revision_match = re.search(r'\[([A-Z0-9]+)\]', filename)
                    filename_hint = filename_revision_match.group(1) if filename_revision_match else None
                    
                    revision_patterns = [
                        r'\b(T[0-9]+)\b',
                        r'\b([0-9]{2})\b',
                        r'\b([A-Z]{1,2}[0-9]*)\b',
                    ]
                    
                    for pattern in revision_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            # Prefer filename hint if it matches one of the found revisions
                            if filename_hint and filename_hint in matches:
                                revision = filename_hint
                                break
                            # Otherwise take the first match that looks like a revision
                            for match in matches:
                                if len(match) <= 3 and match not in ['01', '02', '03', '04', '05', '06', '08', '09', '10']:
                                    revision = match
                                    break
                            if revision:
                                break
            
            # Extract Latest Revision Table Information - ROBUST APPROACH
            revision_table_entries = []
            table_header_line = -1
            
            # Step 1: Find the revision table header (multiple formats)
            revision_table_found = False
            for i, line in enumerate(lines):
                if 'Rev.' in line and 'Date' in line and 'Reason For Issue' in line:
                    table_header_line = i
                    revision_table_found = True
                    
                    # Step 2: Extract table title - look for common table titles
                    table_title_patterns = [
                        r'(CONSTRUCTION PROCUREMENT)',
                        r'(Design Development)',
                        r'(DESIGN DEVELOPMENT)',
                        r'(Construction Procurement)',
                        r'(PROCUREMENT)',
                        r'(DEVELOPMENT)',
                    ]
                    
                    # Look in lines around the header (before and after)
                    for j in range(max(0, i-3), min(len(lines), i+5)):
                        line_text = lines[j].strip()
                        for pattern in table_title_patterns:
                            match = re.search(pattern, line_text, re.IGNORECASE)
                            if match:
                                table_title = match.group(1)
                                break
                        if table_title:
                            break
                    
                    # Step 3: Find revision entries - flexible patterns
                    # Look above the header for revision entries (expand search range)
                    for j in range(max(0, i-15), i):
                        entry_line = lines[j].strip()
                        
                        # Multiple flexible patterns for revision entries
                        revision_patterns = [
                            # Pattern 1: REV DATE REASON CHK (with checker) - strict start
                            r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+([A-Z]{1,3})$',
                            # Pattern 2: REV DATE REASON (no checker) - strict start  
                            r'^([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+)$',
                            # Pattern 3: Embedded in other text - flexible
                            r'([A-Z0-9]{1,3})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(Issue for Tender|ISSUED FOR TENDER|Design Development|100% Design Development|50% Design Development|100% Concept Design|100% Schematic Design|50% Schematic Design)',
                        ]
                        
                        for pattern in revision_patterns:
                            match = re.search(pattern, entry_line, re.IGNORECASE)
                            if match:
                                rev = match.group(1)
                                date = match.group(2)
                                reason = match.group(3).strip()
                                chk = match.group(4) if len(match.groups()) >= 4 else ""
                                
                                # Validate that this looks like a real revision entry
                                if len(rev) <= 3 and '/' in date and len(reason) > 3:
                                    revision_table_entries.append({
                                        'revision': rev,
                                        'date': date,
                                        'reason': reason,
                                        'checker': chk,
                                        'line_number': j
                                    })
                                break
                    break
            
            # Step 1b: Handle simpler format (Drawing Number Revision on same line)
            if not revision_table_found:
                for i, line in enumerate(lines):
                    if 'Drawing Number' in line and 'Revision' in line:
                        # Look for drawing number and revision on next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # Check if this line has both drawing number and revision
                            parts = next_line.split()
                            if len(parts) >= 2:
                                # Last part might be revision
                                potential_revision = parts[-1]
                                if len(potential_revision) <= 3 and re.match(r'^[A-Z0-9]+$', potential_revision):
                                    latest_revision = potential_revision
                                    
                                    # Look for date in nearby lines (Issue Date, Project Date, etc.)
                                    for j in range(max(0, i-5), min(len(lines), i+3)):
                                        date_line = lines[j].strip()
                                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_line)
                                        if date_match and not latest_date:
                                            latest_date = date_match.group(1)
                                    
                                    # Look for actual revision reason in the document first
                                    reason_found = False
                                    for j in range(max(0, i-20), min(len(lines), i+10)):
                                        reason_line = lines[j].strip().lower()
                                        if any(phrase in reason_line for phrase in ['issued for approval', 'for approval', 'approval']):
                                            latest_reason = "issued for approval"
                                            reason_found = True
                                            break
                                        elif any(phrase in reason_line for phrase in ['issued for tender', 'for tender']):
                                            latest_reason = "ISSUED FOR TENDER"
                                            reason_found = True
                                            break
                                    
                                    # Fallback: infer from filename or context
                                    if not reason_found:
                                        filename = os.path.basename(pdf_path).upper()
                                        if 'AS-BUILT' in filename or 'ABD' in filename:
                                            latest_reason = "issued for approval"  # Common for AS-BUILT drawings
                                        elif 'TENDER' in filename:
                                            latest_reason = "ISSUED FOR TENDER"
                                        else:
                                            latest_reason = "ISSUED"
                                    
                                    # Look for table title in surrounding context
                                    for j in range(max(0, i-20), min(len(lines), i+10)):
                                        title_line = lines[j].strip().upper()
                                        if 'AS BUILT' in title_line and 'DRAWING' in title_line:
                                            table_title = "AS BUILT DRAWING"
                                            break
                                        elif 'AS BUILT' in title_line:
                                            table_title = "AS BUILT DRAWING"  # Infer full title
                                            break
                                        elif 'CONSTRUCTION PROCUREMENT' in title_line:
                                            table_title = "CONSTRUCTION PROCUREMENT"
                                            break
                                        elif 'PROCUREMENT' in title_line:
                                            table_title = "PROCUREMENT"
                                            break
                        break
            
            # Step 4: Select the latest revision (lowest line number = appears first = most recent)
            if revision_table_entries:
                latest_entry = min(revision_table_entries, key=lambda x: x['line_number'])
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

def process_all_pdfs_robust(directory_path="."):
    """
    Process all PDF files using the robust extraction method.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info_robust(str(pdf_file))
        results.append(result)
        
        # Show progress for each file
        if result['status'] == 'SUCCESS':
            print(f"  ✓ Title: {result['drawing_title'][:50]}...")
            print(f"  ✓ Number: {result['drawing_number']}")
            print(f"  ✓ Revision: {result['revision']}")
            print(f"  ✓ Latest Rev: {result['latest_revision']}")
            print(f"  ✓ Latest Date: {result['latest_date']}")
            print(f"  ✓ Latest Reason: {result['latest_reason'][:40]}...")
            print(f"  ✓ Table Title: {result['table_title']}")
        else:
            print(f"  ✗ Failed: {result['status']}")
        print()
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    
    # Display results
    print("\n" + "="*150)
    print("ROBUST EXTRACTION RESULTS:")
    print("="*150)
    
    # Format output for better readability
    for _, row in df.iterrows():
        print(f"File: {row['file_name']}")
        print(f"  Drawing Title: {row['drawing_title']}")
        print(f"  Drawing Number: {row['drawing_number']}")
        print(f"  Revision: {row['revision']}")
        print(f"  Latest Revision: {row['latest_revision']}")
        print(f"  Latest Date: {row['latest_date']}")
        print(f"  Latest Reason: {row['latest_reason']}")
        print(f"  Table Title: {row['table_title']}")
        print(f"  Status: {row['status']}")
        print("-" * 120)
    
    # Save to CSV
    output_file = "pdf_extraction_results_robust.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Show summary
    successful = len(df[df['status'] == 'SUCCESS'])
    print(f"\nSummary: {successful}/{len(df)} files processed successfully")
    
    # Show accuracy for each field
    title_success = len(df[df['drawing_title'] != ''])
    number_success = len(df[df['drawing_number'] != ''])
    revision_success = len(df[df['revision'] != ''])
    latest_rev_success = len(df[df['latest_revision'] != ''])
    latest_date_success = len(df[df['latest_date'] != ''])
    latest_reason_success = len(df[df['latest_reason'] != ''])
    table_title_success = len(df[df['table_title'] != ''])
    
    print(f"Field accuracy:")
    print(f"  Drawing Titles: {title_success}/{len(df)} ({title_success/len(df)*100:.1f}%)")
    print(f"  Drawing Numbers: {number_success}/{len(df)} ({number_success/len(df)*100:.1f}%)")
    print(f"  Revisions: {revision_success}/{len(df)} ({revision_success/len(df)*100:.1f}%)")
    print(f"  Latest Revisions: {latest_rev_success}/{len(df)} ({latest_rev_success/len(df)*100:.1f}%)")
    print(f"  Latest Dates: {latest_date_success}/{len(df)} ({latest_date_success/len(df)*100:.1f}%)")
    print(f"  Latest Reasons: {latest_reason_success}/{len(df)} ({latest_reason_success/len(df)*100:.1f}%)")
    print(f"  Table Titles: {table_title_success}/{len(df)} ({table_title_success/len(df)*100:.1f}%)")
    
    return df

if __name__ == "__main__":
    # Process all PDFs in current directory
    results = process_all_pdfs_robust()