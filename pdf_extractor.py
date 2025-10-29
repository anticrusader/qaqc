import PyPDF2
import re
import pandas as pd
import os
from pathlib import Path

def extract_pdf_info(pdf_path):
    """
    Extract Drawing Title, Drawing Number, and Revision from a PDF file.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages (usually info is on first page)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Initialize results
            drawing_title = ""
            drawing_number = ""
            revision = ""
            
            # Extract Drawing Title
            # Look for "Drawing Title" followed by the actual title
            title_match = re.search(r'Drawing Title\s*\n?\s*([^\n]+)', text, re.IGNORECASE)
            if title_match:
                drawing_title = title_match.group(1).strip()
            
            # Extract Drawing Number
            # Look for patterns like "L02-R02D01-FOS-00-XX-DWG-AR-00001"
            number_patterns = [
                r'Drawing Number\s*\n?\s*([A-Z0-9\-]+)',
                r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
                r'Model File Reference\s*\n?\s*([A-Z0-9\-]+)'
            ]
            
            for pattern in number_patterns:
                number_match = re.search(pattern, text, re.IGNORECASE)
                if number_match:
                    drawing_number = number_match.group(1).strip()
                    break
            
            # Extract Revision
            # Look for "Revision" followed by number/letter
            revision_patterns = [
                r'Revision\s*\n?\s*([A-Z0-9]+)',
                r'Rev\s*:?\s*([A-Z0-9]+)',
                r'Revision\s*([A-Z0-9]+)'
            ]
            
            for pattern in revision_patterns:
                revision_match = re.search(pattern, text, re.IGNORECASE)
                if revision_match:
                    revision = revision_match.group(1).strip()
                    break
            
            return {
                'file_name': os.path.basename(pdf_path),
                'drawing_title': drawing_title,
                'drawing_number': drawing_number,
                'revision': revision
            }
            
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return {
            'file_name': os.path.basename(pdf_path),
            'drawing_title': 'ERROR',
            'drawing_number': 'ERROR',
            'revision': 'ERROR'
        }

def process_all_pdfs(directory_path="."):
    """
    Process all PDF files in the specified directory.
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extract_pdf_info(str(pdf_file))
        results.append(result)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    
    # Display results
    print("\n" + "="*80)
    print("EXTRACTION RESULTS:")
    print("="*80)
    print(df.to_string(index=False))
    
    # Save to CSV
    output_file = "pdf_extraction_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    # Process all PDFs in current directory
    results = process_all_pdfs()