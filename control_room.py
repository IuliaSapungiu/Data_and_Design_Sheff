import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import base64
import os
from data.data_processor import load_and_clean_data
from features.progression import build_progression_features
from features.performance import build_performance_features
from shared_ui import render_navbar

# 1. INJECT CSS IMMEDIATELY TO PREVENT FLASHING (FOUC)
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
        
        /* Custom KPI Cards */
        .kpi-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
            height: 100%;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 164, 228, 0.2);
            border-color: rgba(0, 164, 228, 0.5);
        }
        .kpi-icon {
            font-size: 1.8rem;
            margin-bottom: 8px;
            display: block;
        }
        .kpi-title {
            color: #a0aec0;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
        }
        .kpi-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: white;
            margin-bottom: 8px;
            letter-spacing: -1px;
        }
        .kpi-delta {
            font-size: 0.85rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            display: inline-block;
        }
        .delta-red { color: #FC8181; background: rgba(252, 129, 129, 0.15); }
        .delta-neutral { color: #A0AEC0; background: rgba(160, 174, 192, 0.15); }
    </style>
""", unsafe_allow_html=True)

# 2. SPLASH SCREEN (Runs only on first load)
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

# 3. PORTABLE LOGO LOADER
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

# 4. HERO DISPLAY
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

# 5. MAIN CONTENT
st.markdown("<br><br>", unsafe_allow_html=True)
spacer_left, main_col, spacer_right = st.columns([1, 8, 1])

with main_col:
    render_navbar()
    
    with st.spinner("Loading master dataset..."):
        df = load_and_clean_data()

    # --- ADVANCED LOGIC INTEGRATION ---
    with st.container(border=True):
        st.write("#### 🎛️ Field Filters")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            gender_options = sorted(df['Gender'].dropna().unique())
            selected_gender = st.selectbox("Select Gender", gender_options, index=gender_options.index('M') if 'M' in gender_options else 0)
            global_df = df[df['Gender'] == selected_gender]

        with c3:
            # We filter Stroke & Distance before Country so the Global Dataset is complete
            stroke_options = sorted(global_df['Stroke'].dropna().unique())
            selected_stroke = st.selectbox("Select Stroke", stroke_options)
            global_df = global_df[global_df['Stroke'] == selected_stroke]

        with c4:
            distance_options = sorted(global_df['Distance'].dropna().unique())
            selected_distance = st.selectbox("Select Distance", distance_options)
            global_df = global_df[global_df['Distance'] == selected_distance]

        with c2:
            # The country select box now only affects the visible leaderboard
            country_options = ["All Countries"] + sorted(global_df['Country'].dropna().unique().tolist())
            selected_country = st.selectbox("Select Country", country_options)

        st.write("##### Set Timeframe")
        min_yr = int(df['Year'].min()) if not df.empty else 2000
        max_yr = int(df['Year'].max()) if not df.empty else 2025
        selected_years = st.slider(
            "Filter active years", 
            min_value=min_yr, max_value=max_yr, value=(min_yr, max_yr),
            label_visibility="collapsed"
        )

    # 1. PREPARE THE GLOBAL ENGINE DATA (Whole world for this event)
    global_df = global_df[(global_df['Year'] >= selected_years[0]) & (global_df['Year'] <= selected_years[1])]
    selected_event = f"{selected_distance} {selected_stroke}"
    global_df['Swimmer'] = global_df['Swimmer'].str.strip() 

    # 2. PREPARE THE LOCAL LEADERBOARD DATA (Just the selected country)
    if selected_country != "All Countries":
        leaderboard_df = global_df[global_df['Country'] == selected_country].copy()
    else:
        leaderboard_df = global_df.copy()

    # --- GLOBAL ENGINE HELPER FUNCTION ---
    @st.cache_data
    def generate_all_features(working_df):
        prog_df = build_progression_features(working_df)
        perf_df = build_performance_features(working_df)
        return pd.merge(prog_df, perf_df, on='FINA ID')

    def process_and_navigate(swimmer_name, event_name, full_filtered_df):
        # By passing global_df into this function, the AI processes the whole world!
        with st.spinner(f"Crunching global engine data for {swimmer_name}..."):
            features_df = generate_all_features(full_filtered_df)
            target_data = features_df[features_df['Swimmer'] == swimmer_name]
            
            if target_data.empty:
                st.error(f"⚠️ Not enough historical data for {swimmer_name}.")
            else:
                athlete_country = full_filtered_df[full_filtered_df['Swimmer'] == swimmer_name]['Country'].iloc[0]
                stats_dict = target_data.iloc[0].to_dict()
                stats_dict['country'] = athlete_country  
                
                st.session_state['swimmer_stats'] = stats_dict
                st.session_state['swimmer_name'] = swimmer_name
                st.session_state['event'] = event_name
                st.session_state['swimmer_history'] = full_filtered_df[full_filtered_df['Swimmer'] == swimmer_name]
                st.session_state['event_df'] = full_filtered_df
                st.session_state['features_df'] = features_df
                st.session_state['analytics_loaded'] = True 
                st.switch_page("pages/01_progression.py")

    # --- DATA AGGREGATION FOR LEADERBOARD ---
    if not leaderboard_df.empty:
        idx_best = leaderboard_df.groupby('Swimmer')['Time_Sec'].idxmin()
        best_df = leaderboard_df.loc[idx_best, ['Swimmer', 'Time_Sec', 'Year', 'Country']]
        best_df.columns = ['Swimmer', 'best_time', 'best_year', 'country']

        idx_latest = leaderboard_df.groupby('Swimmer')['Year'].idxmax()
        cols_to_extract = ['Swimmer', 'Time_Sec', 'Year']
        if 'Age' in leaderboard_df.columns:
            cols_to_extract.append('Age')
            latest_df = leaderboard_df.loc[idx_latest, cols_to_extract]
            latest_df.columns = ['Swimmer', 'latest_time', 'latest_year', 'latest_age']
        else:
            latest_df = leaderboard_df.loc[idx_latest, cols_to_extract]
            latest_df.columns = ['Swimmer', 'latest_time', 'latest_year']
            latest_df['latest_age'] = np.nan 

        years_df = leaderboard_df.groupby('Swimmer')['Year'].nunique().reset_index(name='years_competed')
        swimmer_summary = best_df.merge(latest_df, on='Swimmer').merge(years_df, on='Swimmer')
    else:
        swimmer_summary = pd.DataFrame()

    # --- QUICK SEARCH SECTION ---
    st.write("---")
    sc1, sc2 = st.columns([3, 1], vertical_alignment="bottom")

    with sc2:
        filter_search = st.toggle("Limit search to active filters", value=False)

    with sc1:
        if filter_search:
            base_list = swimmer_summary['Swimmer'].tolist() if not swimmer_summary.empty else []
        else:
            base_list = df['Swimmer'].dropna().str.strip().unique().tolist()

        search_list = [""] + sorted(list(set(base_list)))
        search_swimmer = st.selectbox(
            "🔍 **Quick Athlete Search (Select to instantly view profile)**", 
            options=search_list, 
            index=0
        )

    if search_swimmer != "":
        if filter_search:
            # We now pass global_df so the AI engine gets world data
            process_and_navigate(search_swimmer, selected_event, global_df)
        else:
            athlete_raw = df[df['Swimmer'].str.strip() == search_swimmer].copy()
            if not athlete_raw.empty:
                athlete_raw['Event_Full'] = athlete_raw['Distance'].astype(str) + " " + athlete_raw['Stroke']
                global_best_event = athlete_raw['Event_Full'].mode()[0]
                global_gender = athlete_raw['Gender'].iloc[0]
                g_dist, g_stroke = global_best_event.split(' ', 1)
                custom_df = df[(df['Gender'] == global_gender) & (df['Stroke'] == g_stroke) & (df['Distance'] == g_dist)]
                process_and_navigate(search_swimmer, global_best_event, custom_df)
            else:
                st.error("Athlete data could not be parsed.")

    # --- RESULTS & LEADERBOARD ---
    st.write("---")
    st.write(f"### 🏆 Global Leaderboard ({selected_country} | {selected_gender} - {selected_event})")

    if not swimmer_summary.empty:
        leaderboard = swimmer_summary.sort_values('best_time', ascending=True).reset_index(drop=True)
        best_overall = leaderboard['best_time'].iloc[0]
        leaderboard['Gap'] = leaderboard['best_time'] - best_overall
        
        st.write("<br>", unsafe_allow_html=True)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f'<div class="kpi-card"><span class="kpi-icon">👥</span><div class="kpi-title">Athletes Found</div><div class="kpi-value">{len(leaderboard):,}</div></div>', unsafe_allow_html=True)

        with kpi2:
            st.markdown(f'<div class="kpi-card"><span class="kpi-icon">🥇</span><div class="kpi-title">Leader (Gold Pace)</div><div class="kpi-value">{best_overall:.2f}s</div></div>', unsafe_allow_html=True)

        with kpi3:
            if len(leaderboard) >= 8:
                finalist_cutoff = leaderboard['best_time'].iloc[7]
                gap_val = finalist_cutoff - best_overall
                delta_html = f'<div class="kpi-delta delta-red">↑ +{gap_val:.2f}s</div>'
                val_text = f"{finalist_cutoff:.2f}s"
            else:
                delta_html = ""
                val_text = "N/A"
            st.markdown(f'<div class="kpi-card"><span class="kpi-icon">🏁</span><div class="kpi-title">Top 8 Cutoff (Finalist)</div><div class="kpi-value">{val_text}</div>{delta_html}</div>', unsafe_allow_html=True)

        with kpi4:
            avg_gap = leaderboard['Gap'].mean()
            st.markdown(f'<div class="kpi-card"><span class="kpi-icon">⏱️</span><div class="kpi-title">Average Gap to Leader</div><div class="kpi-value">+{avg_gap:.2f}s</div><div class="kpi-delta delta-neutral">Dataset Average</div></div>', unsafe_allow_html=True)
            
        st.write("<br>", unsafe_allow_html=True)
        
        display_df = pd.DataFrame({
            'Rank': [f"{i+1}" for i in range(len(leaderboard))],
            'Athlete': leaderboard['Swimmer'],
            'Age': leaderboard['latest_age'].apply(lambda x: str(int(x)) if pd.notna(x) else "N/A"),
            'Country': leaderboard['country'],
            'Latest Time': leaderboard.apply(lambda row: f"{row['latest_time']:.2f}s ({int(row['latest_year'])})", axis=1),
            'Best Time': leaderboard.apply(lambda row: f"{row['best_time']:.2f}s ({int(row['best_year'])})", axis=1),
            'Gap': leaderboard['Gap'].apply(lambda x: f"+{x:.2f}s")
        })
        
        def highlight_rows(row):
            rank = int(row['Rank'])
            total_rows = len(display_df)
            if rank == 1: color = 'background-color: rgba(255, 215, 0, 0.15);' 
            elif rank == 2: color = 'background-color: rgba(192, 192, 192, 0.15);' 
            elif rank == 3: color = 'background-color: rgba(205, 127, 50, 0.15);' 
            else:
                intensity = 1.0 - ((rank - 4) / max(1, (total_rows - 4))) if total_rows > 3 else 0.05
                alpha = max(0.02, 0.02 + (0.08 * intensity))
                color = f'background-color: rgba(30, 144, 255, {alpha:.2f});' 
            return [color] * len(row)
        
        styled_df = display_df.style.apply(highlight_rows, axis=1)
        st.caption("👇 **Click on any row in the table below to load their full analytical profile.**")
        selection_event = st.dataframe(styled_df, width="stretch", hide_index=True, height=600, on_select="rerun", selection_mode="single-row")
        
        if len(selection_event.selection.rows) > 0:
            selected_row_index = selection_event.selection.rows[0]
            selected_swimmer_name = display_df.iloc[selected_row_index]['Athlete']
            
            # CRITICAL FIX: Pass global_df so the AI has the whole world to compare against
            process_and_navigate(selected_swimmer_name, selected_event, global_df)
            
    else:
        st.info("No data available for the current filter selection.")

st.markdown("<br><br><br>", unsafe_allow_html=True)