import streamlit as st
from explain_engine import generate_explanation
from utils.theme import apply_custom_css

# 🌗 Theme toggle
dark_mode = st.sidebar.checkbox("🌙 Dark Mode")
apply_custom_css(dark_mode)

# 📄 Page config
st.set_page_config(page_title="XplainIT.ai", layout="centered")
st.title("🧠 XplainIT.ai")
st.subheader("Explain code or concepts your way — by level, tone, and depth")

# 🔍 Inputs
topic = st.text_input("Enter the topic or code snippet")
level = st.selectbox("Select understanding level", ["Beginner", "Intermediate", "Advanced"])
tone = st.selectbox("Select explanation tone", ["Formal", "Casual", "Technical"])
extras = st.text_input("Anything extra to specify? (optional)", placeholder="e.g., Use real-world examples")
language = st.text_input("Preferred language (default: English)", placeholder="e.g., Hindi, Spanish")

# 🚀 Generate button
if st.button("Explain"):
    if topic.strip() == "":
        st.warning("Please enter a topic or code snippet.")
    else:
        with st.spinner("Explaining..."):
            response = generate_explanation(topic, level, tone, extras, language)
        st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)
