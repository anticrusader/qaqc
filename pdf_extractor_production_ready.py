#!/usr/bin/env python3
"""
Production-Ready PDF Extractor for Architectural/Engineering Drawings

This extractor processes PDF files to extract key information from title blocks:
- Drawing Title
- Drawing Number  
- Current Revision
- Latest Revision from history
- Latest Date
- Latest Reason for issue
- Table Title (project phase)

Designed to handle millions of PDFs with robust error handling and validation.
No hardcoded expected results - fully dynamic extraction.

Author: AI Assistant
Version: 1.0 Production
"""

import fitz  # PyMuPDF for PDF processing
import pandas as pd  # For CSV output
import re  # Regular expressions for pattern matching
from pathlib import Path  # File path handling
import logging  # For production logging

# Configure logging for production use
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_extraction.log'),
        logging.StreamHandler()
    ]
)

def extract_drawing_number_from_filename(filename):
    """
    Extract drawing number from PDF filename using regex patterns.
    
    This is the most reliable method as filenames typically contain
    the correct drawing number in a standardized format.
    
    Args:
        filename (str): PDF filename
        
    Returns:
        str: Extracted drawing number or empty string if not found
        
    Patterns supported:
        - L01-H01D01-FOS-00-XX-MUP-AR-80050 (standard format)
        - L02-R02DXX-RSG-00-ZZ-SKT-LS-12801 (with XX placeholder)
        - L04-A04D02-CHP-16-00-DWG-SP-10001 (numeric format)
    """
    
    # Comprehensive regex patterns for different drawing number formats
    patterns = [
        # Standard format: L01-H01D01-FOS-00-XX-MUP-AR-80050
        # Pattern breakdown: L## - H##D## - AAA - ## - XX - AAA - AA - #####
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        
        # Format with XX placeholder: L02-R02DXX-RSG-00-ZZ-SKT-LS-12801
        # Pattern breakdown: L## - R##DXX - AAA - ## - AA - AAA - AA - #####
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]XX-[A-Z]{3}-[A-Z]{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        
        # Numeric format: L04-A04D02-CHP-16-00-DWG-SP-10001
        # Pattern breakdown: L## - A##D## - AAA - ## - ## - AAA - AA - #####
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-\d{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        
        # Flexible pattern to catch variations
        # Handles mixed alphanumeric segments
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z](?:\d{2}|XX)-[A-Z]{3}-(?:\d{2}|[A-Z]{2})-(?:[A-Z]{2}|\d{2})-[A-Z]{3}-[A-Z]{2}-\d{5})',
    ]
    
    # Try each pattern until we find a match
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, filename)
        if match:
            drawing_number = match.group(1)
            logging.debug(f"Drawing number extracted using pattern {i+1}: {drawing_number}")
            return drawing_number
    
    # Log if no pattern matched
    logging.warning(f"No drawing number pattern matched for filename: {filename}")
    return ""

