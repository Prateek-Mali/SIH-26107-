"""Phase-1 test UI. Start the API first:  uvicorn app.api:app --port 8000
Then:  streamlit run ui/streamlit_app.py"""
import json
import os
import uuid

import httpx
import streamlit as st

API = os.getenv("BIS_API_URL", "http://localhost:8000")

st.set_page_config(page_title="BIS Assistant", page_icon="🛡️", layout="centered")
st.title("BIS Assistant")
st.caption("Answers about BIS law, certification, QCOs and hallmarking, with citations to official BIS documents. "
           "Information only, not legal advice.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []


def read_sse(resp):
    event = None
    for line in resp.iter_lines():
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:") and event:
            yield event, json.loads(line[5:].strip())
            event = None


def show_extras(citations, trace):
    if citations:
        with st.expander(f"Source documents ({len(citations)})"):
            for c in citations:
                where = " · ".join(x for x in (c.get("section", "")[:80], f"page {c['page']}" if c.get("page") else "") if x)
                st.markdown(f"**[{c['n']}] [{c['title']}]({c['url']})**  \n{where}  \n"
                            f"<span style='font-size:0.85em;color:gray'>{c['snippet'][:200]}…</span>",
                            unsafe_allow_html=True)
    if trace:
        with st.expander("How I answered"):
            for t in trace:
                step = t.get("step")
                ms = f" ({t['ms']} ms)" if t.get("ms") is not None else ""
                if step == "router":
                    st.markdown(f"**Router**{ms}: intents = `{', '.join(t['intents']) or '—'}`, language = `{t['language']}`"
                                + (", greeting" if t.get("is_greeting") else "")
                                + (", out of scope" if t.get("out_of_scope") else "")
                                + f"  \nsearch query: _{t.get('search_query', '')}_")
                elif step in ("law", "certification", "product_qco", "hallmarking_consumer"):
                    status = "found an answer" if t.get("found") else "NOT_FOUND"
                    st.markdown(f"**{step} agent**{ms}: {status}; retrieved {len(t.get('retrieved', []))} excerpts, "
                                f"cited {len(t.get('used', []))}")
                    for r in t.get("retrieved", []):
                        mark = "✅" if r["chunk_id"] in t.get("used", []) else "·"
                        page = f", p. {r['page']}" if r.get("page") else ""
                        st.caption(f"{mark} {r['title']}{page} — `{r['chunk_id']}` score {r['score']}")
                else:
                    extra = f": {t['note']}" if t.get("note") else ""
                    st.markdown(f"**{step}**{ms}{extra}")
                    for s in t.get("removed", []):
                        st.caption(f"removed: “{s}”")


for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            show_extras(m.get("citations"), m.get("trace"))

with st.sidebar:
    st.subheader("Knowledge base")
    try:
        docs = httpx.get(f"{API}/sources", timeout=10).json()
        st.caption(f"{docs['count']} official documents indexed")
        for d in docs["documents"][:200]:
            st.markdown(f"- [{d['title']}]({d['url']}) · {d['agent']} · {d['date_downloaded']}")
    except Exception:
        st.warning(f"API not reachable at {API}. Start it with: uvicorn app.api:app --port 8000")
    if st.button("New conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

if prompt := st.chat_input("Ask about BIS certification, QCOs, hallmarking… (English or हिन्दी)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        status = st.status("Thinking…", expanded=False)
        box = st.empty()
        text, citations, trace = "", [], []
        try:
            with httpx.stream("POST", f"{API}/chat", timeout=300,
                              json={"message": prompt, "session_id": st.session_state.session_id}) as resp:
                for event, data in read_sse(resp):
                    if event == "status":
                        status.update(label=data["message"] + "…")
                        status.write(data["message"])
                    elif event == "token":
                        text += data["text"]
                        box.markdown(text + "▌")
                    elif event == "citations":
                        citations = data
                    elif event == "trace":
                        trace = data
                    elif event == "error":
                        text = data["message"]
                    elif event == "done":
                        status.update(label=f"Done in {data['latency_ms'] / 1000:.1f} s", state="complete")
        except httpx.HTTPError as e:
            text = f"Could not reach the API at {API}: {e}"
        box.markdown(text)
        show_extras(citations, trace)
    st.session_state.messages.append({"role": "assistant", "content": text, "citations": citations, "trace": trace})
