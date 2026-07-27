"""FinQuery — Streamlit chat UI (DeepSeek-inspired dark theme)."""

from __future__ import annotations

import html
import os

import requests
import streamlit as st

st.set_page_config(
    page_title="FinQuery",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

_DEFAULT_API_URL = os.getenv("FINQUERY_API_URL", "http://localhost:8000")

_CONNECTION_ERROR = (
    "Cannot connect to the API. Start it in another terminal, then set "
    "API URL to http://localhost:8000\n\n"
    "PowerShell:\n"
    "  cd finquery-rag\n"
    "  $env:PYTHONPATH = '.'\n"
    "  uvicorn api.main:app --reload --port 8000"
)

_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --fq-bg: #0d0d0f;
        --fq-surface: #161618;
        --fq-surface-2: #1e1e22;
        --fq-border: #2a2a30;
        --fq-text: #ececf1;
        --fq-muted: #8e8ea0;
        --fq-accent: #4d6bfe;
        --fq-accent-soft: rgba(77, 107, 254, 0.15);
        --fq-teal: #14b8a6;
        --fq-user-bg: #2a2a35;
        --fq-radius: 12px;
        --fq-danger: #f87171;
        --fq-success: #5eead4;
        --fq-warn: #facc15;
    }

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
        background-color: var(--fq-bg) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #121214 0%, #0d0d0f 100%) !important;
        border-right: 1px solid var(--fq-border) !important;
        min-width: 18rem !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span { color: var(--fq-text) !important; }
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--fq-muted) !important;
    }
    [data-testid="stSidebar"] hr { border-color: var(--fq-border) !important; }

    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 7rem !important;
        max-width: 52rem !important;
    }

    /* Fixed bottom chat bar */
    [data-testid="stBottomBlockContainer"],
    section[data-testid="stBottom"] {
        background: var(--fq-bg) !important;
        border-top: 1px solid var(--fq-border) !important;
    }
    [data-testid="stBottomBlockContainer"] .block-container {
        max-width: 52rem !important;
        padding-top: 0.75rem !important;
        padding-bottom: 0.75rem !important;
    }

    /* Header */
    .fq-header { text-align: center; padding: 0.5rem 0 1.25rem; margin-bottom: 0.25rem; }
    .fq-logo {
        font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em;
        background: linear-gradient(135deg, #ececf1 0%, #4d6bfe 50%, #14b8a6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .fq-tagline { color: var(--fq-muted); font-size: 0.9rem; margin: 0.35rem 0 0; }

    /* Empty state */
    .fq-empty {
        text-align: center; padding: 3rem 1.5rem; margin: 2rem auto; max-width: 28rem;
        background: var(--fq-surface); border: 1px solid var(--fq-border); border-radius: 16px;
    }
    .fq-empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; opacity: 0.9; }
    .fq-empty h3 { color: var(--fq-text); font-weight: 600; margin: 0 0 0.5rem; }
    .fq-empty p { color: var(--fq-muted); font-size: 0.875rem; line-height: 1.5; margin: 0; }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0.35rem 0 !important;
    }
    [data-testid="stChatMessageAvatarUser"] {
        background: linear-gradient(135deg, #4d6bfe, #6366f1) !important;
    }
    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #14b8a6, #0d9488) !important;
    }
    [data-testid="stChatMessageContent"] {
        background: var(--fq-surface) !important;
        border: 1px solid var(--fq-border) !important;
        border-radius: var(--fq-radius) !important;
        color: var(--fq-text) !important;
        padding: 0.85rem 1rem !important;
    }
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li {
        color: var(--fq-text) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] {
        background: var(--fq-user-bg) !important;
        border-color: #3a3a48 !important;
    }

    /* Source cards */
    .fq-source {
        background: var(--fq-surface-2); border: 1px solid var(--fq-border);
        border-left: 3px solid var(--fq-teal); border-radius: 8px;
        padding: 0.65rem 0.85rem; margin: 0.4rem 0; font-size: 0.8rem;
    }
    .fq-source-title { color: var(--fq-text); font-weight: 600; margin-bottom: 0.25rem; }
    .fq-source-meta { color: var(--fq-accent); font-size: 0.75rem; margin-bottom: 0.35rem; }
    .fq-source-snippet { color: var(--fq-muted); line-height: 1.45; margin: 0; }
    .fq-meta-line { color: var(--fq-muted); font-size: 0.75rem; margin: 0.5rem 0 0; }

    /* Sidebar brand */
    .fq-sidebar-brand {
        font-size: 1.35rem; font-weight: 700; color: var(--fq-text);
        letter-spacing: -0.02em; margin: 0 0 0.15rem;
    }
    .fq-sidebar-sub { color: var(--fq-muted); font-size: 0.8rem; margin: 0 0 1rem; }
    .fq-pill {
        display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px;
        font-size: 0.7rem; font-weight: 600; margin-right: 0.35rem;
    }
    .fq-pill-ok { background: rgba(20, 184, 166, 0.2); color: var(--fq-success); }
    .fq-pill-warn { background: rgba(234, 179, 8, 0.15); color: var(--fq-warn); }

    /* Buttons */
    .stButton > button {
        background: var(--fq-surface-2) !important;
        color: var(--fq-text) !important;
        border: 1px solid var(--fq-border) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: border-color 0.15s ease, background 0.15s ease !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        border-color: var(--fq-accent) !important;
        background: var(--fq-accent-soft) !important;
        color: var(--fq-text) !important;
    }
    .stButton > button:focus,
    .stButton > button:focus-visible {
        border-color: var(--fq-accent) !important;
        box-shadow: 0 0 0 1px rgba(77, 107, 254, 0.35) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4d6bfe, #6366f1) !important;
        border: none !important;
        color: #fff !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        white-space: normal !important;
        height: auto !important;
        min-height: 2.5rem;
        line-height: 1.35 !important;
        text-align: left !important;
        padding: 0.5rem 0.75rem !important;
    }

    /* Text inputs — override Streamlit primary (red) focus ring */
    .stTextInput label { color: var(--fq-muted) !important; }
    .stTextInput [data-baseweb="input"],
    .stTextInput > div > div {
        background: var(--fq-surface-2) !important;
        border-color: var(--fq-border) !important;
        border-radius: 10px !important;
    }
    .stTextInput input {
        background: transparent !important;
        color: var(--fq-text) !important;
        caret-color: var(--fq-accent) !important;
    }
    .stTextInput [data-baseweb="input"]:focus-within,
    .stTextInput > div > div:focus-within {
        border-color: var(--fq-accent) !important;
        box-shadow: 0 0 0 1px rgba(77, 107, 254, 0.35) !important;
    }

    /* Chat input — override :focus-within primary (red) border */
    [data-testid="stChatInput"] {
        border: none !important;
        padding-top: 0 !important;
        background: transparent !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] .stChatInput > div {
        border: 1px solid var(--fq-border) !important;
        border-radius: 14px !important;
        background: var(--fq-surface) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] > div:focus-within,
    [data-testid="stChatInput"] .stChatInput > div:focus-within {
        border-color: var(--fq-accent) !important;
        box-shadow: 0 0 0 1px rgba(77, 107, 254, 0.35) !important;
    }
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="base-input"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"] {
        background: transparent !important;
        color: var(--fq-text) !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        caret-color: var(--fq-accent) !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--fq-muted) !important;
        opacity: 0.85;
    }
    [data-testid="stChatInputSubmitButton"] button {
        outline: none !important;
        color: var(--fq-muted) !important;
    }
    [data-testid="stChatInputSubmitButton"] button:not(:disabled) {
        color: var(--fq-accent) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--fq-surface-2) !important;
        border-radius: 8px !important;
        color: var(--fq-muted) !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid var(--fq-border) !important;
        border-radius: 10px !important;
        background: transparent !important;
    }
    div[data-testid="stExpander"] .fq-source { margin-top: 0.25rem; }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--fq-surface-2);
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        border: 1px solid var(--fq-border);
    }
    [data-testid="stMetricLabel"] { color: var(--fq-muted) !important; }
    [data-testid="stMetricValue"] {
        color: var(--fq-text) !important;
        font-size: 0.95rem !important;
    }

    /* Alerts & status */
    [data-testid="stAlert"] {
        background: var(--fq-surface-2) !important;
        border: 1px solid var(--fq-border) !important;
        color: var(--fq-text) !important;
        border-radius: 10px !important;
    }
    [data-testid="stAlert"] code {
        background: var(--fq-bg) !important;
        color: var(--fq-text) !important;
    }
    div[data-testid="stNotificationContentSuccess"] {
        background: rgba(20, 184, 166, 0.12) !important;
        color: var(--fq-success) !important;
    }
    div[data-testid="stNotificationContentError"] {
        background: rgba(248, 113, 113, 0.12) !important;
        color: var(--fq-danger) !important;
    }
    div[data-testid="stNotificationContentWarning"] {
        background: rgba(250, 204, 21, 0.1) !important;
        color: var(--fq-warn) !important;
    }

    /* Spinner */
    [data-testid="stSpinner"] { color: var(--fq-muted) !important; }
    [data-testid="stSpinner"] > div { border-top-color: var(--fq-accent) !important; }

    hr { border-color: var(--fq-border) !important; margin: 1rem 0 !important; }
    footer { visibility: hidden; height: 0; }

    /* Prevent empty <p> gaps from HTML fragments */
    [data-testid="stMarkdownContainer"] p:empty { display: none !important; margin: 0 !important; }