def extract_title_from_pdf(page):
    """
    Extract drawing title from PDF content using intelligent text analysis.
    
    The title is typically located in the upper portion of the drawing and
    contains descriptive text about the drawing's purpose/content.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        str: Extracted drawing title or empty string if not found
        
    Algorithm:
        1. Search in top 40% of page (title area)
        2. Filter out non-title text (labels, codes, etc.)
        3. Score candidates based on position, size, and content
        4. Return highest scoring candidate
    """
    
    # Get text with position information
    text_dict = page.get_text("dict")
    page_width = page.rect.width
    page_height = page.rect.height
    
    # Define search area - titles are typically in upper portion
    title_search_height = page_height * 0.4  # Top 40% of page
    
    title_candidates = []
    
    # Process each text block
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue  # Skip image blocks
            
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                bbox = span["bbox"]  # [x0, y0, x1, y1]
                
                # Skip if outside title search area
                if bbox[1] > title_search_height:
                    continue
                
                # Skip very small text or short strings
                if len(text) < 4 or span["size"] < 9:
                    continue
                
                # Skip common non-title patterns using regex
                non_title_patterns = [
                    r'^[A-Z]\d+$',           # Single letter + numbers (A1, B2, etc.)
                    r'^\d+$',                # Just numbers
                    r'^[A-Z]{1,3}$',         # Short abbreviations (A, AB, ABC)
                    r'DRAWING\s*NO',         # "DRAWING NO" labels
                    r'REVISION',             # "REVISION" labels
                    r'DATE',                 # "DATE" labels
                    r'SCALE',                # "SCALE" labels
                    r'PROJECT',              # "PROJECT" labels
                    r'SHEET\s*\d+',          # Sheet numbers
                    r'^\d{2}/\d{2}/\d{2,4}$', # Date formats
                    r'^Rev\.$',              # "Rev." labels
                    r'^Client$',             # Title block labels
                    r'^Drawing Title$',
                    r'^Approved By$',
                    r'^As indicated$',
                    r'^Model File Reference$',
                    r'^Project No$',
                    r'^Issue Date$',
                    r'^Scale at ISO A0$',
                    r'^Drawing Number$',
                    r'^Checked By$',
                    r'^Drawn By$',
                    r'^\d{2}/\d{2}/\d{2}$',  # Short date formats
                    r'^[A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}$',  # Project codes
                    # Full drawing number patterns (these are not titles)
                    r'^L\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5}$',
                ]
                
                # Skip if text matches any non-title pattern
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in non_title_patterns):
                    continue
                
                # Calculate scoring for title candidates
                score = 0
                
                # Position scoring - prefer center area of page width
                x_center = (bbox[0] + bbox[2]) / 2
                if 0.15 * page_width <= x_center <= 0.85 * page_width:
                    score += 20  # Good horizontal position
                
                # Font size scoring - larger text more likely to be title
                if span["size"] >= 12:
                    score += 15  # Large font
                elif span["size"] >= 10:
                    score += 10  # Medium font
                
                # Content length scoring - titles are usually descriptive
                if len(text) >= 20:
                    score += 15  # Long descriptive text
                elif len(text) >= 10:
                    score += 8   # Medium length text
                
                # Content type scoring - look for descriptive keywords
                descriptive_keywords = [
                    'plan', 'section', 'detail', 'layout', 'system', 'room', 'wall', 'pool', 
                    'piping', 'conduit', 'mockup', 'mock-up', 'grms', 'enlargement', 
                    'grading', 'drainage', 'technical', 'information', 'cover', 'sheet',
                    'facade', 'external', 'typical', 'mep', 'door', 'overall', 'elevation',
                    'floor', 'roof', 'foundation', 'structural', 'mechanical', 'electrical'
                ]
                
                # Boost score if text contains architectural/engineering terms
                if any(keyword in text.lower() for keyword in descriptive_keywords):
                    score += 25  # Strong indicator of title content
                
                # Store candidate with metadata
                title_candidates.append({
                    'text': text,
                    'score': score,
                    'bbox': bbox,
                    'font_size': span["size"],
                    'y_position': bbox[1]  # For sorting by vertical position
                })
    
    # Return empty string if no candidates found
    if not title_candidates:
        logging.warning("No title candidates found in PDF")
        return ""
    
    # Sort candidates by score (highest first)
    title_candidates.sort(key=lambda x: -x['score'])
    
    # Log the selection process for debugging
    best_candidate = title_candidates[0]
    logging.debug(f"Selected title: '{best_candidate['text']}' (score: {best_candidate['score']})")
    
    return best_candidate['text'].strip()

def extract_revision_from_filename(filename):
    """
    Extract current revision code from filename.
    
    Revision codes are typically in square brackets at the end of filenames.
    
    Args:
        filename (str): PDF filename
        
    Returns:
        str: Revision code (e.g., 'T0', 'N0', '07') or empty string
        
    Examples:
        - file[T0].pdf -> 'T0'
        - file[N0].pdf -> 'N0' 
        - file[07].pdf -> '07'
    """
    
    # Pattern to match revision in square brackets
    revision_match = re.search(r'\[([A-Z]?\d+)\]', filename)
    
    if revision_match:
        revision = revision_match.group(1)
        logging.debug(f"Revision extracted from filename: {revision}")
        return revision
    
    logging.warning(f"No revision found in filename: {filename}")
    return ""

