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

# 1. PAGE CONFIG MUST BE ABSOLUTELY FIRST
st.set_page_config(page_title="SwimMetrics Home Page", layout="wide", initial_sidebar_state="collapsed")

# 2. INJECT CSS IMMEDIATELY TO PREVENT FLASHING (FOUC)
st.markdown("""
    <style>
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        .block-container { padding: 0rem !important; max-width: 100% !important; }
        
        .hero-wrapper {
            height: 100vh; width: 100vw;
            background: linear-gradient(135deg, #001233 0%, #002366 100%);
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 10%; color: white; font-family: 'Helvetica Neue', sans-serif;
            position: relative; box-sizing: border-box; overflow: hidden; margin: 0;
        }
        .hero-left { flex: 1.2; text-align: left; z-index: 2; }
        .hero-right { flex: 0.8; display: flex; justify-content: flex-end; z-index: 2; }
        .hero-main-title { font-size: clamp(3rem, 6vw, 5rem); font-weight: 800; line-height: 1.1; margin-bottom: 20px; }
        .hero-sub-text { color: #00A4E4; font-size: clamp(1rem, 2vw, 1.5rem); letter-spacing: 5px; text-transform: uppercase; font-weight: 300; }
        .logo-img { width: 100%; max-width: 480px; filter: drop-shadow(0 20px 50px rgba(0,0,0,0.5)); animation: float 4s ease-in-out infinite; }

        @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-20px); } 100% { transform: translateY(0px); } }

        @media (max-width: 768px) {
            .hero-wrapper { flex-direction: column; justify-content: center; text-align: center; padding: 0 5%; }
            .hero-left { margin-bottom: 2rem; flex: 0; }
            .hero-right { justify-content: center; flex: 0; }
            .logo-img { max-width: 250px; }
        }

        .scroll-hint {
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            text-align: center; font-size: 0.7rem; letter-spacing: 3px; opacity: 0.6;
            animation: bounce 2s infinite; color: white; z-index: 10;
        }
        @keyframes bounce { 0%, 20%, 50%, 80%, 100% {transform: translateY(0) translateX(-50%);} 40% {transform: translateY(-10px) translateX(-50%);} 60% {transform: translateY(-5px) translateX(-50%);} }
    </style>
""", unsafe_allow_html=True)

