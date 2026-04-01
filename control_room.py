import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
from data.data_processor import load_and_clean_data
from features.progression import build_progression_features
from features.performance import build_performance_features
from shared_ui import render_navbar

# 1. PAGE CONFIG MUST BE ABSOLUTELY FIRST
st.set_page_config(page_title="SwimMetrics Control Room", layout="wide", initial_sidebar_state="collapsed")

# 2. INJECT CSS IMMEDIATELY TO PREVENT FLASHING (FOUC)
st.markdown("""
    <style>
        /* Nuke Streamlit's default header and decoration line completely */
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        
        /* Remove padding around the main block */
        .block-container {
            padding: 0rem !important;
            max-width: 100% !important;
        }
        
        /* Hero Section */
        .hero-wrapper {
            height: 100vh;
            width: 100vw;
            background: linear-gradient(135deg, #001233 0%, #002366 100%);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 10%;
            color: white;
            font-family: 'Helvetica Neue', sans-serif;
            position: relative;
            box-sizing: border-box;
            overflow: hidden;
            margin: 0;
        }
        
        .hero-left { flex: 1.2; text-align: left; z-index: 2; }
        .hero-right { flex: 0.8; display: flex; justify-content: flex-end; z-index: 2; }

        .hero-main-title {
            font-size: clamp(3rem, 6vw, 5rem);
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
        }

        .hero-sub-text {
            color: #00A4E4;
            font-size: clamp(1rem, 2vw, 1.5rem);
            letter-spacing: 5px;
            text-transform: uppercase;
            font-weight: 300;
        }

        .logo-img {
            width: 100%;
            max-width: 480px;
            filter: drop-shadow(0 20px 50px rgba(0,0,0,0.5));
            animation: float 4s ease-in-out infinite;
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        /* Mobile specific layout */
        @media (max-width: 768px) {
            .hero-wrapper {
                flex-direction: column;
                justify-content: center;
                text-align: center;
                padding: 0 5%;
            }
            .hero-left { margin-bottom: 2rem; flex: 0; }
            .hero-right { justify-content: center; flex: 0; }
            .logo-img { max-width: 250px; }
        }

        .scroll-hint {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            text-align: center;
            font-size: 0.7rem;
            letter-spacing: 3px;
            opacity: 0.6;
            animation: bounce 2s infinite;
            color: white;
            z-index: 10;
        }

        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {transform: translateY(0) translateX(-50%);}
            40% {transform: translateY(-10px) translateX(-50%);}
            60% {transform: translateY(-5px) translateX(-50%);}
        }
    </style>
""", unsafe_allow_html=True)

# 3. SPLASH SCREEN (Runs only on first load)
if 'splash_shown' not in st.session_state:
    st.markdown("""
        <style>
            .splash-container {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background-color: #000; z-index: 9999999; 
                display: flex; justify-content: center; align-items: center;
                animation: fadeOut 1s ease-in-out 3s forwards; 
            }
            .video-bg {
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                object-fit: cover; opacity: 0.4;
            }
            .splash-title { 
                position: relative; color: white; font-size: 6rem; font-weight: 800; 
                letter-spacing: 2px; z-index: 10000000; animation: zoomIn 2.5s forwards; 
            }
            @keyframes zoomIn { 0% { transform: scale(0.6); opacity: 0; } 50% { opacity: 1; } 100% { transform: scale(1.1); opacity: 1; } }
            @keyframes fadeOut { 0% { opacity: 1; visibility: visible; } 100% { opacity: 0; visibility: hidden; z-index: -100; pointer-events: none; } }
        </style>
        <div class="splash-container">
            <video class="video-bg" autoplay loop muted playsinline>
                <source src="https://cdn.pixabay.com/video/2020/05/24/40062-424754162_large.mp4" type="video/mp4">
            </video>
            <div class="splash-title">SwimMetrics</div>
        </div>
    """, unsafe_allow_html=True)
    st.session_state['splash_shown'] = True

# 4. PORTABLE LOGO LOADER
@st.cache_data
def get_base64_img(file_name):
    current_dir = os.path.dirname(__file__)
    path = os.path.join(current_dir, file_name)
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(current_dir), file_name)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

logo_html = get_base64_img("WHITESwimMetrics-Logo.png")

