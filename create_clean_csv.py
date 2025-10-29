#!/usr/bin/env python3
"""
Create a clean CSV with explicit character handling
"""

import pandas as pd
import unicodedata

def normalize_text(text):
    """Normalize text to handle special characters properly"""
    if not text:
        return text
    
    # Normalize unicode characters
    normalized = unicodedata.normalize('NFC', str(text))
    
    # Replace problematic characters explicitly if needed
    replacements = {
        'ç': 'ç',  # Ensure proper ç character
        'Ã§': 'ç',  # Fix encoding issue
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized

def create_clean_csv():
    """Create a clean CSV with proper character handling"""
    
    # Read the current CSV
    try:
        df = pd.read_csv('pdf_extraction_results_excel_based_fixed.csv', encoding='utf-8-sig')
    except:
        try:
            df = pd.read_csv('pdf_extraction_results_excel_based_fixed.csv', encoding='utf-8')
        except:
            df = pd.read_csv('pdf_extraction_results_excel_based_fixed.csv', encoding='latin1')
    
    # Clean all text columns
    text_columns = ['drawing_title', 'drawing_number', 'latest_reason', 'table_title']
    
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)
    
    # Ensure revision columns are strings
    if 'revision' in df.columns:
        df['revision'] = df['revision'].astype(str)
    if 'latest_revision' in df.columns:
        df['latest_revision'] = df['latest_revision'].astype(str)
    
    # Save with multiple encoding options
    output_files = [
        ('pdf_extraction_results_clean_utf8.csv', 'utf-8'),
        ('pdf_extraction_results_clean_utf8_bom.csv', 'utf-8-sig'),
        ('pdf_extraction_results_clean_latin1.csv', 'latin1'),
    ]
    
    for filename, encoding in output_files:
        try:
            df.to_csv(filename, index=False, encoding=encoding)
            print(f"✅ Created: {filename} (encoding: {encoding})")
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
    
    # Print the data to verify
    print("\n📊 Data verification:")
    for idx, row in df.iterrows():
        print(f"Row {idx}: Title = '{row['drawing_title']}'")
        print(f"         Revision = '{row['revision']}' (type: {type(row['revision'])})")
        if idx == 0:  # Just show first row details
            break

if __name__ == "__main__":
    create_clean_csv()