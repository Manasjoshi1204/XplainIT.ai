# Enhanced main.py - XplainIT.ai with Authentication + WORKING Load Button
import streamlit as st
import requests
from datetime import datetime
import re
import warnings
import json
import sys
import os
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_path)

# Try to import local modules, fallback if not available
try:
    from utils.theme import apply_custom_css
    HAS_THEME = True
except ImportError:
    HAS_THEME = False

try:
    from explain_engine import generate_explanation
    HAS_LOCAL_ENGINE = True
except ImportError:
    HAS_LOCAL_ENGINE = False

# Backend configuration
BACKEND_URL = ("BACKEND_URL", "http://localhost:8000")

# Page config with better SEO
st.set_page_config(
    page_title="XplainIT.ai - Explain Anything, Simply", 
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state - INCLUDING TOPIC_TO_LOAD AND AUTO_GENERATE
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'selected_example' not in st.session_state:
    st.session_state.selected_example = ""
if 'regenerate_requested' not in st.session_state:
    st.session_state.regenerate_requested = False
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""
if 'current_response' not in st.session_state:
    st.session_state.current_response = ""
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = ""
if 'topic_to_load' not in st.session_state:
    st.session_state.topic_to_load = ""
if 'auto_generate' not in st.session_state:
    st.session_state.auto_generate = False

# Authentication functions
def signup_user(username, email, password, full_name):
    """Register a new user"""
    try:
        response = requests.post(f"{BACKEND_URL}/auth/signup", json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name
        })
        return response
    except requests.exceptions.RequestException:
        return None

def login_user(username, password):
    """Login user and get JWT token"""
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", data={
            "username": username,
            "password": password
        })
        return response
    except requests.exceptions.RequestException:
        return None

def get_user_info(token):
    """Get current user information"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        return response
    except requests.exceptions.RequestException:
        return None

def call_explain_api(topic, level, tone, extras, language, token):
    """Call the protected explain API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BACKEND_URL}/api/explain", 
                               json={
                                   "topic": topic,
                                   "level": level,
                                   "tone": tone,
                                   "extras": extras,
                                   "language": language
                               },
                               headers=headers)
        return response
    except requests.exceptions.RequestException:
        return None

