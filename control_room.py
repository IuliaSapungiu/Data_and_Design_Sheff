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
        
        /* KPI Card Custom CSS */
        .kpi-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;}
        .kpi-icon { font-size: 2rem; display: block; margin-bottom: 5px; }
        .kpi-title { font-size: 0.8rem; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .kpi-value { font-size: 1.5rem; font-weight: bold; color: white; }
        .kpi-delta { font-size: 0.8rem; margin-top: 5px; }
        .delta-red { color: #FC8181; }
        .delta-neutral { color: #A0AEC0; }
    </style>
""", unsafe_allow_html=True)

# 2. SPLASH SCREEN (Runs only on first load)
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

# 3. PORTABLE LOGO LOADER
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

# 🔥 OPTIMIZATION: Using an underscore ignores DataFrame hashing. Streamlit only hashes the string 'cache_key'.
@st.cache_data(show_spinner=False)
def run_heavy_analytics(_working_df, cache_key):
    prog = build_progression_features(_working_df)
    perf = build_performance_features(_working_df)
    merged = pd.merge(prog, perf, on='FINA ID')
    best = _working_df.groupby('FINA ID')['Time_Sec'].min().rename('best_time').reset_index()
    countries = _working_df.groupby('FINA ID')['Country'].first().reset_index()
    final_df = pd.merge(merged, best, on='FINA ID', how='inner')
    final_df = pd.merge(final_df, countries, on='FINA ID', how='left')
    return final_df

def process_and_navigate(swimmer_name, event_name, engine_df, cache_key):
    with st.spinner(f"Accelerating engine data for {swimmer_name}..."):
        features_df = run_heavy_analytics(engine_df, cache_key)
        target_data = features_df[features_df['Swimmer'] == swimmer_name]
        
        if target_data.empty:
            st.error(f"⚠️ Not enough historical data for {swimmer_name}.")
        else:
            athlete_country = engine_df[engine_df['Swimmer'] == swimmer_name]['Country'].iloc[0]
            stats_dict = target_data.iloc[0].to_dict()
            if 'country' not in stats_dict:
                stats_dict['country'] = athlete_country  
            
            st.session_state.update({
                'swimmer_stats': stats_dict,
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

    # --- 1. SET UP VISUAL LAYOUT ORDER ---
    charts_container = st.container()
    st.write("---")
    search_container = st.container()
    st.write("---")
    filters_container = st.container()
    st.write("---")
    leaderboard_container = st.container()

    # --- 2. EXECUTE FILTERS LOGIC (Visually 3rd) ---
    with filters_container:
        with st.container(border=True):
            st.write("#### 🎛️ Field Filters")
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                gender_options = sorted(df['Gender'].dropna().unique())
                selected_gender = st.selectbox("Select Gender", gender_options, index=gender_options.index('M') if 'M' in gender_options else 0)
                base_event_df = df[df['Gender'] == selected_gender]

            with c3:
                stroke_options = sorted(base_event_df['Stroke'].dropna().unique())
                selected_stroke = st.selectbox("Select Stroke", stroke_options, index=stroke_options.index('Freestyle') if 'Freestyle' in stroke_options else 0)
                base_event_df = base_event_df[base_event_df['Stroke'] == selected_stroke]

            with c4:
                distance_options = sorted(base_event_df['Distance'].dropna().unique())
                selected_distance = st.selectbox("Select Distance", distance_options, index=distance_options.index('100m') if '100m' in distance_options else 0)
                base_event_df = base_event_df[base_event_df['Distance'] == selected_distance]
                
            base_event_df['Swimmer'] = base_event_df['Swimmer'].str.strip() 
            selected_event = f"{selected_distance} {selected_stroke}"

            with c2:
                country_options = ["All Countries"] + sorted(base_event_df['Country'].dropna().unique().tolist())
                selected_country = st.selectbox("Select Country", country_options)

            st.write("##### Set Timeframe")
            min_yr = int(df['Year'].min()) if not df.empty else 2000
            max_yr = int(global_max_year)
            selected_years = st.slider(
                "Filter active years", 
                min_value=min_yr, max_value=max_yr, value=(min_yr, max_yr),
                label_visibility="collapsed"
            )

        # ENGINE DATA TOGGLE
        st.write("<br>", unsafe_allow_html=True)
        analyze_full_career = st.toggle(
            "📈 Analyze Full Career History (Recommended)", 
            value=True, 
            help="If checked, clicking an athlete will run the engine on their ENTIRE lifetime history for this event. If unchecked, it will ONLY run calculations based on the timeframe/country filters above."
        )

    # DATA PREP: GLOBAL DF (Time Filtered) & LEADERBOARD DF (Time + Country Filtered)
    global_df = base_event_df[(base_event_df['Year'] >= selected_years[0]) & (base_event_df['Year'] <= selected_years[1])]
    
    leaderboard_df = global_df.copy()
    if selected_country != "All Countries":
        leaderboard_df = leaderboard_df[leaderboard_df['Country'] == selected_country]
        
    target_engine_df = base_event_df if analyze_full_career else leaderboard_df
    
    # 🔥 GENERATE UNIQUE CACHE KEY
    if analyze_full_career:
        current_cache_key = f"full_{selected_gender}_{selected_stroke}_{selected_distance}"
    else:
        current_cache_key = f"filtered_{selected_gender}_{selected_stroke}_{selected_distance}_{selected_country}_{selected_years[0]}_{selected_years[1]}"

    # --- DATA AGGREGATION FOR LEADERBOARD & SEARCH ---
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

    # --- 3. EXECUTE CHARTS LOGIC (Visually 1st) ---
    with charts_container:
        vis_col1, vis_col2 = st.columns([1, 1], gap="large")

        with vis_col1:
            st.write(f"#### 🌍 Global Dominance: {selected_event}")
            if not global_df.empty:
                country_best = global_df.groupby('Country')['Time_Sec'].min().reset_index()
                
                mapper = {
                    "People's Republic of China": "China", 
                    "Great Britain": "United Kingdom", 
                    "United States of America": "United States",
                    "Russian Federation": "Russia",
                    "Republic of Korea": "South Korea",
                    "Islamic Republic of Iran": "Iran"
                }
                country_best['Map_Name'] = country_best['Country'].replace(mapper)

                fig_globe = px.choropleth(
                    country_best, locations="Map_Name", locationmode="country names",
                    color="Time_Sec", color_continuous_scale="Viridis_r",
                    hover_name="Country", hover_data={"Map_Name": False, "Time_Sec": ":.2f"},
                    template="plotly_dark", labels={'Time_Sec': 'Best Time (s)'}
                )
                fig_globe.update_geos(
                    projection_type="orthographic", bgcolor="rgba(0,0,0,0)", 
                    showcountries=True, countrycolor="rgba(255,255,255,0.1)",
                    showocean=False
                )
                
                fig_globe.update_layout(
                    margin=dict(l=0,r=0,t=0,b=0), 
                    height=350,
                    coloraxis_colorbar=dict(
                        title=dict(text="Seconds", font=dict(color="white", size=12)),
                        thickness=12,
                        len=0.7,
                        yanchor="middle", y=0.5,
                        xanchor="left", x=0.9,
                        tickfont=dict(color="white", size=10)
                    )
                )
                st.plotly_chart(fig_globe, use_container_width=True)
                
                top5_df = country_best.sort_values('Time_Sec').head(5).reset_index(drop=True)
                if not top5_df.empty:
                    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                    top5_html = "<div style='display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: -10px;'>"
                    for i, row in top5_df.iterrows():
                        c_name = row['Country'] if len(row['Country']) < 18 else row['Country'][:15] + '...'
                        top5_html += f"<div style='background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; color: #e2e8f0;'>{medals[i]} <b>{c_name}</b> <span style='color: #4FD1C5; font-weight: bold;'>{row['Time_Sec']:.2f}s</span></div>"
                    top5_html += "</div>"
                    st.markdown(top5_html, unsafe_allow_html=True)
                    
            else:
                st.info("No global data available for this event.")

        with vis_col2:
            st.write(f"#### 📈 Evolution of Elite: {selected_years[0]}-{selected_years[1]}")
            if not global_df.empty:
                pace_df = global_df.groupby('Year')['Time_Sec'].apply(
                    lambda x: x.nsmallest(8).mean() if len(x) >= 1 else np.nan
                ).dropna().reset_index(name='top8_avg')
                
                if not pace_df.empty:
                    fig_pace = px.line(pace_df, x='Year', y='top8_avg', markers=True, template="plotly_dark")
                    fig_pace.update_traces(
                        line_color='#00A4E4', line_width=3, 
                        marker=dict(size=8, color='white', line=dict(width=2, color='#00A4E4')),
                        hovertemplate="Year: %{x}<br>Top 8 Avg: %{y:.2f}s<extra></extra>"
                    )
                    fig_pace.update_yaxes(autorange="reversed", title="Pace (Seconds)")
                    fig_pace.update_layout(margin=dict(l=0,r=0,t=20,b=0), height=350, xaxis_title=None, hovermode="x unified")
                    st.plotly_chart(fig_pace, use_container_width=True)
                else:
                    st.info("Insufficient yearly data for the pace tracker.")
            else:
                st.info("No data available to plot pace evolution.")

    # --- 4. EXECUTE SEARCH LOGIC (Visually 2nd) ---
    with search_container:
        st.write("### 🔍 Quick Athlete Search")
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
                "**Select an athlete to instantly view profile**", 
                options=search_list, 
                index=0,
                label_visibility="collapsed"
            )

        if search_swimmer != "":
            if filter_search:
                process_and_navigate(search_swimmer, selected_event, target_engine_df, current_cache_key)
            else:
                athlete_raw = df[df['Swimmer'].str.strip() == search_swimmer].copy()
                if not athlete_raw.empty:
                    athlete_raw['Event_Full'] = athlete_raw['Distance'].astype(str) + " " + athlete_raw['Stroke']
                    global_best_event = athlete_raw['Event_Full'].mode()[0]
                    global_gender = athlete_raw['Gender'].iloc[0]
                    g_dist, g_stroke = global_best_event.split(' ', 1)
                    custom_df = df[(df['Gender'] == global_gender) & (df['Stroke'] == g_stroke) & (df['Distance'] == g_dist)]
                    custom_cache_key = f"custom_search_{global_gender}_{g_stroke}_{g_dist}"
                    process_and_navigate(search_swimmer, global_best_event, custom_df, custom_cache_key)
                else:
                    st.error("Athlete data could not be parsed.")

    # --- 5. EXECUTE LEADERBOARD LOGIC (Visually 4th) ---
    with leaderboard_container:
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
                    intensity = 1.0 - ((rank - 4) / max(1, (total_rows - 4))) if total_rows > 3 else 0.05
                    alpha = max(0.02, 0.02 + (0.08 * intensity))
                    color = f'background-color: rgba(30, 144, 255, {alpha:.2f});' 
                return [color] * len(row)
            
            styled_df = display_df.style.apply(highlight_rows, axis=1)
            
            with st.expander(f"🏆 View Full Global Leaderboard Table", expanded=False):
                st.caption("👇 **Click on any row in the table below to load their full analytical profile.**")
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
                process_and_navigate(selected_swimmer_name, selected_event, target_engine_df, current_cache_key)
                
        else:
            st.info("No data available for the current filter selection.")

    st.markdown("<br><br><br>", unsafe_allow_html=True)