import streamlit as st
from openai import OpenAI

import re

def highlight_logs(text):
    # Highlight ERROR / FATAL / EXCEPTION in red
    text = re.sub(r"(ERROR|FATAL|EXCEPTION)", r"<span style='color:#ff4d4d;font-weight:bold'>\1</span>", text)

    # Highlight WARN in orange
    text = re.sub(r"(WARN|WARNING)", r"<span style='color:#ffa500;font-weight:bold'>\1</span>", text)

    # Highlight INFO in green
    text = re.sub(r"(INFO)", r"<span style='color:#3cff88;font-weight:bold'>\1</span>", text)

    return text


st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }

    /* Title */
    h1, h2, h3, h4 {
        color: #E4F1F6 !important;
    }

    /* Input labels */
    label {
        color: #CDE8F6 !important;
        font-weight: 600;
    }

    /* Text areas + upload boxes */
    textarea, input, .stFileUploader {
        background-color: #0E1B24 !important;
        color: white !important;
        border-radius: 8px;
        border: 1px solid #3a556a !important;
    }

    /* Buttons */
    button {
        background-color: #1f7ae0 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
    }

    button:hover {
        background-color: #3ea0ff !important;
        color: white !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        color: #9dd6ff !important;
        font-weight: 600;
    }

    /* Output markdown */
    .stMarkdown, .stText {
        color: #EAF4FF !important;
    }

    /* Code block */
    pre {
        background-color: #08131e !important;
        border-radius: 10px;
        padding: 12px;
        color: #c7e1ff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# OpenAI client will read OPENAI_API_KEY from your env
client = OpenAI()

BASE_SYSTEM_PROMPT = """
You are an SRE / DevOps copilot that explains incidents clearly.
Given raw logs, you will:
- Summarize what happened in plain English
- Highlight likely root cause(s)
- Suggest 3–5 things to check first
Keep it concise and structured for on-call engineers.
"""

st.set_page_config(
    page_title="DevOps Copilot – Incident Triage",
    page_icon="🛠️",
    layout="wide",
)

st.title("🛠️ LLM DevOps Copilot for Incident Triage")
st.caption("LLM-powered incident triage for production systems")
st.write(
    "Paste incident logs or upload a log file, and the copilot will explain "
    "what’s going on, likely root cause, and what to check first."
)

# --- Incident context controls (top bar) ---
col_ctx1, col_ctx2 = st.columns(2)

with col_ctx1:
    incident_type = st.selectbox(
        "Incident type (for extra context to the copilot)",
        [
            "Generic / Mixed",
            "Timeouts between services",
            "Database errors / connection issues",
            "Authentication / authorization failures",
            "Deployment / rollout issues",
            "Traffic spike / performance degradation",
        ],
    )

with col_ctx2:
    severity = st.slider(
        "Perceived business impact (1 = low, 5 = very high)",
        min_value=1,
        max_value=5,
        value=3,
    )

# --- Main layout: logs on left, summary on right ---
left, right = st.columns([2, 3])

with left:
    st.subheader("Logs input")

    # Text area
    logs_text = st.text_area("Paste logs here", height=260)

    # Optional file upload
    uploaded = st.file_uploader(
        "…or upload a log file (.txt / .log)", type=["txt", "log"]
    )

    if uploaded is not None:
        file_content = uploaded.read().decode("utf-8", errors="ignore")
        if not logs_text.strip():
            logs_text = file_content
        else:
            logs_text = logs_text + "\n" + file_content

    analyze_clicked = st.button("Analyze incident", type="primary", use_container_width=True)

with right:
    st.subheader("📋 Copilot Summary")
    summary_placeholder = st.empty()

if analyze_clicked:
    if not logs_text.strip():
        st.warning("Please paste logs or upload a file first.")
    else:
        # Build a slightly richer system prompt using the controls
        system_prompt = (
            BASE_SYSTEM_PROMPT
            + f"\n\nAdditional context:\n"
              f"- Incident type: {incident_type}\n"
              f"- Reported business impact (1–5): {severity}\n"
              f"Prioritize explanation and checks that match this context."
        )

        user_prompt = (
            "Here are the raw logs. Please follow the instructions in the system prompt.\n\n"
            "Logs:\n```text\n"
            f"{logs_text}\n"
            "```"
        )

        with st.spinner("Asking the copilot…"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            answer = response.choices[0].message.content

        # Show the answer in the right column
        #summary_placeholder.markdown(answer)
        summary_placeholder.markdown(highlight_logs(answer), unsafe_allow_html=True)

        # Optional: also show as code block for easy copying
        with right:
            st.markdown("#### Copy-friendly summary")
            st.code(answer, language="markdown")

# --- How this works (for portfolio readers / demo) ---
with st.expander("ℹ️ How this copilot works"):
    st.markdown(
        """
        This mini-app sends your pasted or uploaded logs to an LLM (OpenAI `gpt-4o-mini`)
        together with a structured system prompt.

        The copilot:
        - Reads the raw log lines
        - Uses the **incident type** and **severity** you selected as extra context
        - Returns a structured summary with:
          - What happened
          - Likely root cause(s)
          - 3–5 concrete checks for the on-call engineer

        No logs are stored by this app; they are only used to generate the current answer.
        """
    )
