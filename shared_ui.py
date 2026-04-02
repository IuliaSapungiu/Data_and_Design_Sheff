import streamlit as st

def render_navbar():
    # 1. FULL-WIDTH GLASS NAVBAR & FADE ANIMATION
    st.markdown("""
        <div class="top-navbar">
            <h2 style="margin: 0; font-family: 'Helvetica Neue', sans-serif; font-size: 1.5rem; font-weight: 800; letter-spacing: 1px;">
                <span style="color: #002366;">SwimMetrics</span> 
                <span style="color: #00A4E4; font-weight: 400;">| Ultimate Aquatic Intelligence</span>
            </h2>
        </div>
        
        <style>
            /* Hide Streamlit's default top header line */
            [data-testid="stHeader"] { display: none; }
            
            /* Push the app down so it clears the navbar */
            .stApp { padding-top: 80px; }
            
            /* Full-Width Glass Navbar */
            .top-navbar {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                padding: 15px 30px;
                z-index: 99999;
                box-shadow: 0 4px 20px rgba(0, 35, 102, 0.05);
                text-align: center;
            }
            
            /* The Smooth Fade-In and Slide-Up Effect for the entire page */
            .main .block-container {
                animation: fadeSlideUp 1.0s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            
            @keyframes fadeSlideUp {
                0% { opacity: 0; transform: translateY(30px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            
            /* Headers */
            h1, h2, h3 { 
                font-family: 'Helvetica Neue', sans-serif; 
                font-weight: 700;
                color: #002366;
            }
            
            /* Modern 3D Block Navigation Links (Rectangular with soft rounded corners) */
            [data-testid="stPageLink-NavLink"] {
                background: rgba(255, 255, 255, 0.6);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 164, 228, 0.2);
                border-radius: 12px; /* Standard blocky curve, not an oval */
                padding: 10px;
                transition: all 0.3s ease;
                text-align: center;
                text-decoration: none;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
            }
            [data-testid="stPageLink-NavLink"]:hover {
                border-color: #00A4E4; 
                background: #00A4E4;
                transform: translateY(-4px);
                box-shadow: 0 8px 20px rgba(0, 164, 228, 0.25);
            }
            /* Change text color to white when hovering over links */
            [data-testid="stPageLink-NavLink"]:hover p {
                color: white !important;
            }
            [data-testid="stPageLink-NavLink"] p {
                transition: color 0.3s ease;
                color: #002366;
                font-weight: 700;
                margin: 0;
            }
            
            /* Call-to-Action Button (Rectangular with soft corners) */
            .stButton > button {
                background: linear-gradient(135deg, #CFB53B 0%, #B89728 100%);
                color: black !important;
                font-weight: bold;
                border-radius: 12px; /* Standard blocky curve */
                border: none;
                padding: 12px 28px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(207, 181, 59, 0.3);
            }
            .stButton > button:hover {
                background: linear-gradient(135deg, #00A4E4 0%, #0077B6 100%);
                color: white !important;
                transform: translateY(-3px) scale(1.02);
                box-shadow: 0 8px 25px rgba(0, 164, 228, 0.4);
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. CONDITIONAL NAVIGATION BUTTONS
    if st.session_state.get('analytics_loaded', False):
        nav_cols = st.columns(3) # Changed from 4 to 3
        
        with nav_cols[0]:
            st.page_link("control_room.py", label="Home", use_container_width=True)
        with nav_cols[1]:
            st.page_link("pages/01_progression.py", label="Progression", use_container_width=True)
        with nav_cols[2]:
            st.page_link("pages/03_comparator.py", label="Comparator", use_container_width=True) # Shifted from [3] to [2]
        
        st.write("---")