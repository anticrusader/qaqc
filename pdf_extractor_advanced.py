import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info_advanced(pdf_path):
    """
    Extract Drawing Title, Drawing Number, and Revision from a PDF file using pdfplumber.
    This version provides better text extraction for digital PDFs.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from first page (where info table usually is)
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
            # Method 1: Both on same line (Format: "Drawing Number Revision" followed by "NUMBER REVISION")
            number_revision_pattern = r'Drawing Number\s+Revision\s*\n?\s*([A-Z0-9\-]+)\s+([A-Z0-9]+)'
            number_revision_match = re.search(number_revision_pattern, text, re.IGNORECASE)
            
            if number_revision_match:
                drawing_number = number_revision_match.group(1).strip()
                revision = number_revision_match.group(2).strip()
            else:
                # Method 2: Look for drawing number patterns
                number_patterns = [
                    # Specific pattern for L01-H01D02-WSP-75-XX-MUP-IC-80301 format
                    r'(L\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                    # Specific pattern for L02-R02D01-FOS-00-XX-DWG-AR-00001 format  
                    r'(L\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                    # General pattern for drawing numbers
                    r'([A-Z]\d{2}-[A-Z0-9\-]+)',
                    # Model file reference as fallback
                    r'Model File Reference\s*\n?\s*([A-Z0-9\-]+)',
                ]
                
                for pattern in number_patterns:
                    number_match = re.search(pattern, text, re.IGNORECASE)
                    if number_match:
                        drawing_number = number_match.group(1).strip()
                        break
                
                # Method 3: Look for revision patterns
                # First try to find revision after "Drawing Number Revision" header
                revision_after_header = r'Drawing Number\s+Revision\s*\n?[^\n]*?([A-Z0-9]+)\s*$'
                revision_match = re.search(revision_after_header, text, re.IGNORECASE | re.MULTILINE)
                
                if revision_match:
                    revision = revision_match.group(1).strip()
                else:
                    # Look for standalone revision patterns
                    revision_patterns = [
                        r'Revision\s*\n?\s*([A-Z0-9]+)(?:\s|$)',
                        r'Rev\.?\s*:?\s*([A-Z0-9]+)',
                        # Look for revision at end of lines containing drawing numbers
                        r'[A-Z0-9\-]+\s+([T][0-9]+|[0-9]+|[A-Z][0-9]+)\s*$'
                    ]
                    
                    for pattern in revision_patterns:
                        revision_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if revision_match:
                            revision = revision_match.group(1).strip()
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

def process_all_pdfs_advanced(directory_path="."):
    """
    Process all PDF files in the specified directory using advanced extraction.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info_advanced(str(pdf_file))
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
    output_file = "pdf_extraction_results_advanced.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Show summary
    successful = len(df[df['status'] == 'SUCCESS'])
    print(f"\nSummary: {successful}/{len(df)} files processed successfully")
    
    return df

if __name__ == "__main__":
    # Process all PDFs in current directory
    results = process_all_pdfs_advanced()