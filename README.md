# InsightNarrator
### Agentic BI Dashboard with Natural Language Explanations

---

## What it does

Upload any CSV dataset → get auto-generated charts → Claude explains each chart in plain English → ask follow-up questions in natural language.

Solves a real analyst problem: dashboards show **what**, InsightNarrator tells you **why** and **what to do next**.

---

## Setup (5 minutes)

### 1. Clone / download this folder

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get an Anthropic API key
Go to https://console.anthropic.com → create an API key (free tier available)

### 4. Run the app
```bash
python -m streamlit run app.py
```
(On Windows, use this instead of `streamlit run` if the command is not found — pip installs scripts outside your PATH.)

### 5. Open in browser
Streamlit will open at `http://localhost:8501`

---

## How to use

1. Paste your Anthropic API key in the sidebar
2. Upload a CSV file (or click "Load demo dataset")
3. Go to any chart tab — pick your columns — click **Generate + Explain**
4. Read the AI explanation below the chart
5. Ask follow-up questions in the Q&A section at the bottom

---

## Tech stack

| Component | Tool |
|---|---|
| UI | Streamlit |
| Charts | Plotly |
| AI Engine | Claude (claude-sonnet-4) via Anthropic API |
| Data | Pandas |
| Language | Python |

---




