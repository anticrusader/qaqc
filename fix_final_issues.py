#!/usr/bin/env python3
"""
Final fixes for remaining PDF extraction issues
"""

import fitz
import pandas as pd
import re
from pathlib import Path

def debug_specific_pdf(pdf_path):
    """Debug specific PDF extraction issues"""
    print(f"\n🔍 DEBUGGING: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # Get all text with positions
        text_dict = page.get_text("dict")
        
        print(f"📄 Page dimensions: {page.rect}")
        
        # Look for title blocks and drawing numbers
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 3:
                            bbox = span["bbox"]
                            print(f"  📍 [{bbox[0]:.0f},{bbox[1]:.0f}] '{text}'")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error debugging {pdf_path}: {e}")

def extract_title_improved(page):
    """Improved title extraction with better positioning logic"""
    text_dict = page.get_text("dict")
    page_width = page.rect.width
    page_height = page.rect.height
    
    # Define title search area (top portion of page)
    title_area_height = page_height * 0.3
    
    title_candidates = []
    
    for block in text_dict["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    bbox = span["bbox"]
                    
                    # Skip if not in title area
                    if bbox[1] > title_area_height:
                        continue
                    
                    # Skip very small text or single characters
                    if len(text) < 3 or span["size"] < 8:
                        continue
                    
                    # Skip common non-title patterns
                    skip_patterns = [
                        r'^[A-Z]\d+$',  # Single letter + numbers
                        r'^\d+$',       # Just numbers
                        r'^[A-Z]{1,3}$', # Short abbreviations
                        r'DRAWING\s*NO',
                        r'REVISION',
                        r'DATE',
                        r'SCALE',
                        r'PROJECT',
                        r'SHEET\s*\d+',
                        r'^\d{2}/\d{2}/\d{2,4}$',  # Dates
                    ]
                    
                    if any(re.search(pattern, text, re.IGNORECASE) for pattern in skip_patterns):
                        continue
                    
                    # Calculate score based on position, size, and content
                    score = 0
                    
                    # Position scoring (prefer center-left area)
                    x_center = (bbox[0] + bbox[2]) / 2
                    if 0.2 * page_width <= x_center <= 0.8 * page_width:
                        score += 20
                    
                    # Size scoring
                    if span["size"] >= 12:
                        score += 15
                    elif span["size"] >= 10:
                        score += 10
                    
                    # Content scoring
                    if len(text) >= 20:
                        score += 10
                    elif len(text) >= 10:
                        score += 5
                    
                    # Prefer descriptive words
                    descriptive_words = ['plan', 'section', 'detail', 'layout', 'system', 'room', 'wall', 'pool', 'piping']
                    if any(word in text.lower() for word in descriptive_words):
                        score += 15
                    
                    title_candidates.append({
                        'text': text,
                        'score': score,
                        'bbox': bbox,
                        'size': span["size"]
                    })
    
    if not title_candidates:
        return ""
    
    # Sort by score and return best candidate
    title_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Try to combine adjacent high-scoring candidates
    best_candidate = title_candidates[0]
    
    # Look for continuation on same or next line
    combined_title = best_candidate['text']
    used_candidates = [best_candidate]
    
    for candidate in title_candidates[1:]:
        # Check if this could be a continuation
        if (abs(candidate['bbox'][1] - best_candidate['bbox'][1]) < 20 and  # Same line
            candidate['bbox'][0] > best_candidate['bbox'][2] - 10):  # Adjacent
            combined_title += " " + candidate['text']
            used_candidates.append(candidate)
        elif (candidate['bbox'][1] > best_candidate['bbox'][1] and  # Next line
              candidate['bbox'][1] - best_candidate['bbox'][3] < 30 and  # Close vertically
              abs(candidate['bbox'][0] - best_candidate['bbox'][0]) < 50):  # Similar x position
            combined_title += " " + candidate['text']
            used_candidates.append(candidate)
    
    return combined_title.strip()

def extract_drawing_number_improved(page, filename):
    """Improved drawing number extraction"""
    # First try to extract from filename
    filename_match = re.search(r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})', filename)
    if filename_match:
        return filename_match.group(1)
    
    # Then try from PDF content
    text_dict = page.get_text("dict")
    
    drawing_number_patterns = [
        r'([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        r'DRAWING\s*NO\.?\s*:?\s*([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
        r'DWG\s*NO\.?\s*:?\s*([A-Z]\d{2}-[A-Z]\d{2}[A-Z]\d{2}-[A-Z]{3}-\d{2}-[A-Z]{2}-[A-Z]{3}-[A-Z]{2}-\d{5})',
    ]
    
    for block in text_dict["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    line_text += span["text"] + " "
                
                for pattern in drawing_number_patterns:
                    match = re.search(pattern, line_text, re.IGNORECASE)
                    if match:
                        return match.group(1) if len(match.groups()) > 0 else match.group(0)
    
    return ""

# Test the problematic files
problematic_files = [
    "L02-R02D01-FOS-00-XX-DWG-AR-00001[07].pdf",
    "L02-R02DXX-RSG-00-ZZ-SKT-LS-12801[N0] - Sample Sketch.pdf",
    "L04-A04D02-CHP-16-00-DWG-SP-10001[N0].pdf"
]

for filename in problematic_files:
    if Path(filename).exists():
        print(f"\n{'='*80}")
        debug_specific_pdf(filename)
        
        # Test improved extraction
        try:
            doc = fitz.open(filename)
            page = doc[0]
            
            title = extract_title_improved(page)
            drawing_number = extract_drawing_number_improved(page, filename)
            
            print(f"\n🔧 IMPROVED EXTRACTION:")
            print(f"  📝 Title: '{title}'")
            print(f"  🔢 Drawing Number: '{drawing_number}'")
            
            doc.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")