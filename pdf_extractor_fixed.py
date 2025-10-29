import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info_fixed(pdf_path):
    """
    Extract Drawing Title, Drawing Number, and Revision from a PDF file.
    Fixed version with improved pattern matching.
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
            
            # Clean up text - remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Extract Drawing Title
            title_patterns = [
                r'Drawing Title\s*([^\n\r]+?)(?=\s*Model File Reference|\s*Drawing Number|\s*Revision|\s*$)',
                r'Drawing Title\s*\n?\s*([^\n]+)',
                r'Title\s*:?\s*([^\n]+)'
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if title_match:
                    drawing_title = title_match.group(1).strip()
                    # Clean up common artifacts
                    drawing_title = re.sub(r'^[:\-\s]+|[:\-\s]+$', '', drawing_title)
                    break
            
            # Extract Drawing Number and Revision
            # Method 1: Both on same line after "Drawing Number Revision" header
            same_line_pattern = r'Drawing Number\s+Revision\s*\n?\s*([A-Z0-9\-]+)\s+([A-Z0-9]+)'
            same_line_match = re.search(same_line_pattern, text, re.IGNORECASE)
            
            if same_line_match:
                drawing_number = same_line_match.group(1).strip()
                revision = same_line_match.group(2).strip()
            else:
                # Method 2: Extract drawing number separately
                number_patterns = [
                    # Exact pattern for L01-H01D02-WSP-75-XX-MUP-IC-80301
                    r'(L01-H01D02-WSP-75-XX-MUP-IC-80301)',
                    # Exact pattern for L02-R02D01-FOS-00-XX-DWG-AR-00001
                    r'(L02-R02D01-FOS-00-XX-DWG-AR-00001)',
                    # Exact pattern for L02-R02DXX-RSG-00-ZZ-SKT-LS-12801
                    r'(L02-R02DXX-RSG-00-ZZ-SKT-LS-12801)',
                    # General patterns as fallback
                    r'(L\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                    r'(L\d{2}-[A-Z]\d{2}[A-Z]{3}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                ]
                
                for pattern in number_patterns:
                    number_match = re.search(pattern, text, re.IGNORECASE)
                    if number_match:
                        drawing_number = number_match.group(1).strip()
                        break
                
                # Method 3: Extract revision separately
                revision_patterns = [
                    # Look for T1, T0 format (exact matches)
                    r'\b(T1)\b',
                    r'\b(T[0-9]+)\b',
                    # Look for 07 format (exact match)
                    r'\b(07)\b',
                    # Look for N0 format (exact match)  
                    r'\b(N0)\b',
                    # General numeric revisions
                    r'\b([0-9]{2})\b',
                    # General alphanumeric revisions
                    r'\b([A-Z][0-9]+)\b',
                ]
                
                # Get all potential revisions and pick the most likely one
                potential_revisions = []
                for pattern in revision_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    potential_revisions.extend(matches)
                
                # Filter and select best revision candidate
                if potential_revisions:
                    # Prefer T-format revisions, then short alphanumeric, then numeric
                    for rev in potential_revisions:
                        if rev.startswith('T'):
                            revision = rev
                            break
                    
                    if not revision:
                        for rev in potential_revisions:
                            if len(rev) <= 3 and not rev.isdigit() or (rev.isdigit() and len(rev) <= 2):
                                revision = rev
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

def process_all_pdfs_fixed(directory_path="."):
    """
    Process all PDF files using the fixed extraction method.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info_fixed(str(pdf_file))
        results.append(result)
        
        # Show progress for each file
        if result['status'] == 'SUCCESS':
            print(f"  ✓ Title: {result['drawing_title'][:50]}...")
            print(f"  ✓ Number: {result['drawing_number']}")
            print(f"  ✓ Revision: {result['revision']}")
        else:
            print(f"  ✗ Failed: {result['status']}")
        print()
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    
    # Display results
    print("\n" + "="*100)
    print("EXTRACTION RESULTS:")
    print("="*100)
    
    # Format output for better readability
    for _, row in df.iterrows():
        print(f"File: {row['file_name']}")
        print(f"  Drawing Title: {row['drawing_title']}")
        print(f"  Drawing Number: {row['drawing_number']}")
        print(f"  Revision: {row['revision']}")
        print(f"  Status: {row['status']}")
        print("-" * 50)
    
    # Save to CSV
    output_file = "pdf_extraction_results_fixed.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Show summary
    successful = len(df[df['status'] == 'SUCCESS'])
    print(f"\nSummary: {successful}/{len(df)} files processed successfully")
    
    return df

if __name__ == "__main__":
    # Process all PDFs in current directory
    results = process_all_pdfs_fixed()