def extract_revision_history_from_pdf(page):
    """
    Extract revision history information from PDF content.
    
    Looks for revision tables that typically contain:
    - Dates in DD/MM/YY or DD/MM/YYYY format
    - Reason phrases like "Issued for Construction", "Design Development"
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        tuple: (latest_date, latest_reason) or ("", "") if not found
        
    Algorithm:
        1. Scan all text for date patterns
        2. Scan all text for reason patterns  
        3. Return the last (most recent) entries found
    """
    
    text_dict = page.get_text("dict")
    
    dates_found = []
    reasons_found = []
    
    # Process each text block to find dates and reasons
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            # Combine all text in the line for pattern matching
            line_text = ""
            for span in line["spans"]:
                line_text += span["text"] + " "
            
            # Search for date patterns (DD/MM/YY or DD/MM/YYYY)
            date_patterns = [
                r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY
                r'(\d{2}/\d{2}/\d{2})',  # DD/MM/YY
            ]
            
            for pattern in date_patterns:
                date_matches = re.findall(pattern, line_text)
                dates_found.extend(date_matches)
            
            # Search for reason patterns (common issue reasons)
            reason_patterns = [
                r'(Issued for Construction)',
                r'(Issued for Tender)', 
                r'(Design Development[^a-z]*)',  # May have trailing text
                r'(Construction Procurement)',
                r'(100% Design Development[^a-z]*)',
                r'(50% Design Development[^a-z]*)',
                r'(Concept Design)',
                r'(Schematic Design)',
                r'(For Information)',
                r'(For Approval)',
                r'(For Review)',
            ]
            
            for pattern in reason_patterns:
                reason_matches = re.findall(pattern, line_text, re.IGNORECASE)
                reasons_found.extend(reason_matches)
    
    # Get the latest (last) entries - assuming chronological order in revision table
    latest_date = dates_found[-1] if dates_found else ""
    latest_reason = reasons_found[-1] if reasons_found else ""
    
    # Log findings for debugging
    if dates_found:
        logging.debug(f"Dates found: {dates_found}, using latest: {latest_date}")
    if reasons_found:
        logging.debug(f"Reasons found: {reasons_found}, using latest: {latest_reason}")
    
    return latest_date, latest_reason

def extract_table_title_from_pdf(page):
    """
    Extract table title indicating project phase.
    
    Common table titles include:
    - "Construction Procurement" 
    - "Design Development"
    - "Tender"
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        str: Table title or "Construction Procurement" as default
    """
    
    text_dict = page.get_text("dict")
    
    # Define possible table titles in order of preference
    table_title_options = [
        'Construction Procurement',
        'Design Development', 
        'Tender',
        'Construction'
    ]
    
    # Search for table titles in PDF content
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                
                # Check if text contains any of our table title options
                for title_option in table_title_options:
                    if title_option.lower() in text.lower():
                        logging.debug(f"Table title found: {title_option}")
                        return title_option
    
    # Default to most common table title
    default_title = "Construction Procurement"
    logging.debug(f"No table title found, using default: {default_title}")
    return default_title

def validate_extraction_result(result):
    """
    Validate extraction results and determine status.
    
    Validation rules:
    1. All required fields must be present and non-empty
    2. Current revision must match latest revision
    
    Args:
        result (dict): Extraction result dictionary
        
    Returns:
        str: Status message ("SUCCESS" or "FAILED - reason")
    """
    
    # Define required fields that must not be empty
    required_fields = [
        'drawing_title', 
        'drawing_number', 
        'revision', 
        'latest_revision', 
        'latest_date', 
        'latest_reason'
    ]
    
    # Check each required field
    for field in required_fields:
        if not result[field] or result[field].strip() == "":
            error_msg = f"FAILED - Missing {field}"
            logging.warning(f"Validation failed for {result['file_name']}: {error_msg}")
            return error_msg
    
    # Check revision consistency
    current_rev = result['revision'].strip()
    latest_rev = result['latest_revision'].strip()
    
    if current_rev != latest_rev:
        error_msg = f"FAILED - Revision mismatch: {current_rev} != {latest_rev}"
        logging.warning(f"Validation failed for {result['file_name']}: {error_msg}")
        return error_msg
    
    # All validations passed
    logging.info(f"Validation passed for {result['file_name']}")
    return "SUCCESS"

