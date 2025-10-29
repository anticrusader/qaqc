#!/usr/bin/env python3
"""
Create Excel-friendly CSV that preserves leading zeros in revisions
"""

import pandas as pd
import csv

def create_excel_friendly_csv():
    """Create CSV that preserves leading zeros when opened in Excel"""
    
    # Read the current data
    try:
        df = pd.read_csv('pdf_extraction_results_excel_based_fixed.csv', encoding='utf-8-sig')
    except:
        df = pd.read_csv('pdf_extraction_results_excel_based_fixed.csv', encoding='utf-8')
    
    print("Original data:")
    print(df[['file_name', 'revision', 'latest_revision']].head())
    
    # Method 1: Add leading apostrophe to force text format in Excel
    df_method1 = df.copy()
    df_method1['revision'] = df_method1['revision'].apply(lambda x: f"'{x}" if pd.notna(x) else x)
    df_method1['latest_revision'] = df_method1['latest_revision'].apply(lambda x: f"'{x}" if pd.notna(x) else x)
    
    # Method 2: Add ="07" format to force Excel to treat as text
    df_method2 = df.copy()
    df_method2['revision'] = df_method2['revision'].apply(lambda x: f'="{x}"' if pd.notna(x) else x)
    df_method2['latest_revision'] = df_method2['latest_revision'].apply(lambda x: f'="{x}"' if pd.notna(x) else x)
    
    # Method 3: Use tab-separated values (TSV) which Excel handles better
    df_method3 = df.copy()
    
    # Method 4: Manual CSV writing with proper quoting
    def write_csv_with_quotes(df, filename):
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            
            # Write header
            writer.writerow(df.columns)
            
            # Write data rows
            for _, row in df.iterrows():
                # Convert all values to strings and ensure revisions keep leading zeros
                row_data = []
                for col, value in row.items():
                    if col in ['revision', 'latest_revision'] and pd.notna(value):
                        # Ensure it's a string with leading zeros preserved
                        str_value = str(value)
                        if str_value.isdigit() and len(str_value) == 1:
                            str_value = f"0{str_value}"
                        row_data.append(str_value)
                    else:
                        row_data.append(str(value) if pd.notna(value) else "")
                
                writer.writerow(row_data)
    
    # Save different versions
    output_files = [
        ('pdf_results_method1_apostrophe.csv', df_method1, 'standard'),
        ('pdf_results_method2_formula.csv', df_method2, 'standard'),
        ('pdf_results_method3.tsv', df_method3, 'tsv'),
        ('pdf_results_method4_quoted.csv', df, 'manual'),
    ]
    
    for filename, data, method in output_files:
        try:
            if method == 'tsv':
                data.to_csv(filename, index=False, sep='\t', encoding='utf-8-sig')
            elif method == 'manual':
                write_csv_with_quotes(data, filename)
            else:
                data.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"✅ Created: {filename}")
            
            # Show sample of what was written
            if method == 'manual':
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()[:3]  # First 3 lines
                    print(f"   Sample content:")
                    for i, line in enumerate(lines):
                        print(f"   Line {i+1}: {line.strip()}")
            
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
    
    print(f"\n📋 Try opening these files in Excel:")
    print(f"1. pdf_results_method1_apostrophe.csv - Uses ' prefix")
    print(f"2. pdf_results_method2_formula.csv - Uses =\"07\" format") 
    print(f"3. pdf_results_method3.tsv - Tab-separated values")
    print(f"4. pdf_results_method4_quoted.csv - All fields quoted")

if __name__ == "__main__":
    create_excel_friendly_csv()