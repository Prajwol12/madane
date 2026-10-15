import json, re
import numpy as np
import streamlit as st
from google import genai

st.set_page_config(page_title="Birds of Madane", page_icon="🦅")
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Tried in order; if one is unavailable or out of quota, the next is used.
LLM_MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]


@st.cache_resource
def load_data():
    recs = json.load(open("data/records.json", encoding="utf-8"))
    emb = np.load("data/embeddings.npy")
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
    return recs, emb


records, emb = load_data()


def retrieve(query, k=8):
    res = client.models.embed_content(model="gemini-embedding-001", contents=query)
    q = np.array(res.embeddings[0].values, dtype="float32")
    q = q / np.linalg.norm(q)
    top = np.argsort(emb @ q)[::-1][:k]
    return [records[i] for i in top]


def status_filter(query):
    """Exact lookups for list-style status questions, where vector search is weak."""
    q = query.lower()
    listy = any(w in q for w in ["list", "which", "all ", "how many", "name"])

    # CITES appendix questions, e.g. "birds in CITES Appendix I"
    m = re.search(r"cites\s*(?:appendix\s*)?(iii|ii|i)\b", q)
    if m:
        app = m.group(1).upper()
        return [r for r in records if r["cites"].strip().upper() == app]
    if "cites" in q and listy:
        return [r for r in records if r["cites"].strip()]

    # National / global threat status lists and counts
    if listy and "national" in q:
        return [r for r in records if r["nts"]]
    if listy and "global" in q:
        return [r for r in records if r["gts"]]

    # General "threatened / protected" lists
    if listy and any(w in q for w in ["threatened", "endangered", "vulnerable", "protected"]):
        return [r for r in records if r["gts"] or r["nts"] or r["cites"]]
    return []


def generate(prompt):
    last_error = None
    for model in LLM_MODELS:
        try:
            return client.models.generate_content(model=model, contents=prompt).text
        except Exception as e:
            last_error = e
    raise last_error


SYSTEM = """You answer questions about the birds recorded in Madane Forest Conservation Area,
using ONLY the context below (from the Bird Conservation Nepal checklist, 2025).
Status codes: global status (STG), national status (STN), CITES appendix.
VU = Vulnerable, EN = Endangered, CR = Critically Endangered, NT = Near Threatened.
"not listed" means the checklist shows no status for that bird.
If the context begins with "Total matching records", use that number for counting questions.
If the context does not contain the answer, say you could not find it in the checklist.
Do not guess or use outside knowledge. Keep answers clear and short."""

with st.sidebar:
    st.header("About")
    st.write(
        "Answers come from the Birds of Madane Forest Conservation Area "
        "checklist (Bird Conservation Nepal, 2025)."
    )

st.title("🦅 Madane Bird Status Assistant")
st.caption("Ask me about any bird in Madane Forest. Version 2!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

if q := st.chat_input("e.g. What is the status of the Cheer Pheasant?"):
    st.chat_message("user").write(q)

    try:
        filtered = status_filter(q)
        hits = filtered or retrieve(q)
        body = "\n".join(h["text"] for h in hits)
        context = f"Total matching records: {len(hits)}\n{body}" if filtered else body
        history = "\n".join(
            f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]
        )
        answer = generate(
            f"{SYSTEM}\n\nContext:\n{context}\n\n"
            f"Recent chat:\n{history}\n\nQuestion: {q}"
        )
    except Exception:
        context = ""
        answer = "Sorry, something went wrong. Please try again in a minute."

    st.chat_message("assistant").write(answer)
    if context:
        with st.expander("Sources used from the checklist"):
            st.text(context)

    st.session_state.messages.append({"role": "user", "content": q})
    st.session_state.messages.append({"role": "assistant", "content": answer})