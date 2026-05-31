import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InsightNarrator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }
.stApp { background: #0f0f11; color: #e8e6e0; }
.insight-card {
    background: #1a1a1f; border: 1px solid #2a2a35;
    border-left: 3px solid #c8a96e; border-radius: 8px;
    padding: 1.2rem 1.4rem; margin: 0.8rem 0;
    font-size: 0.92rem; line-height: 1.7; color: #d4d0c8;
}
.section-label {
    font-size: 0.72rem; letter-spacing: 0.12em;
    text-transform: uppercase; color: #666; margin-bottom: 0.5rem;
}
div[data-testid="stSidebar"] { background: #0c0c0f; border-right: 1px solid #1e1e26; }
.stButton > button {
    background: #c8a96e; color: #0f0f11; border: none;
    border-radius: 6px; font-weight: 500;
    font-family: 'DM Sans', sans-serif; padding: 0.5rem 1.2rem;
}
.stButton > button:hover { background: #d4b87e; color: #0f0f11; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1a1a1f; border: 1px solid #2a2a35;
    color: #e8e6e0; border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── Gemini helpers ────────────────────────────────────────────────────────────
def get_gemini_client(api_key: str):
    from google import genai
    return genai.Client(api_key=api_key)


def call_gemini(client, prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


def explain_chart(client, chart_type: str, chart_description: str, stats: dict) -> str:
    prompt = f"""You are an expert data analyst. A user is looking at a {chart_type} chart.

Chart description: {chart_description}

Key statistics from the data:
{json.dumps(stats, indent=2)}

Write a concise, plain-English explanation (3-5 sentences) covering:
1. What the chart shows (the main pattern or finding)
2. One notable observation or anomaly
3. One actionable recommendation or question the analyst should investigate

Be specific and use the actual numbers. Avoid generic statements. Write directly with no preamble."""
    return call_gemini(client, prompt)


def answer_followup(client, question: str, df_summary: str, chart_context: str) -> str:
    prompt = f"""You are an expert data analyst. The user has a question about their dataset.

Dataset summary:
{df_summary}

Current chart context: {chart_context}

User question: {question}

Answer directly and specifically using the data context. 3-4 sentences max.
If the question requires computation you cannot do, say so clearly and suggest how they could find out."""
    return call_gemini(client, prompt)


def compute_stats(df: pd.DataFrame, col: str = None) -> dict:
    stats = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "numeric_columns": list(df.select_dtypes(include="number").columns),
    }
    if col and col in df.columns:
        s = df[col]
        stats[f"{col}_stats"] = {
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "mean": round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
        }
    return stats


def df_summary(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.describe(include="all").to_string(buf)
    return f"Shape: {df.shape}\nColumns: {list(df.columns)}\n\nStats:\n{buf.getvalue()}"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## InsightNarrator")
    st.markdown('<p class="section-label">by Amit A · IIT Ropar</p>', unsafe_allow_html=True)
    st.divider()

    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Free at aistudio.google.com → Get API Key"
    )
    if api_key:
        st.session_state["api_key"] = api_key

    st.divider()
    uploaded = st.file_uploader("Upload CSV dataset", type=["csv"])
    st.divider()
    st.markdown('<p class="section-label">How it works</p>', unsafe_allow_html=True)
    st.markdown("- Upload your data\n- Charts auto-generate\n- AI explains each one\n- Ask follow-up questions")


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# InsightNarrator")
st.markdown("*Your data, explained in plain English — powered by Gemini AI*")
st.divider()

if not st.session_state.get("api_key"):
    st.info("👈 Enter your Gemini API key in the sidebar to get started. Get one free at aistudio.google.com")
    st.stop()

# Init client
try:
    client = get_gemini_client(st.session_state["api_key"])
except Exception as e:
    st.error(f"Could not connect to Gemini: {e}")
    st.stop()

if uploaded is None and "df" not in st.session_state:
    st.markdown("### Upload a CSV to begin")
    if st.button("Load demo dataset"):
        import numpy as np
        np.random.seed(42)
        months = pd.date_range("2024-01-01", periods=12, freq="MS")
        demo = pd.DataFrame({
            "month": months.strftime("%b %Y"),
            "revenue": np.random.randint(80000, 200000, 12),
            "expenses": np.random.randint(50000, 120000, 12),
            "customers": np.random.randint(200, 800, 12),
            "region": np.random.choice(["North", "South", "East", "West"], 12),
        })
        demo["profit"] = demo["revenue"] - demo["expenses"]
        st.session_state["df"] = demo
        st.rerun()
    st.stop()

if uploaded is not None:
    try:
        st.session_state["df"] = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

df = st.session_state["df"]

# ── Dataset overview ──────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<p class="section-label">Rows</p>', unsafe_allow_html=True)
    st.markdown(f"### {len(df):,}")
with c2:
    st.markdown('<p class="section-label">Columns</p>', unsafe_allow_html=True)
    st.markdown(f"### {len(df.columns)}")
with c3:
    numeric_cols = list(df.select_dtypes(include="number").columns)
    st.markdown('<p class="section-label">Numeric columns</p>', unsafe_allow_html=True)
    st.markdown(f"### {len(numeric_cols)}")

with st.expander("Preview raw data"):
    st.dataframe(df.head(20), use_container_width=True)

st.divider()

if not numeric_cols:
    st.warning("No numeric columns found. InsightNarrator needs at least one numeric column to chart.")
    st.stop()

all_cols = list(df.columns)
PLOTLY_THEME = dict(
    paper_bgcolor="#1a1a1f", plot_bgcolor="#1a1a1f",
    font=dict(color="#d4d0c8"), margin=dict(t=30, b=30)
)

st.markdown("## Charts + AI Explanations")
tab1, tab2, tab3 = st.tabs(["📈 Trend / Bar", "🔵 Distribution", "🔗 Correlation"])

# ── Tab 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        y_col = st.selectbox("Y-axis (metric)", numeric_cols, key="bar_y")
    with c2:
        x_col = st.selectbox("X-axis (category or time)", all_cols, key="bar_x")
    chart_type_bar = st.radio("Chart type", ["Bar", "Line"], horizontal=True, key="bar_type")

    if st.button("Generate + Explain", key="btn_bar"):
        with st.spinner("Building chart..."):
            if chart_type_bar == "Bar":
                fig = px.bar(df, x=x_col, y=y_col, color_discrete_sequence=["#c8a96e"], template="plotly_dark")
            else:
                fig = px.line(df, x=x_col, y=y_col, color_discrete_sequence=["#c8a96e"], template="plotly_dark", markers=True)
            fig.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)

        with st.spinner("Gemini is analyzing..."):
            stats = compute_stats(df, y_col)
            desc = f"{y_col} by {x_col} — {chart_type_bar.lower()} chart"
            explanation = explain_chart(client, chart_type_bar, desc, stats)

        st.markdown('<p class="section-label">AI Explanation</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-card">{explanation}</div>', unsafe_allow_html=True)
        st.session_state["last_chart_context"] = desc

# ── Tab 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    dist_col = st.selectbox("Select column", numeric_cols, key="dist_col")
    bins = st.slider("Bins", 10, 100, 30)

    if st.button("Generate + Explain", key="btn_dist"):
        with st.spinner("Building chart..."):
            fig = px.histogram(df, x=dist_col, nbins=bins, color_discrete_sequence=["#c8a96e"], template="plotly_dark")
            fig.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)

        with st.spinner("Gemini is analyzing..."):
            stats = compute_stats(df, dist_col)
            desc = f"Distribution of {dist_col} — histogram with {bins} bins"
            explanation = explain_chart(client, "histogram", desc, stats)

        st.markdown('<p class="section-label">AI Explanation</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-card">{explanation}</div>', unsafe_allow_html=True)
        st.session_state["last_chart_context"] = desc

# ── Tab 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    if len(numeric_cols) < 2:
        st.info("Need at least 2 numeric columns for correlation.")
    else:
        cx1, cx2 = st.columns(2)
        with cx1:
            scatter_x = st.selectbox("X axis", numeric_cols, key="sc_x")
        with cx2:
            scatter_y = st.selectbox("Y axis", numeric_cols, index=1, key="sc_y")
        color_col = st.selectbox("Color by (optional)", ["None"] + all_cols, key="sc_color")

        if st.button("Generate + Explain", key="btn_scatter"):
            with st.spinner("Building chart..."):
                color_arg = None if color_col == "None" else color_col
                fig = px.scatter(df, x=scatter_x, y=scatter_y, color=color_arg,
                                 template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Antique)
                fig.update_layout(**PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)

            with st.spinner("Gemini is analyzing..."):
                corr = df[[scatter_x, scatter_y]].corr().iloc[0, 1]
                stats = compute_stats(df)
                stats["correlation"] = round(corr, 3)
                stats["x_col"] = scatter_x
                stats["y_col"] = scatter_y
                desc = f"Scatter plot of {scatter_x} vs {scatter_y}, correlation = {corr:.2f}"
                explanation = explain_chart(client, "scatter", desc, stats)

            st.markdown('<p class="section-label">AI Explanation</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="insight-card">{explanation}</div>', unsafe_allow_html=True)
            st.session_state["last_chart_context"] = desc

# ── Follow-up Q&A ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("## Ask a follow-up question")
question = st.text_input("Your question", placeholder="e.g. Which region has the highest average revenue?")

if st.button("Ask Gemini", key="btn_qa") and question:
    with st.spinner("Thinking..."):
        context = st.session_state.get("last_chart_context", "No chart selected yet")
        answer = answer_followup(client, question, df_summary(df), context)
    st.markdown('<p class="section-label">AI Answer</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="insight-card">{answer}</div>', unsafe_allow_html=True)
