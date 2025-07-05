import streamlit as st

def apply_custom_css(dark_mode):
    if dark_mode:
        st.markdown("""
            <style>
                body, .stApp {
                    background-color: #0E1117;
                    color: white;
                }
                .response-box {
                    background-color: #1E1E1E;
                    color: white;
                    padding: 1rem;
                    border-radius: 12px;
                    margin-top: 1rem;
                    font-size: 1rem;
                    line-height: 1.6;
                }
                input, textarea, select {
                    background-color: #1E1E1E !important;
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                .response-box {
                    background-color: #f0f2f6;
                    color: black;
                    padding: 1rem;
                    border-radius: 12px;
                    margin-top: 1rem;
                    font-size: 1rem;
                    line-height: 1.6;
                }
            </style>
        """, unsafe_allow_html=True)
