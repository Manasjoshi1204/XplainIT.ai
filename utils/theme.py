# utils/theme.py - Dark mode only theme

import streamlit as st

def apply_custom_css(dark_mode=True):
    """Apply clean dark theme - light mode removed to avoid conflicts"""
    
    st.markdown("""
    <style>
        /* Import fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Base app styling - DARK MODE ONLY */
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0e1117;
            color: #ffffff;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .main-header h1 {
            color: white;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.2rem;
        }
        
        .category-pill {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            margin: 0.2rem;
            background-color: rgba(255,255,255,0.2);
            border-radius: 20px;
            font-size: 0.9em;
            color: white;
        }
        
        /* Response box */
        .response-box {
            background-color: #262730;
            color: #ffffff;
            border-left: 4px solid #7b3ff2;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            line-height: 1.6;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #262730 !important;
            border: 2px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            padding: 0.75rem !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #7b3ff2 !important;
            outline: none !important;
        }
        
        /* Selectbox */
        .stSelectbox > div > div > select {
            background-color: #262730 !important;
            color: #ffffff !important;
            border: 2px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #7b3ff2;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px rgba(123, 63, 242, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(123, 63, 242, 0.4);
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #7b3ff2, #3b82f6);
            font-size: 1.1rem;
            padding: 1rem 2rem;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #b0b0b0;
            background-color: transparent;
            border: none;
            padding: 0.75rem 0;
            font-weight: 600;
        }
        
        .stTabs [aria-selected="true"] {
            color: #7b3ff2 !important;
            border-bottom: 3px solid #7b3ff2;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1e1e1e;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Metric containers */
        [data-testid="metric-container"] {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Checkbox */
        .stCheckbox > label {
            color: #ffffff !important;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Code blocks */
        code {
            background-color: #1e1e1e;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            color: #ffffff;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .main-header, .response-box {
            animation: fadeIn 0.5s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)
