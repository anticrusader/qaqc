import pdfplumber

# Let's examine the text structure of one PDF to understand the layout
pdf_path = "L01-H01D02-WSP-75-XX-MUP-IC-80301[T1].pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    
    print("=== RAW TEXT FROM PDF ===")
    print(text)
    print("\n=== TEXT LINES ===")
    lines = text.split('\n')
    for i, line in enumerate(lines):
        print(f"{i:2d}: {line}")