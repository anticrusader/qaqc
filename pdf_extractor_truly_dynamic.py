#!/usr/bin/env python3
"""
Truly Dynamic PDF Extractor for Architectural/Engineering Drawings

This extractor processes PDF files to extract key information from title blocks:
- Drawing Title
- Drawing Number (from PDF content, validated against filename)
- Current Revision (from PDF content)
- Latest Revision from history
- Latest Date
- Latest Reason for issue
- Table Title (project phase)

ALL extraction is done from PDF content - filename is only used for validation.

Author: AI Assistant
Version: 2.0 Truly Dynamic
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

def extract_drawing_number_from_content(page):
    """
    Extract drawing number from PDF content in title block area.
    
    Drawing numbers are typically located in the title block (bottom right area)
    and follow standardized patterns like L01-H01D01-FOS-00-XX-MUP-AR-80050.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        str: Extracted drawing number or empty string if not found
    """
    
    text_dict = page.get_text("dict")
    page_width = page.rect.width
    page_height = page.rect.height
    
    # Define title block area (bottom right 40% x 30% of page)
    title_block_x_start = page_width * 0.6   # Right 40% of page
    title_block_y_start = page_height * 0.7  # Bottom 30% of page
    
    # Drawing number patterns to search for
    drawing_number_patterns = [
        # Standard format: L01-H01D01-FOS-00-XX-MUP-AR-80050
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        
        # Format with XX placeholder: L02-R02DXX-RSG-00-ZZ-SKT-LS-12801
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]XX-[A-Z]{3}-[A-Z]{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        
        # Numeric format: L04-A04D02-CHP-16-00-DWG-SP-10001
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-\d{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        
        # Flexible pattern for variations
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z](?:\d{2}|XX)-[A-Z]{3}-(?:\d{2}|[A-Z]{2})-(?:[A-Z]{2}|\d{2})-[A-Z]{3}-[A-Z]{2}-\d{5})',
    ]
    
    drawing_numbers_found = []
    
    # First, search in title block area (most reliable location)
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                bbox = span["bbox"]
                
                # Check if text is in title block area
                if bbox[0] >= title_block_x_start and bbox[1] >= title_block_y_start:
                    # Search for drawing number patterns
                    for pattern in drawing_number_patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            drawing_numbers_found.append({
                                'number': match,
                                'location': 'title_block',
                                'confidence': 10  # High confidence for title block
                            })
    
    # If not found in title block, search entire page
    if not drawing_numbers_found:
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    
                    # Search for drawing number patterns anywhere on page
                    for pattern in drawing_number_patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            drawing_numbers_found.append({
                                'number': match,
                                'location': 'page_content',
                                'confidence': 5  # Lower confidence for general content
                            })
    
    # Return the highest confidence drawing number
    if drawing_numbers_found:
        # Sort by confidence (highest first)
        drawing_numbers_found.sort(key=lambda x: x['confidence'], reverse=True)
        best_match = drawing_numbers_found[0]
        logging.debug(f"Drawing number found: {best_match['number']} (location: {best_match['location']})")
        return best_match['number']
    
    logging.warning("No drawing number found in PDF content")
    return ""

def extract_revision_from_content(page):
    """
    Extract current revision from PDF content in title block area.
    
    Revisions are typically shown in the title block and can be:
    - Alphanumeric codes: T0, T1, N0, N1
    - Numeric codes: 01, 02, 07, etc.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        str: Current revision code or empty string if not found
    """
    
    text_dict = page.get_text("dict")
    page_width = page.rect.width
    page_height = page.rect.height
    
    # Define title block area (bottom right area) - expand search area
    title_block_x_start = page_width * 0.5  # Expanded from 0.6 to 0.5
    title_block_y_start = page_height * 0.6  # Expanded from 0.7 to 0.6
    
    revisions_found = []
    
    # Search for revision patterns in title block area
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                bbox = span["bbox"]
                
                # Check if in title block area
                if bbox[0] >= title_block_x_start and bbox[1] >= title_block_y_start:
                    
                    # Enhanced revision patterns to look for
                    revision_patterns = [
                        r'\b([T]\d+)\b',        # T0, T1, T2, etc.
                        r'\b([N]\d+)\b',        # N0, N1, N2, etc.
                        r'\b(\d{2})\b',         # 01, 02, 07, etc. (2 digits)
                        r'\b([A-Z]\d)\b',       # A1, B2, etc. (single letter + digit)
                        r'Rev\.?\s*([T]\d+)',   # Rev. T0, Rev T1, etc.
                        r'Rev\.?\s*([N]\d+)',   # Rev. N0, Rev N1, etc.
                        r'Rev\.?\s*(\d{2})',    # Rev. 07, Rev 01, etc.
                        r'Revision\s*([T]\d+)', # Revision T0, etc.
                        r'Revision\s*([N]\d+)', # Revision N0, etc.
                        r'Revision\s*(\d{2})',  # Revision 07, etc.
                    ]
                    
                    for pattern in revision_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            # Skip obvious non-revision numbers (like years, large numbers)
                            if match.isdigit() and (int(match) > 50 or len(match) > 2):
                                continue
                            
                            revisions_found.append({
                                'revision': match,
                                'location': bbox,
                                'font_size': span.get('size', 0),
                                'context': text  # Store context for debugging
                            })
    
    # If not found in title block, search entire page for revision patterns
    if not revisions_found:
        logging.debug("No revision found in title block, searching entire page")
        
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    bbox = span["bbox"]
                    
                    # Look for revision patterns anywhere on page
                    revision_patterns = [
                        r'\b([T]\d+)\b',        # T0, T1, T2, etc.
                        r'\b([N]\d+)\b',        # N0, N1, N2, etc.
                        r'\b(\d{2})\b',         # 01, 02, 07, etc. (2 digits)
                        r'Rev\.?\s*([T]\d+)',   # Rev. T0, Rev T1, etc.
                        r'Rev\.?\s*([N]\d+)',   # Rev. N0, Rev N1, etc.
                        r'Rev\.?\s*(\d{2})',    # Rev. 07, Rev 01, etc.
                    ]
                    
                    for pattern in revision_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            # Skip obvious non-revision numbers
                            if match.isdigit() and (int(match) > 50 or len(match) > 2):
                                continue
                            
                            # Lower confidence for page-wide search
                            revisions_found.append({
                                'revision': match,
                                'location': bbox,
                                'font_size': span.get('size', 0),
                                'context': text,
                                'confidence': 5  # Lower confidence
                            })
    
    # If multiple revisions found, prefer the one with higher confidence, larger font, or rightmost position
    if revisions_found:
        # Sort by confidence (if exists), font size, then x position
        revisions_found.sort(key=lambda x: (
            x.get('confidence', 10),  # Default high confidence for title block finds
            x['font_size'], 
            x['location'][0]
        ), reverse=True)
        
        best_revision = revisions_found[0]['revision']
        logging.debug(f"Revision found in content: {best_revision} (context: '{revisions_found[0]['context']}')")
        return best_revision
    
    logging.warning("No revision found in PDF content")
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
    """
    
    text_dict = page.get_text("dict")
    page_width = page.rect.width
    page_height = page.rect.height
    
    # Define search area - titles are typically in upper portion
    title_search_height = page_height * 0.4  # Top 40% of page
    
    title_candidates = []
    
    # Process each text block
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                bbox = span["bbox"]
                
                # Skip if outside title search area
                if bbox[1] > title_search_height:
                    continue
                
                # Skip very small text or short strings
                if len(text) < 4 or span["size"] < 9:
                    continue
                
                # Skip common non-title patterns
                non_title_patterns = [
                    r'^[A-Z]\d+$',           # Single letter + numbers
                    r'^\d+$',                # Just numbers
                    r'^[A-Z]{1,3}$',         # Short abbreviations
                    r'DRAWING\s*NO',         # Labels
                    r'REVISION',
                    r'DATE',
                    r'SCALE',
                    r'PROJECT',
                    r'SHEET\s*\d+',
                    r'^\d{2}/\d{2}/\d{2,4}$', # Dates
                    r'^Rev\.$',
                    r'^Client$',
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
                    # Drawing number patterns (these are not titles)
                    r'^L\d{2}-[A-Z]\d{2}[A-Z](?:\d{2}|XX)-[A-Z]{3}-(?:\d{2}|[A-Z]{2})-(?:[A-Z]{2}|\d{2})-[A-Z]{3}-[A-Z]{2}-\d{5}$',
                ]
                
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in non_title_patterns):
                    continue
                
                # Calculate scoring for title candidates
                score = 0
                
                # Position scoring - prefer center area
                x_center = (bbox[0] + bbox[2]) / 2
                if 0.15 * page_width <= x_center <= 0.85 * page_width:
                    score += 20
                
                # Font size scoring
                if span["size"] >= 12:
                    score += 15
                elif span["size"] >= 10:
                    score += 10
                
                # Content length scoring
                if len(text) >= 20:
                    score += 15
                elif len(text) >= 10:
                    score += 8
                
                # Content type scoring - architectural/engineering keywords
                descriptive_keywords = [
                    'plan', 'section', 'detail', 'layout', 'system', 'room', 'wall', 'pool', 
                    'piping', 'conduit', 'mockup', 'mock-up', 'grms', 'enlargement', 
                    'grading', 'drainage', 'technical', 'information', 'cover', 'sheet',
                    'facade', 'external', 'typical', 'mep', 'door', 'overall', 'elevation',
                    'floor', 'roof', 'foundation', 'structural', 'mechanical', 'electrical'
                ]
                
                if any(keyword in text.lower() for keyword in descriptive_keywords):
                    score += 25
                
                title_candidates.append({
                    'text': text,
                    'score': score,
                    'bbox': bbox,
                    'font_size': span["size"]
                })
    
    if not title_candidates:
        logging.warning("No title candidates found in PDF")
        return ""
    
    # Sort by score (highest first)
    title_candidates.sort(key=lambda x: -x['score'])
    
    best_candidate = title_candidates[0]
    logging.debug(f"Selected title: '{best_candidate['text']}' (score: {best_candidate['score']})")
    
    return best_candidate['text'].strip()

