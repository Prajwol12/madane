import pdfplumber

with pdfplumber.open("data/checklist.pdf") as pdf:
    print("Pages:", len(pdf.pages))
    shown = 0
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        tables = page.extract_tables()
        if i < 3 or "Phasianidae" in text:
            print(f"\n--- Page {i+1}: {len(text)} chars, {len(tables)} tables ---")
            print(text[:600])
            if tables:
                print("FIRST TABLE ROWS:", tables[0][:4])
            shown += 1
        if shown >= 4:
            break