# 3. SPLASH SCREEN (Runs only on first load)
if 'splash_shown' not in st.session_state:
    st.markdown("""
        <style>
            .splash-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #000; z-index: 9999999; display: flex; justify-content: center; align-items: center; animation: fadeOut 1s ease-in-out 3s forwards; }
            .video-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.4; }
            .splash-title { position: relative; color: white; font-size: 6rem; font-weight: 800; letter-spacing: 2px; z-index: 10000000; animation: zoomIn 2.5s forwards; }
            @keyframes zoomIn { 0% { transform: scale(0.6); opacity: 0; } 50% { opacity: 1; } 100% { transform: scale(1.1); opacity: 1; } }
            @keyframes fadeOut { 0% { opacity: 1; visibility: visible; } 100% { opacity: 0; visibility: hidden; z-index: -100; pointer-events: none; } }
        </style>
        <div class="splash-container"><video class="video-bg" autoplay loop muted playsinline><source src="https://cdn.pixabay.com/video/2020/05/24/40062-424754162_large.mp4" type="video/mp4"></video><div class="splash-title">SwimMetrics</div></div>
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
        with open(path, 'rb') as f: return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

# 5. HERO DISPLAY
st.markdown(f"""
    <div class="hero-wrapper">
        <div class="hero-left">
            <div class="hero-sub-text">Elite Performance Analytics</div>
            <div class="hero-main-title">Precision in <br>Every Stroke</div>
        </div>
        <div class="hero-right"><img src="{get_base64_img('WHITESwimMetrics-Logo.png')}" class="logo-img"></div>
        <div class="scroll-hint">SCROLL TO ANALYZE<br>▼</div>
    </div>
""", unsafe_allow_html=True)

# --- GLOBAL ENGINE HELPER FUNCTIONS ---
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

def process_and_navigate(swimmer_name, event_name, engine_df):
    with st.spinner(f"Processing KNN Models & Engine Data for {swimmer_name}..."):
        features_df = run_heavy_analytics(engine_df)
        target_data = features_df[features_df['Swimmer'] == swimmer_name]
        
        if target_data.empty:
            st.error(f"⚠️ Not enough historical data for {swimmer_name}.")
        else:
            st.session_state.update({
                'swimmer_stats': target_data.iloc[0],
                'swimmer_name': swimmer_name,
                'event': event_name,
                'swimmer_history': engine_df[engine_df['Swimmer'] == swimmer_name],
                'event_df': engine_df, 
                'features_df': features_df,
                'analytics_loaded': True
            })
            st.switch_page("pages/01_progression.py")

# --- MAIN CONTENT ---
st.markdown("<br><br>", unsafe_allow_html=True)
spacer_left, main_col, spacer_right = st.columns([1, 8, 1])

with main_col:
    render_navbar()
    st.title("🎛️ Control Room")
    st.markdown("Use the filters below to isolate specific events, or use the Quick Search to jump straight to an athlete's profile.")

    with st.spinner("Syncing Database..."):
        df = load_and_clean_data()
        global_max_year = df['Year'].max() if not df.empty else 2025
        
    # --- 1. FIELD FILTERS ---
    with st.container(border=True):
        st.write("#### 1. Global Event Filters")
        c1, c2, c3, c4 = st.columns(4)

        # Build the BASE Event DataFrame (No country/year restrictions yet)
        with c1:
            gender_options = sorted(df['Gender'].dropna().unique())
            selected_gender = st.selectbox("Gender Focus", gender_options, index=gender_options.index('M') if 'M' in gender_options else 0)
        with c3:
            stroke_options = sorted(df[df['Gender'] == selected_gender]['Stroke'].dropna().unique())
            selected_stroke = st.selectbox("Stroke Focus", stroke_options, index=stroke_options.index('Freestyle') if 'Freestyle' in stroke_options else 0)
        with c4:
            distance_options = sorted(df[(df['Gender'] == selected_gender) & (df['Stroke'] == selected_stroke)]['Distance'].dropna().unique())
            selected_distance = st.selectbox("Distance Focus", distance_options)
            
        # BASE EVENT DATAFRAME (Entire history of the specific race)
        base_event_df = df[(df['Gender'] == selected_gender) & (df['Stroke'] == selected_stroke) & (df['Distance'] == selected_distance)].copy()
        base_event_df['Swimmer'] = base_event_df['Swimmer'].str.strip() 
        selected_event = f"{selected_distance}m {selected_stroke}"

        # Build the NARROW Leaderboard DataFrame (Restricted by Country/Year)
        with c2:
            country_options = ["All Countries"] + sorted(base_event_df['Country'].dropna().unique().tolist())
            selected_country = st.selectbox("Country Focus", country_options)
        
        st.write("##### Set Timeframe")
        min_yr = int(df['Year'].min()) if not df.empty else 2000
        max_yr = int(global_max_year)
        selected_years = st.slider("Filter active years", min_value=min_yr, max_value=max_yr, value=(min_yr, max_yr), label_visibility="collapsed")

    # Lock in the filtered leaderboard dataframe
    leaderboard_df = base_event_df.copy()
    if selected_country != "All Countries":
        leaderboard_df = leaderboard_df[leaderboard_df['Country'] == selected_country]
    leaderboard_df = leaderboard_df[(leaderboard_df['Year'] >= selected_years[0]) & (leaderboard_df['Year'] <= selected_years[1])]

    # --- 2. DYNAMIC SUMMARY GENERATION ---
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
        
        swimmer_summary['Status'] = swimmer_summary['latest_year'].apply(
            lambda y: '🟢 Active' if y >= global_max_year - 1 else '🔴 Retired/Inactive'
        )
        
        swimmer_summary['Label'] = swimmer_summary.apply(
            lambda r: f"{r['Swimmer']} [{r['Status']} | {r['years_competed']} yrs data]", axis=1
        )
        swimmer_summary = swimmer_summary.sort_values('Swimmer')
        name_map = dict(zip(swimmer_summary['Label'], swimmer_summary['Swimmer']))
    else:
        swimmer_summary = pd.DataFrame()
        name_map = {}

    # --- 3. ATHLETE DEEP-DIVE SELECTION ---
    st.write("---")
    st.subheader("🔍 2. Athlete Deep-Dive Selection")
    
    # NEW TOGGLE: Let the user choose what data to pass to the engine
    analyze_full_career = st.toggle(
        "📈 Analyze Full Career History (Recommended)", 
        value=True, 
        help="If checked, clicking an athlete will run the engine on their ENTIRE lifetime history for this event. If unchecked, it will ONLY run calculations based on the timeframe/country filters above."
    )
    
    # Determine which dataset to send to the engine based on the toggle
    target_engine_df = base_event_df if analyze_full_career else leaderboard_df

    if not swimmer_summary.empty:
        selected_label = st.selectbox("Search Athlete Profile (Filtered by selections above)", options=[""] + list(name_map.keys()), index=0)
        
        if selected_label != "":
            swimmer_name = name_map[selected_label]
            if st.button("RUN PERFORMANCE ENGINE", use_container_width=True):
                process_and_navigate(swimmer_name, selected_event, target_engine_df)
    else:
        st.info("No athletes match the current filters.")

    # --- 4. RESULTS & LEADERBOARD ---
    st.write("---")
    st.write(f"### 🏆 Global Leaderboard ({selected_country} | {selected_gender} - {selected_event})")

    if not swimmer_summary.empty:
        leaderboard = swimmer_summary.sort_values('best_time', ascending=True).reset_index(drop=True)
        best_overall = leaderboard['best_time'].iloc[0]
        leaderboard['Gap'] = leaderboard['best_time'] - best_overall
        
        # ADDED TOOLTIPS (`help=...`) to all KPIs!
        st.write("")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Athletes Found", f"{len(leaderboard):,}", 
                    help="The total number of unique swimmers currently matching your gender, country, stroke, and timeframe filters.")
        kpi2.metric("Leader (Gold Pace)", f"{best_overall:.2f}s", 
                    help="The absolute fastest time recorded within your selected filters.")
        
        if len(leaderboard) >= 8:
            finalist_cutoff = leaderboard['best_time'].iloc[7]
            kpi3.metric("Top 8 Cutoff (Finalist)", f"{finalist_cutoff:.2f}s", f"+{finalist_cutoff - best_overall:.2f}s", delta_color="inverse", 
                        help="The time required to make it into the top 8 (simulating a final event). The colored number shows the gap between 8th place and 1st place.")
        else:
            kpi3.metric("Top 8 Cutoff", "N/A", help="Not enough athletes to form a Top 8 final.")
            
        kpi4.metric("Average Gap to Leader", f"+{leaderboard['Gap'].mean():.2f}s", 
                    help="The average time difference between all filtered athletes and the current #1 Leader.")
        st.write("")
        
        leaderboard['Medal %'] = np.clip(85 - (leaderboard['Gap'] * 60), 1, 99).astype(int).astype(str) + "%"
        leaderboard['Finalist %'] = np.clip(95 - (leaderboard['Gap'] * 35), 5, 99).astype(int).astype(str) + "%"
        
        display_df = pd.DataFrame({
            'Rank': [f"{i+1}" for i in range(len(leaderboard))],
            'Athlete': leaderboard['Swimmer'],
            'Age': leaderboard['latest_age'].apply(lambda x: str(int(x)) if pd.notna(x) else "N/A"),
            'Country': leaderboard['country'],
            'Latest Time': leaderboard.apply(lambda row: f"{row['latest_time']:.2f}s ({int(row['latest_year'])})", axis=1),
            'Best Time': leaderboard.apply(lambda row: f"{row['best_time']:.2f}s ({int(row['best_year'])})", axis=1),
            'Medal %': leaderboard['Medal %'],
            'Finalist %': leaderboard['Finalist %'],
            'Gap': leaderboard['Gap'].apply(lambda x: f"+{x:.2f}s")
        })
        
        def highlight_rows(row):
            rank = int(row['Rank'])
            total_rows = len(display_df)
            if rank == 1: color = 'background-color: rgba(255, 215, 0, 0.15);' 
            elif rank == 2: color = 'background-color: rgba(192, 192, 192, 0.15);' 
            elif rank == 3: color = 'background-color: rgba(205, 127, 50, 0.15);' 
            else:
                alpha = max(0.02, 0.02 + (0.08 * (1.0 - ((rank - 4) / max(1, (total_rows - 4)))))) if total_rows > 3 else 0.05
                color = f'background-color: rgba(30, 144, 255, {alpha:.2f});' 
            return [color] * len(row)
        
        styled_df = display_df.style.apply(highlight_rows, axis=1)
        
        st.caption("👇 **Click on any row in the table below to automatically load their full analytical profile.**")
        
        # REDUCED HEIGHT to 400px to prevent the user getting "trapped" while scrolling
        selection_event = st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            height=400, 
            on_select="rerun",
            selection_mode="single-row"
        )
        
        if len(selection_event.selection.rows) > 0:
            selected_row_index = selection_event.selection.rows[0]
            selected_swimmer_name = display_df.iloc[selected_row_index]['Athlete']
            # Target engine uses the toggle logic too!
            process_and_navigate(selected_swimmer_name, selected_event, target_engine_df)

    st.markdown("<br><br><br>", unsafe_allow_html=True)