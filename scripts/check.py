import json
records = json.load(open("data/records.json", encoding="utf-8"))

for r in records:
    if r["common"] in ("Cheer Pheasant", "Koklass Pheasant", "Kalij Pheasant"):
        print(r["text"])

print("\nWith a global status:", sum(1 for r in records if r["gts"]))
print("With a national status:", sum(1 for r in records if r["nts"]))
print("With CITES:", sum(1 for r in records if r["cites"]))