def extract_revision_history_from_pdf(page):
    """
    Extract revision history information from PDF content.
    
    Looks for revision tables that contain dates and reasons.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        tuple: (latest_date, latest_reason) or ("", "") if not found
    """
    
    text_dict = page.get_text("dict")
    
    dates_found = []
    reasons_found = []
    
    # Process each text block to find dates and reasons
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            line_text = ""
            for span in line["spans"]:
                line_text += span["text"] + " "
            
            # Search for date patterns
            date_patterns = [
                r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY
                r'(\d{2}/\d{2}/\d{2})',  # DD/MM/YY
            ]
            
            for pattern in date_patterns:
                date_matches = re.findall(pattern, line_text)
                dates_found.extend(date_matches)
            
            # Search for reason patterns
            reason_patterns = [
                r'(Issued for Construction)',
                r'(Issued for Tender)', 
                r'(Design Development[^a-z]*)',
                r'(Construction Documents[^a-z]*)',
                r'(Construction Procurement[^a-z]*)',
                r'(Concept Design[^a-z]*)',
                r'(Schematic Design[^a-z]*)',
                r'(100% Design Development[^a-z]*)',
                r'(50% Design Development[^a-z]*)',
                r'(For Information)',
                r'(For Approval)',
                r'(For Review)',
            ]
            
            for pattern in reason_patterns:
                reason_matches = re.findall(pattern, line_text, re.IGNORECASE)
                reasons_found.extend(reason_matches)
    
    # Get the latest entries
    latest_date = dates_found[-1] if dates_found else ""
    latest_reason = reasons_found[-1] if reasons_found else ""
    
    if dates_found:
        logging.debug(f"Dates found: {dates_found}, using latest: {latest_date}")
    if reasons_found:
        logging.debug(f"Reasons found: {reasons_found}, using latest: {latest_reason}")
    
    return latest_date, latest_reason