# 5. HERO DISPLAY
st.markdown(f"""
    <div class="hero-wrapper">
        <div class="hero-left">
            <div class="hero-sub-text">Elite Performance Analytics</div>
            <div class="hero-main-title">Precision in <br>Every Stroke</div>
        </div>
        <div class="hero-right">
            <img src="{logo_html}" class="logo-img">
        </div>
        <div class="scroll-hint">SCROLL TO ANALYZE<br>▼</div>
    </div>
""", unsafe_allow_html=True)


# 6. MAIN CONTENT (Using Streamlit Native Columns for Perfect Centering)
st.markdown("<br><br>", unsafe_allow_html=True)

spacer_left, main_col, spacer_right = st.columns([1, 8, 1])

with main_col:
    render_navbar()
    st.title("🎛️ Control Room")

    # Load Data
    with st.spinner("Syncing Database..."):
        df = load_and_clean_data()

    # Logic Filtering
    valid_events = ['50m Freestyle', '100m Freestyle', '200m Freestyle']
    if 'Stroke' in df.columns:
        df = df[df['Stroke'] == 'Freestyle']
    df = df[df['Event'].isin(valid_events)]

    st.subheader("1. System Configuration")
    col1, col2 = st.columns(2)
    with col1:
        selected_gender = st.selectbox("Gender Focus", ['M', 'F'])
        gender_df = df[df['Gender'] == selected_gender]
    with col2:
        selected_event = st.selectbox("Event Focus", valid_events)
        event_df = gender_df[gender_df['Event'] == selected_event]

    # Process summary
    event_df['Swimmer'] = event_df['Swimmer'].str.strip() 
    current_year = event_df['Year'].max()
    swimmer_summary = event_df.groupby('Swimmer').agg(
        latest_year=('Year', 'max'),
        years_competed=('Year', 'nunique'),
        best_time=('Time_Sec', 'min')
    ).reset_index()

    swimmer_summary['Status'] = swimmer_summary['latest_year'].apply(
        lambda y: '🟢 Active' if y >= current_year - 1 else '🔴 Retired/Inactive'
    )

    st.write("---")
    st.subheader(f"🏆 {selected_event} Power Rankings")

    top_10 = swimmer_summary[swimmer_summary['Status'] == '🟢 Active'].nsmallest(10, 'best_time')
    if not top_10.empty:
        fig = px.bar(top_10.sort_values('best_time', ascending=False), 
                     x='best_time', y='Swimmer', orientation='h', 
                     text_auto='.2f', color_discrete_sequence=['#00A4E4'])
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0), 
                          xaxis_title="Time (s)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.write("---")
    st.subheader("2. Athlete Deep-Dive Selection")

    # RESTORED: Years of data and proper sorting
    swimmer_summary['Label'] = swimmer_summary.apply(
        lambda r: f"{r['Swimmer']} [{r['Status']} | {r['years_competed']} yrs data]", axis=1
    )
    swimmer_summary = swimmer_summary.sort_values('Swimmer')
    name_map = dict(zip(swimmer_summary['Label'], swimmer_summary['Swimmer']))
    
    selected_label = st.selectbox("Search Athlete Profile", options=list(name_map.keys()))
    swimmer_name = name_map[selected_label]

    @st.cache_data
    def run_heavy_analytics(working_df):
        prog = build_progression_features(working_df)
        perf = build_performance_features(working_df)
        merged = pd.merge(prog, perf, on='FINA ID')
        best = working_df.groupby('FINA ID')['Time_Sec'].min().rename('best_time').reset_index()
        countries = working_df.groupby('FINA ID')['Country'].first().reset_index()
        final_df = pd.merge(merged, best, on='FINA ID', how='inner')
        final_df = pd.merge(final_df, countries, on='FINA ID', how='left')
        return final_df

    if st.button("RUN PERFORMANCE ENGINE", use_container_width=True):
        with st.spinner("Processing KNN Models..."):
            feat_df = run_heavy_analytics(event_df)
            target = feat_df[feat_df['Swimmer'] == swimmer_name]
            
            if target.empty:
                 st.error(f"⚠️ Not enough historical data for {swimmer_name}.")
            else:
                st.session_state.update({
                    'swimmer_stats': target.iloc[0],
                    'swimmer_name': swimmer_name,
                    'event': selected_event,
                    'swimmer_history': event_df[event_df['Swimmer'] == swimmer_name],
                    'event_df': event_df,
                    'features_df': feat_df,
                    'analytics_loaded': True
                })
                st.switch_page("pages/01_progression.py")

    st.markdown("<br><br><br>", unsafe_allow_html=True) # Bottom padding