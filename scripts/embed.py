import json, os, time
import numpy as np
from google import genai
from google.genai import errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
records = json.load(open("data/records.json", encoding="utf-8"))
texts = [r["text"] for r in records]

CACHE = "data/embed_cache.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

BATCH = 50
for i in range(0, len(texts), BATCH):
    if str(i) in cache:
        continue  # already done in an earlier run
    while True:
        try:
            res = client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts[i:i + BATCH],
            )
            cache[str(i)] = [e.values for e in res.embeddings]
            json.dump(cache, open(CACHE, "w"))
            print(f"Embedded {min(i + BATCH, len(texts))}/{len(texts)}")
            break
        except errors.ClientError as e:
            if e.code == 429:
                print("Rate limit hit, waiting 60s...")
                time.sleep(60)
            else:
                raise
    time.sleep(35)  # keeps you under 100 texts/minute

vecs = []
for i in range(0, len(texts), BATCH):
    vecs += cache[str(i)]

np.save("data/embeddings.npy", np.array(vecs, dtype="float32"))
print("Saved data/embeddings.npy", np.array(vecs).shape)