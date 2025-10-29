#!/usr/bin/env python3
"""
Check revision values in all Excel files
"""

import openpyxl
from pathlib import Path

def check_all_excel_revisions():
    """Check revision values in all Excel files"""
    
    excel_files = list(Path('.').glob('*.xlsx'))
    
    for excel_file in excel_files:
        if excel_file.name.startswith('~$'):  # Skip temp files
            continue
            
        try:
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active
            
            revision_value = sheet.cell(row=12, column=2).value
            
            print(f"{excel_file.name}: Revision = '{revision_value}' (type: {type(revision_value)})")
            
            workbook.close()
            
        except Exception as e:
            print(f"Error reading {excel_file.name}: {e}")

if __name__ == "__main__":
    check_all_excel_revisions()