def get_user_history(token):
    """Get user's explanation history"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/history", headers=headers)
        return response
    except requests.exceptions.RequestException:
        return None

def clean_response(response):
    """Clean up AI response and format with markdown headings"""
    import re
    # Remove HTML divs
    response = re.sub(r'</?div[^>]*>', '', response)
    
    # Convert *Heading* or **Heading** (at start of line) to markdown heading
    response = re.sub(r'^\*{1,2}([^\n*]+)\*{1,2}\s*$', r'### \1', response, flags=re.MULTILINE)
    
    # Convert lines ending with : or ? to markdown heading
    response = re.sub(r'^(.+?[\?:])\s*$', r'### \1', response, flags=re.MULTILINE)

    # Replace extra bold/italic markup in the content
    response = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'**\1**', response)

    # Convert bullets
    response = re.sub(r'^\s*•\s?', '- ', response, flags=re.MULTILINE)
    response = re.sub(r'^\s*-\s?', '- ', response, flags=re.MULTILINE)

    # Remove excessive empty lines
    response = re.sub(r'\n{3,}', '\n\n', response)

    return response.strip()

def fallback_generate_explanation(topic, level, tone, extras, language):
    """Fallback explanation when backend is not available"""
    return f"""
    ## {topic}

    **Note:** This is a demo explanation since the backend is not available.

    **Level:** {level} | **Tone:** {tone} | **Language:** {language}

    This would normally be a comprehensive explanation of **{topic}** tailored to your {level.lower()} level understanding in a {tone.lower()} tone.

    ### Key Points:
    - Professional AI explanation would be generated here
    - Customized for your learning preferences
    - Including examples and analogies as requested

    **To get real AI explanations, please ensure your backend server is running at {BACKEND_URL}**

    Additional context: {extras}
    """

# Authentication Section
if not st.session_state.authenticated:
    # Check if backend is available
    try:
        test_response = requests.get(f"{BACKEND_URL}/test", timeout=2)
        backend_available = test_response.status_code == 200
    except:
        backend_available = False
    
    if not backend_available:
        st.error(f"⚠️ Backend server not available at {BACKEND_URL}. Please start your backend first.")
        st.info("To start backend: `cd backend` then `python app.py`")
        st.stop()

    st.markdown("""           
                
    <div style="text-align: center; margin-top: 0; padding: 0;">
        <h1 style="margin-top: 0;">🧠 XplainIT.ai</h1>
        <p style="font-size: 1.2rem; color: #888;">Your Personal AI Tutor with Secure User Accounts</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Login/Signup tabs
    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with auth_tab1:
        st.markdown("### Login to Your Account")
        
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("🔑 Login", use_container_width=True)
            
            if login_submit:
                if login_username and login_password:
                    with st.spinner("Logging in..."):
                        response = login_user(login_username, login_password)
                        
                        if response and response.status_code == 200:
                            data = response.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.authenticated = True
                            
                            # Get user info
                            user_response = get_user_info(st.session_state.token)
                            if user_response and user_response.status_code == 200:
                                st.session_state.user_info = user_response.json()
                            
                            st.success("✅ Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                else:
                    st.error("Please fill in all fields")
    
    with auth_tab2:
        st.markdown("### Create New Account")
        
        with st.form("signup_form"):
            signup_username = st.text_input("Choose Username")
            signup_email = st.text_input("Email Address")
            signup_fullname = st.text_input("Full Name (Optional)")
            signup_password = st.text_input("Create Password", type="password")
            signup_password2 = st.text_input("Confirm Password", type="password")
            signup_submit = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if signup_submit:
                if signup_username and signup_email and signup_password:
                    if signup_password == signup_password2:
                        with st.spinner("Creating account..."):
                            response = signup_user(signup_username, signup_email, signup_password, signup_fullname)
                            
                            if response and response.status_code == 200:
                                st.success("✅ Account created successfully! Please login.")
                            elif response and response.status_code == 400:
                                st.error("❌ Username or email already exists")
                            else:
                                st.error("❌ Failed to create account")
                    else:
                        st.error("Passwords don't match")
                else:
                    st.error("Please fill in all required fields")

else:
    # Authenticated User Interface - CLEAN SIDEBAR WITH WORKING LOAD BUTTON
    
    # Sidebar with clean user info
    with st.sidebar:
        # Clean user info section
        if st.session_state.user_info:
            st.markdown("### 👋 Welcome back!")
            st.markdown(f"**Username:** {st.session_state.user_info.get('username', 'Unknown')}")
            st.markdown(f"**Email:** {st.session_state.user_info.get('email', 'Unknown')}")
            
            # Show backend explanation count (most accurate) - only if > 0
            total_explanations = st.session_state.user_info.get('total_explanations', 0)
            if total_explanations > 0:
                st.markdown(f"**Explanations Generated:** {total_explanations}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.user_info = None
            st.session_state.history = []  # Clear history on logout
            st.success("Logged out successfully!")
            st.rerun()
        
        st.title("⚙️ Settings")
        
        # Apply theme if available
        if HAS_THEME:
            dark_mode = True  # Fixed to dark mode
            apply_custom_css(dark_mode)
        
        # History section - FIXED VERSION WITH WORKING LOAD BUTTON
        st.markdown("---")
        st.markdown("### 📜 Recent History")

        # Load backend history with error handling
        if st.button("🔄 Refresh History"):
            with st.spinner("Loading history..."):
                history_response = get_user_history(st.session_state.token)
                if history_response and history_response.status_code == 200:
                    try:
                        history_data = history_response.json()
                        backend_history = history_data.get('explanations', [])
                        
                        # Convert backend format to local format - SAFE VERSION
                        st.session_state.history = []
                        for exp in backend_history:
                            st.session_state.history.append({
                                'topic': exp.get('topic', 'Untitled'),
                                'response': exp.get('explanation', 'No explanation available'),
                                'level': exp.get('level', 'Unknown'),
                                'tone': exp.get('tone', 'Unknown'),
                                'timestamp': exp.get('timestamp', ''),
                                'settings': {
                                    'level': exp.get('level', 'Unknown'),
                                    'tone': exp.get('tone', 'Unknown'),
                                    'language': exp.get('language', 'English'),
                                    'extras': exp.get('extras', '')
                                }
                            })
                        
                        if st.session_state.history:
                            st.success(f"✅ Loaded {len(st.session_state.history)} explanations from history!")
                        else:
                            st.info("No history found. Start asking questions!")
                            
                    except Exception as e:
                        st.error(f"❌ Error parsing history data: {str(e)}")
                else:
                    st.error("❌ Failed to load history. Please try again.")

        # Show recent history items - CORRECTED WORKING LOAD BUTTON VERSION
        if st.session_state.history:
            st.write(f"**Showing {len(st.session_state.history)} recent items:**")
            for i, item in enumerate(reversed(st.session_state.history[-5:])):
                # Safe access to all dictionary keys
                topic = item.get('topic', 'Untitled')
                timestamp = item.get('timestamp', '')
                level = item.get('level', 'Unknown')
                
                # Handle timestamp formatting safely
                try:
                    if timestamp:
                        display_time = timestamp[:10] if 'T' in timestamp else timestamp[:10]
                    else:
                        display_time = "Unknown date"
                except:
                    display_time = "Unknown date"
                
                with st.expander(f"{topic[:25]}...", expanded=False):
                    st.caption(f"🕐 {display_time}")
                    st.caption(f"📊 Level: {level}")
                    
                    # CORRECTED LOAD BUTTON - NOW TRIGGERS AUTO GENERATION
                    if st.button("📋 Load Topic", key=f"load_history_{i}"):
                        # Set the topic to be loaded
                        st.session_state.topic_to_load = topic
                        st.session_state.input_text = topic
                        
                        # Load the previous explanation immediately
                        st.session_state.current_response = item.get('response', '')
                        st.session_state.current_topic = topic
                        
                        # Set flag to trigger automatic explanation generation (optional)
                        # st.session_state.auto_generate = True
                        
                        st.success(f"✅ Loaded topic with explanation: {topic[:30]}...")
                        st.rerun()
        else:
            st.info("No history yet. Generate some explanations first, then click '🔄 Refresh History'!")

    # Main content area with improved header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 XplainIT.ai</h1>
        <p>Explain anything in the world, tailored to your understanding</p>
        <div style="margin-top: 1rem;">
            <span class="category-pill">🔬 Science</span>
            <span class="category-pill">🎨 Art</span>
            <span class="category-pill">📚 History</span>
            <span class="category-pill">💻 Technology</span>
            <span class="category-pill">🏥 Medicine</span>
            <span class="category-pill">🌍 Culture</span>
            <span class="category-pill">💰 Finance</span>
            <span class="category-pill">🎯 Any Topic!</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Create simplified tabs
    tab1, tab2 = st.tabs(["🎯 Ask Anything", "📊 About"])

    with tab1:
        # Main input section
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Topic input - FIXED TO HANDLE LOADED TOPICS FROM HISTORY
            st.markdown("### What would you like to understand better?")

            # Handle loaded topic from history - IMPROVED APPROACH
            default_value = st.session_state.input_text
            
            # Check if we have a topic to load from history
            if st.session_state.topic_to_load:
                default_value = st.session_state.topic_to_load
                # Clear after using it
                st.session_state.topic_to_load = ""
            
            # Handle selected example from category buttons
            elif st.session_state.selected_example:
                default_value = st.session_state.selected_example
                st.session_state.selected_example = ""

            topic = st.text_area(
                "Enter any topic, question, concept, or even paste content to explain:",
                height=150,
                value=default_value,
                placeholder="""Examples:
• How does photosynthesis work?
• Explain the 2008 financial crisis
• What is quantum computing?
• How do vaccines work?
• Explain this Shakespeare sonnet: [paste text]
• What caused World War I?
• How does blockchain technology work?
• Explain the theory of relativity
• What is impressionism in art?
• How does the stock market work?
• Explain this medical report: [paste text]
• What is CRISPR gene editing?
• How do hurricanes form?
• Explain this legal document: [paste text]
• What is the meaning of life? (philosophy)
• How does machine learning work?
• Explain this recipe in detail: [paste text]
• What is cognitive behavioral therapy?
• How do electric cars work?
• Literally anything you're curious about!""",
                key="main_input"
            )

            # Update session state with current input
            st.session_state.input_text = topic
        
        with col2:
            st.markdown("### 🎲 Quick Examples")
            
            # Diverse category buttons
            categories = {
                "🔬 Science": [
                    "How do black holes work?",
                    "What is DNA?",
                    "Climate change explained"
                ],
                "🎨 Arts": [
                    "What is the Mona Lisa's significance?",
                    "Jazz music origins",
                    "Modern art movements"
                ],
                "📚 History": [
                    "The Renaissance period",
                    "Ancient Egyptian civilization",
                    "The Cold War"
                ],
                "🏥 Health": [
                    "How does the immune system work?",
                    "What is mental health?",
                    "Nutrition basics"
                ],
                "💰 Finance": [
                    "What is cryptocurrency?",
                    "How do mortgages work?",
                    "Stock market basics"
                ],
                "🌍 Culture": [
                    "World religions overview",
                    "Cultural traditions",
                    "Language families"
                ]
            }
            
            selected_category = st.selectbox("Choose a category:", list(categories.keys()))
            
            for example in categories[selected_category]:
                if st.button(example, use_container_width=True, key=f"ex_{example}"):
                    st.session_state.selected_example = example
                    st.rerun()
        
        # Advanced settings in an expander
        with st.expander("🔧 Customize Your Explanation", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                level = st.selectbox(
                    "My Understanding Level",
                    ["Beginner", "Intermediate", "Advanced"],
                    help="We'll adjust the complexity accordingly"
                )
                
            with col2:
                tone = st.selectbox(
                    "Explanation Style",
                    ["Casual", "Formal", "Technical"],
                    help="How would you like us to explain?"
                )
                
            with col3:
                language = st.selectbox(
                    "Language",
                    ["English", "Spanish", "French", "Hindi", "Chinese", "German", "Japanese", "Arabic"],
                    help="Get explanations in your preferred language"
                )
            
            # Additional options
            col1, col2 = st.columns(2)
            with col1:
                include_examples = st.checkbox("Include Real-World Examples", value=True)
                include_analogies = st.checkbox("Use Simple Analogies", value=True)
                visual_aids = st.checkbox("Describe Visual Concepts", value=False)
            
            with col2:
                include_history = st.checkbox("Add Historical Context", value=False)
                include_resources = st.checkbox("Suggest Learning Resources", value=False)
                eli5_mode = st.checkbox("ELI5 Mode (Explain Like I'm 5)", value=False)
            
            extras = st.text_input(
                "Any specific angle or focus?",
                placeholder="e.g., Focus on practical applications, Compare with alternatives, Include recent developments"
            )
        
        # Generate button with better styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_button = st.button(
                "🚀 Explain This To Me",
                type="primary",
                use_container_width=True
            )
        
        # Check if regeneration was requested (Deeper Dive)
        if st.session_state.regenerate_requested:
            generate_button = True
            st.session_state.regenerate_requested = False
        
        # NEW: Auto-generate explanation for loaded topics
        if st.session_state.auto_generate:
            generate_button = True
            st.session_state.auto_generate = False
        
        # Generation logic - ENHANCED WITH BACKEND
        if generate_button:
            if not topic or topic.strip() == "":
                st.error("🚫 Please enter a topic or question to explain!")
            else:
                # Build enhanced prompt
                enhanced_extras = []
                if include_examples:
                    enhanced_extras.append("Include practical real-world examples")
                if include_analogies:
                    enhanced_extras.append("Use simple, relatable analogies")
                if visual_aids:
                    enhanced_extras.append("Describe visual representations where helpful")
                if include_history:
                    enhanced_extras.append("Add historical context and evolution")
                if include_resources:
                    enhanced_extras.append("Suggest resources for further learning")
                if eli5_mode:
                    enhanced_extras.append("Explain as if to a 5-year-old child")
                if extras:
                    enhanced_extras.append(extras)
                
                final_extras = ". ".join(enhanced_extras)
                
                # Show simple spinner
                with st.spinner("🧠 Generating your explanation..."):
                    # Try backend first, fallback to local
                    if st.session_state.token:
                        api_response = call_explain_api(topic, level, tone, final_extras, language, st.session_state.token)
                        if api_response and api_response.status_code == 200:
                            explanation_data = api_response.json()
                            response = explanation_data['explanation']
                            
                            # Refresh user info to get updated explanation count
                            user_response = get_user_info(st.session_state.token)
                            if user_response and user_response.status_code == 200:
                                st.session_state.user_info = user_response.json()
                        else:
                            # Fallback to local generation or demo
                            if HAS_LOCAL_ENGINE:
                                response = generate_explanation(topic, level, tone, final_extras, language)
                            else:
                                response = fallback_generate_explanation(topic, level, tone, final_extras, language)
                    else:
                        # Fallback to local generation
                        if HAS_LOCAL_ENGINE:
                            response = generate_explanation(topic, level, tone, final_extras, language)
                        else:
                            response = fallback_generate_explanation(topic, level, tone, final_extras, language)
                
                # Store response in session state
                st.session_state.current_response = response
                st.session_state.current_topic = topic

        # Display response if it exists in session state
        if 'current_response' in st.session_state and st.session_state.current_response:
            st.markdown("---")
            st.markdown("### 💡 Your Personalized Explanation")
            
            # Clean the response
            cleaned_response = clean_response(st.session_state.current_response)
            
            # Display with custom styling
            st.markdown("""
            <style>
            div[data-testid="stMarkdownContainer"] .response-box {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%) !important;
                border-left: 5px solid #7b3ff2 !important;
                border-radius: 15px !important;
                padding: 2.5rem !important;
                margin: 1.5rem 0 !important;
                box-shadow: 0 10px 40px rgba(123, 63, 242, 0.15) !important;
                border: 1px solid rgba(123, 63, 242, 0.2) !important;
                color: #ffffff !important;
            }
            div[data-testid="stMarkdownContainer"] .response-box h3 {
                color: #7b3ff2 !important;
                font-size: 1.4rem !important;
                font-weight: 700 !important;
                margin: 1.5rem 0 1rem 0 !important;
            }
            div[data-testid="stMarkdownContainer"] .response-box p {
                color: #e0e0e0 !important;
                line-height: 1.8 !important;
                font-size: 1.05rem !important;
            }
            div[data-testid="stMarkdownContainer"] .response-box strong {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display with clean container
            st.markdown(f"""
            <div class="response-box">
            {cleaned_response}
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("👍 Helpful", use_container_width=True):
                    st.success("Thanks for your feedback!")
            
            with col2:
                if st.button("🔄 Explain Differently", use_container_width=True):
                    st.info("🔄 Adjust the settings above and click 'Explain This To Me' again for a different explanation!")
            
            with col3:
                if st.button("🔍 Deeper Dive", use_container_width=True):
                    st.session_state.input_text = f"Explain {st.session_state.current_topic} in more detail with advanced concepts"
                    st.session_state.regenerate_requested = True
                    st.rerun()
            
            with col4:
                if st.download_button(
                    "💾 Save",
                    data=f"Topic: {st.session_state.current_topic}\n\nExplanation:\n{st.session_state.current_response}",
                    file_name=f"explanation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    use_container_width=True
                ):
                    st.success("Downloaded!")

    # ABOUT TAB
    with tab2:
        st.markdown("### 📊 About XplainIT.ai")
        st.markdown("""
        ## Welcome to XplainIT.ai! 🧠
        
        Your personal AI tutor that explains **anything** in the world, tailored to your understanding level.
        
        ### ✨ What Makes Us Special:
        - **Universal Knowledge**: From quantum physics to ancient history, art to technology
        - **Adaptive Learning**: Explanations that match your knowledge level
        - **Multiple Languages**: Get explanations in your preferred language
        - **Interactive Experience**: Beautiful UI with personalized features
        - **Secure User Accounts**: Your history is saved and protected
        
        ### 🎯 Perfect For:
        - **Students** learning new concepts
        - **Professionals** exploring new fields  
        - **Curious minds** who love to learn
        - **Anyone** with questions about the world
        
        ### 🚀 Features:
        - Smart level detection (Beginner → Advanced)
        - Multiple explanation styles (Casual, Formal, Technical)
        - Real-world examples and analogies
        - Learning history and progress tracking
        - Secure authentication and data storage
        - Export explanations for later reference
        
        ### 🔍 How It Works:
        1. **Create Account**: Secure signup with your email
        2. **Ask Anything**: Enter any topic, question, or concept
        3. **Customize**: Choose your level, style, and preferences  
        4. **Learn**: Get personalized explanations with examples
        5. **Track Progress**: Your history is saved automatically
        
        ### 💡 Pro Tips:
        - Use the **ELI5 Mode** for super simple explanations
        - Try different **explanation styles** for varied perspectives
        - Enable **real-world examples** for better understanding
        - Use **Deeper Dive** to explore topics in more detail
        - **Refresh History** to sync with your backend account
        
        ---
        **Built with ❤️ using Streamlit, FastAPI, and AI**
        
        *Making knowledge accessible to everyone, everywhere.*
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 1rem;">
        <p>🧠 XplainIT.ai | Making knowledge accessible to everyone, everywhere</p>
        <p style="font-size: 0.9em;">Learn anything. Understand everything. No topic too complex.</p>
    </div>
    """, unsafe_allow_html=True)
