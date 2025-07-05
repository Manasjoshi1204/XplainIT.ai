import streamlit as st
from utils.theme import apply_custom_css

def show(dark_mode):
    apply_custom_css(dark_mode)

    # Heading + tagline
    st.markdown("""
    <div style="text-align: center; margin-top: 80px;">
        <h1 style="font-size: 3em;">🧠 XplainIT.ai</h1>
        <p style="font-size: 1.2em; color: gray;">Explain complex topics in your style — smart, clear, and human.</p>
    </div>
    """, unsafe_allow_html=True)

    # Image
    st.markdown("""
    <div style="text-align: center; margin-top: 30px;">
        <img src="https://img.icons8.com/external-flaticons-lineal-color-flat-icons/96/null/external-explain-agile-flaticons-lineal-color-flat-icons.png" />
    </div>
    """, unsafe_allow_html=True)

    # Start Button (Streamlit native)
    st.markdown("<div style='text-align: center; margin-top: 40px;'>", unsafe_allow_html=True)
    if st.button("🚀 Start Explaining", use_container_width=False):
        st.session_state.page = "main"
    st.markdown("</div>", unsafe_allow_html=True)
