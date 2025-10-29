#!/usr/bin/env python3
"""
Debug Excel encoding to see exact characters
"""

import openpyxl

def debug_excel_title():
    """Debug the exact characters in Excel title"""
    
    try:
        workbook = openpyxl.load_workbook("L01-H01D01-FOS-00-XX-MUP-AR-80050[T0].xlsx")
        sheet = workbook.active
        
        title = sheet.cell(row=12, column=3).value
        
        print(f"Raw title from Excel: {repr(title)}")
        print(f"Title type: {type(title)}")
        
        if title:
            # Clean up line breaks
            title_clean = str(title).replace('\n', ' ').replace('\r', ' ').strip()
            title_clean = ' '.join(title_clean.split())
            
            print(f"Cleaned title: {repr(title_clean)}")
            print(f"Cleaned title display: {title_clean}")
            
            # Check each character
            print("\nCharacter analysis:")
            for i, char in enumerate(title_clean):
                print(f"  {i}: '{char}' (ord: {ord(char)}, hex: {hex(ord(char))})")
        
        workbook.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_excel_title()