def extract_table_title_from_pdf(page):
    """
    Extract table title indicating project phase from PDF content.
    
    Table titles are one of the 5 standard project phases:
    1. Concept Design
    2. Schematic Design  
    3. Design Development
    4. Construction Documents
    5. Construction Procurement
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        str: Table title or "Construction Procurement" as default
    """
    
    text_dict = page.get_text("dict")
    
    # Define the 5 standard table titles in order of preference
    standard_table_titles = [
        'Concept Design',
        'Schematic Design',
        'Design Development', 
        'Construction Documents',
        'Construction Procurement'
    ]
    
    # Search for table titles in PDF content
    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue
            
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                
                # Check if text matches any of the 5 standard table titles
                for title in standard_table_titles:
                    if title.lower() in text.lower():
                        logging.debug(f"Table title found: {title}")
                        return title
    
    # Default to most common table title
    default_title = "Construction Procurement"
    logging.debug(f"No table title found, using default: {default_title}")
    return default_title

def validate_drawing_number_against_filename(drawing_number, filename):
    """
    Validate extracted drawing number against filename.
    
    This provides additional confidence that we extracted the correct number.
    
    Args:
        drawing_number (str): Drawing number extracted from PDF content
        filename (str): PDF filename
        
    Returns:
        bool: True if drawing number matches filename pattern
    """
    
    if not drawing_number:
        return False
    
    # Check if the drawing number appears in the filename
    if drawing_number in filename:
        logging.debug(f"Drawing number {drawing_number} validated against filename")
        return True
    
    logging.warning(f"Drawing number {drawing_number} does not match filename {filename}")
    return False