</style>
"""

st.markdown(_THEME_CSS, unsafe_allow_html=True)

if "api_url" not in st.session_state:
    st.session_state.api_url = _DEFAULT_API_URL
if "messages" not in st.session_state:
    st.session_state.messages = []
if "prefill" not in st.session_state:
    st.session_state.prefill = ""
if "api_status" not in st.session_state:
    st.session_state.api_status = None


def _html(fragment: str) -> None:
    """Render compact HTML (no leading newlines — avoids broken Streamlit wrappers)."""
    st.markdown(fragment.strip(), unsafe_allow_html=True)


def api_call(method, endpoint, data=None):
    """Make API call, return (response_dict, error_string)."""
    base = st.session_state.get("api_url") or _DEFAULT_API_URL
    try:
        if method == "GET":
            r = requests.get(f"{base}{endpoint}", timeout=10)
        elif method == "POST":
            r = requests.post(f"{base}{endpoint}", json=data, timeout=120)
        elif method == "DELETE":
            r = requests.delete(f"{base}{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.HTTPError as e:
        detail = str(e)
        try:
            body = e.response.json()
            if isinstance(body.get("detail"), list):
                msgs = [
                    d.get("msg", str(d))
                    for d in body["detail"]
                    if isinstance(d, dict)
                ]
                detail = "; ".join(msgs) if msgs else detail
            elif isinstance(body.get("detail"), str):
                detail = body["detail"]
        except Exception:
            pass
        return None, detail
    except requests.exceptions.ConnectionError:
        return None, _CONNECTION_ERROR
    except Exception as e:
        return None, str(e)


def render_sources(sources: list) -> None:
    """Render retrieved source chunks as compact cards."""
    if not sources:
        return
    with st.expander(f"Sources · {len(sources)} passages", expanded=False):
        for src in sources:
            snippet = html.escape(src.get("snippet", "")[:200])
            fname = html.escape(src.get("filename", "unknown"))
            score = src.get("relevance_score", 0)
            _html(
                f'<div class="fq-source">'
                f'<div class="fq-source-title">📄 {fname}</div>'
                f'<div class="fq-source-meta">Relevance {score:.3f}</div>'
                f'<p class="fq-source-snippet">{snippet}…</p>'
                f"</div>"
            )


def render_assistant_message(msg: dict) -> None:
    """Render one assistant turn with optional sources and metadata."""
    with st.chat_message("assistant", avatar="📊"):
        if msg.get("is_error"):
            st.error(msg["content"])
        else:
            st.markdown(msg["content"])
        if msg.get("sources"):
            render_sources(msg["sources"])
        if msg.get("processing_time_ms"):
            model = html.escape(str(msg.get("model", "")))
            ms = msg["processing_time_ms"]
            _html(f'<p class="fq-meta-line">⚡ {ms} ms · {model}</p>')


# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    _html(
        '<p class="fq-sidebar-brand">FinQuery</p>'
        '<p class="fq-sidebar-sub">Financial document intelligence</p>'
    )

    st.session_state.api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        placeholder="http://localhost:8000",
    )

    if st.button("Check connection", use_container_width=True, type="primary"):
        data, err = api_call("GET", "/health")
        st.session_state.api_status = (data, err)

    status = st.session_state.api_status
    if status:
        data, err = status
        if err:
            st.error(err)
        elif data:
            ready = data.get("pipeline_ready", False)
            chunks = data.get("total_chunks", 0)
            if ready:
                _html(
                    f'<span class="fq-pill fq-pill-ok">Ready</span>'
                    f'<span style="color:var(--fq-muted);font-size:0.8rem">'
                    f"{chunks} chunks indexed</span>"
                )
            else:
                _html('<span class="fq-pill fq-pill-warn">Not indexed</span>')
                st.caption("Load documents to enable Q&A.")
            c1, c2 = st.columns(2)
            groq_ok = data.get("groq_configured", False)
            jina_ok = data.get("jina_configured", False)
            c1.metric("Groq", "✓" if groq_ok else "—")
            c2.metric("Jina", "✓" if jina_ok else "—")

    st.divider()

    if st.button("Load documents", use_container_width=True):
        with st.spinner("Indexing with Jina embeddings…"):
            data, err = api_call("POST", "/ingest", {})
        if err:
            st.error(err)
        else:
            st.success(f"Indexed {data['chunks_added']} chunks")
            st.caption(", ".join(data.get("sources", [])))
            st.session_state.api_status = None

    st.caption(
        "Uses data/raw/ if present, otherwise sample_docs/ (Apple 10-K sample)."
    )

    st.divider()
    st.markdown("**Suggested questions**")

    suggestions = [
        ("Total net sales in 2023?", "What was Apple's total net sales in 2023?"),
        ("Main risk factors?", "What are the main risk factors?"),
        ("R&D spending?", "How much was spent on R&D?"),
        ("Cash position?", "What is the cash position?"),
    ]
    for label, question in suggestions:
        if st.button(label, use_container_width=True, key=f"suggest_{question}"):
            st.session_state.prefill = question

    st.divider()
    if st.button("Clear chat & index", use_container_width=True):
        data, err = api_call("DELETE", "/reset")
        if err:
            st.error(err)
        else:
            st.session_state.messages = []
            st.session_state.api_status = None
            st.success("Chat and vector store cleared")
            st.rerun()

# ── Main chat area ──────────────────────────────────────────────────────
_html(
    '<div class="fq-header">'
    '<div class="fq-logo">FinQuery</div>'
    '<p class="fq-tagline">Ask questions grounded in your financial filings · Groq + Jina + Chroma</p>'
    "</div>"
)

if not st.session_state.messages:
    _html(
        '<div class="fq-empty">'
        '<div class="fq-empty-icon">💬</div>'
        '<h3>How can I help you today?</h3>'
        "<p>Load documents from the sidebar, then ask about revenue, risks, R&D, cash, "
        "and more. Answers cite your indexed sources.</p>"
        "</div>"
    )

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        render_assistant_message(msg)

prefill_val = st.session_state.get("prefill", "")
if prefill_val:
    st.session_state.prefill = ""

prompt = st.chat_input("Message FinQuery…")
user_input = (prompt or prefill_val or "").strip()

if user_input:
    if len(user_input) < 3:
        st.warning("Please enter at least 3 characters.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="📊"):
        with st.spinner("Searching documents…"):
            data, err = api_call("POST", "/query", {"question": user_input})

        if err:
            st.error(err)
            st.session_state.messages.append(
                {"role": "assistant", "content": err, "is_error": True}
            )
        else:
            st.markdown(data["answer"])
            sources = data.get("sources", [])
            if sources:
                render_sources(sources)
            if data.get("processing_time_ms"):
                _html(
                    f'<p class="fq-meta-line">⚡ {data["processing_time_ms"]} ms · '
                    f"{html.escape(str(data.get('model', '')))}</p>"
                )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": sources,
                    "processing_time_ms": data.get("processing_time_ms"),
                    "model": data.get("model"),
                }
            )
    st.rerun()
