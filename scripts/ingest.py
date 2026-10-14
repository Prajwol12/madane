import pdfplumber, json, re

AREA = "Madane Forest Conservation Area"

def clean(c):
    c = (c or "").replace("\n", " ").strip()
    c = re.sub(r"(fi|fl|ff|ffi) (?=[a-z])", r"\1", c)  # fixes "Kingfi sher" -> "Kingfisher"
    return re.sub(r"\s+", " ", c)

records = []
order = family = ""

with pdfplumber.open("data/checklist.pdf") as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            for row in table:
                cells = [clean(c) for c in row]
                cells = (cells + [""] * 8)[:8]
                _, common, sci, _nepali, gts, nts, cites, _ref = cells

                filled = [c for c in cells if c]
                if not filled:
                    continue

                # Section rows: only one filled cell (order or family)
                if len(filled) == 1:
                    if filled[0].isupper():
                        order = filled[0]
                    else:
                        family = filled[0]
                    continue

                # Skip header row and anything that isn't a species row
                if common == "Common Name" or not common or not sci:
                    continue

                text = (
                    f"{common} ({sci}), order {order}, family {family}. "
                    f"Recorded in {AREA}. "
                    f"Global status: {gts or 'not listed'}. "
                    f"National status: {nts or 'not listed'}. "
                    f"CITES: {('Appendix ' + cites) if cites else 'not listed'}."
                )
                records.append({"common": common, "scientific": sci,
                                "order": order, "family": family,
                                "gts": gts, "nts": nts, "cites": cites,
                                "text": text})

json.dump(records, open("data/records.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(len(records), "records")
for r in records[:3]:
    print(r["text"])