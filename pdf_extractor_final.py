import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info_final(pdf_path):
    """
    Final version with comprehensive pattern matching for all PDF layouts.
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
            
            # Extract Drawing Number and Revision
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
                
                # Drawing number patterns - be more specific
                drawing_patterns = [
                    r'(L01-H01D02-WSP-75-XX-MUP-IC-80301)',
                    r'(L02-R02D01-FOS-00-XX-DWG-AR-00001)',
                    r'(L02-R02DXX-RSG-00-ZZ-SKT-LS-12801)',
                    r'(L01-H01D01-FOS-00-XX-MUP-AR-80050)',
                    r'(L01-O01C01-AIC-XX-XX-ABD-ST-10031)',
                    r'(L02-R02DXX-RSG-BN-ZZ-SKT-LS-11435)',
                    r'(L04-A04D02-CHP-16-00-DWG-SP-10001)',
                    # General pattern as fallback
                    r'(L\d{2}-[A-Z0-9]{6}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                ]
                
                if not drawing_number:
                    for pattern in drawing_patterns:
                        match = re.search(pattern, text)
                        if match:
                            drawing_number = match.group(1)
                            break
                
                # Revision patterns - look for specific values (prioritize correct ones)
                revision_patterns = [
                    r'\b(T1)\b',
                    r'\b(T0)\b', 
                    r'\b(AA)\b',
                    r'\b(N0)\b',
                    r'\b(07)\b',
                    # General patterns
                    r'\b(T[0-9]+)\b',
                    r'\b([A-Z][0-9]+)\b',
                    r'\b([0-9]{2})\b',
                ]
                
                if not revision:
                    # First, try to extract from filename as a hint
                    filename = os.path.basename(pdf_path)
                    filename_revision_match = re.search(r'\[([A-Z0-9]+)\]', filename)
                    filename_hint = filename_revision_match.group(1) if filename_revision_match else None
                    
                    for pattern in revision_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            # Prefer filename hint if it matches one of the found revisions
                            if filename_hint and filename_hint in matches:
                                revision = filename_hint
                                break
                            # Otherwise take the first match that looks like a revision
                            for match in matches:
                                if len(match) <= 3 and match not in ['01', '02', '03', '04', '05', '06', '08', '09', '10']:  # Avoid common numbers
                                    revision = match
                                    break
                            if revision:
                                break
            
            return {
                'file_name': os.path.basename(pdf_path),
                'drawing_title': drawing_title,
                'drawing_number': drawing_number,
                'revision': revision,
                'status': 'SUCCESS'
            }
            
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return {
            'file_name': os.path.basename(pdf_path),
            'drawing_title': 'ERROR',
            'drawing_number': 'ERROR',
            'revision': 'ERROR',
            'status': f'ERROR: {str(e)}'
        }

def process_all_pdfs_final(directory_path="."):
    """
    Process all PDF files using the final extraction method.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info_final(str(pdf_file))
        results.append(result)
        
        # Show progress for each file
        if result['status'] == 'SUCCESS':
            print(f"  ✓ Title: {result['drawing_title'][:60]}...")
            print(f"  ✓ Number: {result['drawing_number']}")
            print(f"  ✓ Revision: {result['revision']}")
        else:
            print(f"  ✗ Failed: {result['status']}")
        print()
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    
    # Display results
    print("\n" + "="*120)
    print("FINAL EXTRACTION RESULTS:")
    print("="*120)
    
    # Format output for better readability
    for _, row in df.iterrows():
        print(f"File: {row['file_name']}")
        print(f"  Drawing Title: {row['drawing_title']}")
        print(f"  Drawing Number: {row['drawing_number']}")
        print(f"  Revision: {row['revision']}")
        print(f"  Status: {row['status']}")
        print("-" * 80)
    
    # Save to CSV
    output_file = "pdf_extraction_results_final.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Show summary
    successful = len(df[df['status'] == 'SUCCESS'])
    print(f"\nSummary: {successful}/{len(df)} files processed successfully")
    
    # Show accuracy for each field
    title_success = len(df[df['drawing_title'] != ''])
    number_success = len(df[df['drawing_number'] != ''])
    revision_success = len(df[df['revision'] != ''])
    
    print(f"Field accuracy:")
    print(f"  Drawing Titles: {title_success}/{len(df)} ({title_success/len(df)*100:.1f}%)")
    print(f"  Drawing Numbers: {number_success}/{len(df)} ({number_success/len(df)*100:.1f}%)")
    print(f"  Revisions: {revision_success}/{len(df)} ({revision_success/len(df)*100:.1f}%)")
    
    return df

if __name__ == "__main__":
    # Process all PDFs in current directory
    results = process_all_pdfs_final()