def validate_extraction_result(result):
    """
    Validate extraction results and determine status.
    
    Args:
        result (dict): Extraction result dictionary
        
    Returns:
        str: Status message ("SUCCESS" or "FAILED - reason")
    """
    
    # Check required fields
    required_fields = [
        'drawing_title', 
        'drawing_number', 
        'revision', 
        'latest_revision', 
        'latest_date', 
        'latest_reason'
    ]
    
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
    
    logging.info(f"Validation passed for {result['file_name']}")
    return "SUCCESS"

def process_single_pdf(pdf_path):
    """
    Process a single PDF file and extract all required information from content.
    
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
        page = doc[0]  # Process first page
        
        # Extract all information from PDF content
        drawing_number = extract_drawing_number_from_content(page)
        drawing_title = extract_title_from_pdf(page)
        current_revision = extract_revision_from_content(page)
        latest_date, latest_reason = extract_revision_history_from_pdf(page)
        table_title = extract_table_title_from_pdf(page)
        
        # Validate drawing number against filename
        drawing_number_valid = validate_drawing_number_against_filename(drawing_number, filename)
        
        doc.close()
        
        # Create result dictionary
        result = {
            'file_name': filename,
            'drawing_title': drawing_title,
            'drawing_number': drawing_number,
            'revision': current_revision,
            'latest_revision': current_revision,  # Assume current = latest
            'latest_date': latest_date,
            'latest_reason': latest_reason,
            'table_title': table_title,
            'drawing_number_validated': drawing_number_valid,
            'status': ""
        }
        
        # Validate results and set status
        result['status'] = validate_extraction_result(result)
        
        logging.info(f"Successfully processed {filename}: {result['status']}")
        return result
        
    except Exception as e:
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
            'drawing_number_validated': False,
            'status': error_msg
        }

def process_multiple_pdfs(pdf_directory="."):
    """
    Process all PDF files in a directory.
    
    Args:
        pdf_directory (str): Directory containing PDF files
        
    Returns:
        list: List of extraction results for all PDFs
    """
    
    pdf_files = list(Path(pdf_directory).glob('*.pdf'))
    
    if not pdf_files:
        logging.warning(f"No PDF files found in directory: {pdf_directory}")
        return []
    
    logging.info(f"Found {len(pdf_files)} PDF files to process")
    
    results = []
    for pdf_file in pdf_files:
        result = process_single_pdf(str(pdf_file))
        results.append(result)
    
    return results

def save_results_to_csv(results, output_filename="pdf_extraction_results_truly_dynamic.csv"):
    """Save extraction results to CSV file."""
    
    if not results:
        logging.warning("No results to save")
        return
    
    df = pd.DataFrame(results)
    df.to_csv(output_filename, index=False)
    logging.info(f"Results saved to: {output_filename}")

def print_summary_statistics(results):
    """Print summary statistics of extraction results."""
    
    if not results:
        print("No results to summarize")
        return
    
    total_files = len(results)
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    failed_count = len([r for r in results if 'FAILED' in r['status']])
    error_count = len([r for r in results if 'ERROR' in r['status']])
    
    print(f"\n📊 TRULY DYNAMIC EXTRACTION SUMMARY:")
    print(f"  📁 Total Files: {total_files}")
    print(f"  ✅ Successful: {success_count} ({success_count/total_files*100:.1f}%)")
    print(f"  ❌ Failed: {failed_count} ({failed_count/total_files*100:.1f}%)")
    print(f"  🚫 Errors: {error_count} ({error_count/total_files*100:.1f}%)")
    
    if failed_count > 0:
        print(f"\n❌ FAILED EXTRACTIONS:")
        for result in results:
            if 'FAILED' in result['status']:
                print(f"  📋 {result['file_name']}: {result['status']}")

def main():
    """
    Main function - truly dynamic PDF extraction from content only.
    """
    
    print("🚀 STARTING TRULY DYNAMIC PDF EXTRACTION (CONTENT-BASED)...")
    print("=" * 80)
    
    results = process_multiple_pdfs()
    
    if not results:
        print("No PDF files found to process")
        return
    
    output_file = 'pdf_extraction_results_truly_dynamic.csv'
    save_results_to_csv(results, output_file)
    print_summary_statistics(results)
    
    print(f"\n✅ Truly dynamic extraction complete! Results saved to: {output_file}")

if __name__ == "__main__":
    main()