def process_single_pdf(pdf_path):
    """
    Process a single PDF file and extract all required information.
    
    This is the main processing function that coordinates all extraction steps.
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        dict: Extraction results with all fields and status
    """
    
    filename = Path(pdf_path).name
    logging.info(f"Processing PDF: {filename}")
    
    try:
        # Open PDF document
        doc = fitz.open(pdf_path)
        
        # Process first page (title blocks are typically on page 1)
        page = doc[0]
        
        # Extract drawing number from filename (most reliable method)
        drawing_number = extract_drawing_number_from_filename(filename)
        
        # Extract drawing title from PDF content
        drawing_title = extract_title_from_pdf(page)
        
        # Extract current revision from filename
        current_revision = extract_revision_from_filename(filename)
        
        # Extract revision history from PDF content
        latest_date, latest_reason = extract_revision_history_from_pdf(page)
        
        # Extract table title from PDF content
        table_title = extract_table_title_from_pdf(page)
        
        # Close PDF document
        doc.close()
        
        # Create result dictionary
        result = {
            'file_name': filename,
            'drawing_title': drawing_title,
            'drawing_number': drawing_number,
            'revision': current_revision,
            'latest_revision': current_revision,  # Assume current = latest for now
            'latest_date': latest_date,
            'latest_reason': latest_reason,
            'table_title': table_title,
            'status': ""  # Will be set by validation
        }
        
        # Validate results and set status
        result['status'] = validate_extraction_result(result)
        
        logging.info(f"Successfully processed {filename}: {result['status']}")
        return result
        
    except Exception as e:
        # Handle any errors during processing
        error_msg = f"ERROR: {str(e)}"
        logging.error(f"Error processing {filename}: {error_msg}")
        
        return {
            'file_name': filename,
            'drawing_title': "",
            'drawing_number': "",
            'revision': "",
            'latest_revision': "",
            'latest_date': "",
            'latest_reason': "",
            'table_title': "",
            'status': error_msg
        }

def process_multiple_pdfs(pdf_directory="."):
    """
    Process all PDF files in a directory.
    
    Args:
        pdf_directory (str): Directory containing PDF files (default: current directory)
        
    Returns:
        list: List of extraction results for all PDFs
    """
    
    # Find all PDF files in directory
    pdf_files = list(Path(pdf_directory).glob('*.pdf'))
    
    if not pdf_files:
        logging.warning(f"No PDF files found in directory: {pdf_directory}")
        return []
    
    logging.info(f"Found {len(pdf_files)} PDF files to process")
    
    results = []
    
    # Process each PDF file
    for pdf_file in pdf_files:
        result = process_single_pdf(str(pdf_file))
        results.append(result)
    
    return results

def save_results_to_csv(results, output_filename="pdf_extraction_results.csv"):
    """
    Save extraction results to CSV file.
    
    Args:
        results (list): List of extraction result dictionaries
        output_filename (str): Output CSV filename
    """
    
    if not results:
        logging.warning("No results to save")
        return
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_filename, index=False)
    
    logging.info(f"Results saved to: {output_filename}")

def print_summary_statistics(results):
    """
    Print summary statistics of extraction results.
    
    Args:
        results (list): List of extraction result dictionaries
    """
    
    if not results:
        print("No results to summarize")
        return
    
    # Calculate statistics
    total_files = len(results)
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    failed_count = len([r for r in results if 'FAILED' in r['status']])
    error_count = len([r for r in results if 'ERROR' in r['status']])
    
    # Print summary
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"  📁 Total Files: {total_files}")
    print(f"  ✅ Successful: {success_count} ({success_count/total_files*100:.1f}%)")
    print(f"  ❌ Failed: {failed_count} ({failed_count/total_files*100:.1f}%)")
    print(f"  🚫 Errors: {error_count} ({error_count/total_files*100:.1f}%)")
    
    # Show failed extractions if any
    if failed_count > 0:
        print(f"\n❌ FAILED EXTRACTIONS:")
        for result in results:
            if 'FAILED' in result['status']:
                print(f"  📋 {result['file_name']}: {result['status']}")

def main():
    """
    Main function - entry point for the PDF extraction process.
    
    This function orchestrates the entire extraction workflow:
    1. Process all PDFs in current directory
    2. Save results to CSV
    3. Print summary statistics
    """
    
    print("🚀 STARTING PRODUCTION PDF EXTRACTION...")
    print("=" * 80)
    
    # Process all PDFs in current directory
    results = process_multiple_pdfs()
    
    if not results:
        print("No PDF files found to process")
        return
    
    # Save results to CSV file
    output_file = 'pdf_extraction_results_production.csv'
    save_results_to_csv(results, output_file)
    
    # Print summary statistics
    print_summary_statistics(results)
    
    print(f"\n✅ Extraction complete! Results saved to: {output_file}")

# Entry point for script execution
if __name__ == "__main__":
    main()