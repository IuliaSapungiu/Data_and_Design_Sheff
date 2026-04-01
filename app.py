import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data.data_processor import load_and_clean_data
from features.progression import build_progression_features
from features.performance import build_performance_features

st.set_page_config(page_title="SWIMETRICS Analytics", layout="wide", initial_sidebar_state="expanded")

# --- HEADER ---
st.title("🏊‍♂️ SWIMETRICS: Analytics Control Room")
st.markdown("Use the filters below to isolate specific events, or use the Quick Search to jump straight to an athlete's profile.")

with st.spinner("Loading master dataset..."):
    df = load_and_clean_data()

# --- 1. CONTROL PANEL (Grouped in a stylized container) ---
with st.container(border=True):
    st.write("#### 🎛️ Field Filters")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        gender_options = sorted(df['Gender'].dropna().unique())
        selected_gender = st.selectbox("Select Gender", gender_options, index=gender_options.index('M') if 'M' in gender_options else 0)
        filtered_df = df[df['Gender'] == selected_gender]

    with c2:
        country_options = ["All Countries"] + sorted(filtered_df['Country'].dropna().unique().tolist())
        selected_country = st.selectbox("Select Country", country_options)
        if selected_country != "All Countries":
            filtered_df = filtered_df[filtered_df['Country'] == selected_country]

    with c3:
        stroke_options = sorted(filtered_df['Stroke'].dropna().unique())
        selected_stroke = st.selectbox("Select Stroke", stroke_options)
        filtered_df = filtered_df[filtered_df['Stroke'] == selected_stroke]

    with c4:
        distance_options = sorted(filtered_df['Distance'].dropna().unique())
        selected_distance = st.selectbox("Select Distance", distance_options)
        filtered_df = filtered_df[filtered_df['Distance'] == selected_distance]

    st.write("##### Set Timeframe")
    min_yr = int(df['Year'].min()) if not df.empty else 2000
    max_yr = int(df['Year'].max()) if not df.empty else 2025
    selected_years = st.slider(
        "Filter active years", 
        min_value=min_yr, max_value=max_yr, value=(min_yr, max_yr),
        label_visibility="collapsed"
    )

# Apply year filter to the working dataset
filtered_df = filtered_df[(filtered_df['Year'] >= selected_years[0]) & (filtered_df['Year'] <= selected_years[1])]
selected_event = f"{selected_distance} {selected_stroke}"
filtered_df['Swimmer'] = filtered_df['Swimmer'].str.strip() 

# --- GLOBAL ENGINE HELPER FUNCTION ---
@st.cache_data
def generate_all_features(working_df):
    prog_df = build_progression_features(working_df)
    perf_df = build_performance_features(working_df)
    return pd.merge(prog_df, perf_df, on='FINA ID')

def process_and_navigate(swimmer_name, event_name, full_filtered_df):
    """Generates features for the selected swimmer and instantly switches pages."""
    with st.spinner(f"Crunching engine data for {swimmer_name}..."):
        features_df = generate_all_features(full_filtered_df)
        target_data = features_df[features_df['Swimmer'] == swimmer_name]
        
        if target_data.empty:
            st.error(f"⚠️ Not enough historical data for {swimmer_name}.")
        else:
            st.session_state['swimmer_stats'] = target_data.iloc[0]
            st.session_state['swimmer_name'] = swimmer_name
            st.session_state['event'] = event_name
            st.session_state['swimmer_history'] = full_filtered_df[full_filtered_df['Swimmer'] == swimmer_name]
            st.session_state['event_df'] = full_filtered_df
            st.session_state['features_df'] = features_df
            st.switch_page("pages/01_progression.py")

# --- DATA AGGREGATION ---
if not filtered_df.empty:
    current_year = filtered_df['Year'].max()

    idx_best = filtered_df.groupby('Swimmer')['Time_Sec'].idxmin()
    best_df = filtered_df.loc[idx_best, ['Swimmer', 'Time_Sec', 'Year', 'Country']]
    best_df.columns = ['Swimmer', 'best_time', 'best_year', 'country']

    idx_latest = filtered_df.groupby('Swimmer')['Year'].idxmax()
    cols_to_extract = ['Swimmer', 'Time_Sec', 'Year']
    if 'Age' in filtered_df.columns:
        cols_to_extract.append('Age')
        latest_df = filtered_df.loc[idx_latest, cols_to_extract]
        latest_df.columns = ['Swimmer', 'latest_time', 'latest_year', 'latest_age']
    else:
        latest_df = filtered_df.loc[idx_latest, cols_to_extract]
        latest_df.columns = ['Swimmer', 'latest_time', 'latest_year']
        latest_df['latest_age'] = np.nan 

    years_df = filtered_df.groupby('Swimmer')['Year'].nunique().reset_index(name='years_competed')
    swimmer_summary = best_df.merge(latest_df, on='Swimmer').merge(years_df, on='Swimmer')
    swimmer_summary['Status'] = swimmer_summary['latest_year'].apply(
        lambda y: '🟢 Active' if y >= selected_years[1] - 1 else '🔴 Retired/Inactive'
    )
else:
    swimmer_summary = pd.DataFrame()


# --- 2. QUICK SEARCH SECTION ---
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
        process_and_navigate(search_swimmer, selected_event, filtered_df)
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


# --- 3. RESULTS & LEADERBOARD ---
st.write("---")
st.write(f"### 🏆 Global Leaderboard ({selected_country} | {selected_gender} - {selected_event})")

if not swimmer_summary.empty:
    
    leaderboard = swimmer_summary.sort_values('best_time', ascending=True).reset_index(drop=True)
    best_overall = leaderboard['best_time'].iloc[0]
    leaderboard['Gap'] = leaderboard['best_time'] - best_overall
    
    # NEW: KPI Summary Cards above the table
    st.write("")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Athletes Found", f"{len(leaderboard):,}")
    kpi2.metric("Leader (Gold Pace)", f"{best_overall:.2f}s")
    
    # Calculate what it takes to be Top 8 (Finalist)
    if len(leaderboard) >= 8:
        finalist_cutoff = leaderboard['best_time'].iloc[7]
        kpi3.metric("Top 8 Cutoff (Finalist)", f"{finalist_cutoff:.2f}s", f"+{finalist_cutoff - best_overall:.2f}s", delta_color="inverse")
    else:
        kpi3.metric("Top 8 Cutoff", "N/A")
        
    kpi4.metric("Average Gap to Leader", f"+{leaderboard['Gap'].mean():.2f}s")
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
    
    # UPGRADED: Softer, elegant coloring that preserves readability
    def highlight_rows(row):
        rank = int(row['Rank'])
        total_rows = len(display_df)
        
        # Lowered opacity significantly (e.g. 0.15 instead of 0.3) for readability
        if rank == 1:
            color = 'background-color: rgba(255, 215, 0, 0.15);' # Soft Gold
        elif rank == 2:
            color = 'background-color: rgba(192, 192, 192, 0.15);' # Soft Silver
        elif rank == 3:
            color = 'background-color: rgba(205, 127, 50, 0.15);' # Soft Bronze
        else:
            if total_rows > 3:
                intensity = 1.0 - ((rank - 4) / max(1, (total_rows - 4)))
                alpha = max(0.02, 0.02 + (0.08 * intensity)) # Very subtle blue fade
            else:
                alpha = 0.05
            color = f'background-color: rgba(30, 144, 255, {alpha:.2f});' 
            
        return [color] * len(row)
    
    styled_df = display_df.style.apply(highlight_rows, axis=1)
    
    st.caption("👇 **Click on any row in the table below to load their full analytical profile.**")
    
    selection_event = st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True,
        height=600, 
        on_select="rerun",
        selection_mode="single-row"
    )
    
    if len(selection_event.selection.rows) > 0:
        selected_row_index = selection_event.selection.rows[0]
        selected_swimmer_name = display_df.iloc[selected_row_index]['Athlete']
        process_and_navigate(selected_swimmer_name, selected_event, filtered_df)
        
else:
    if not filtered_df.empty:
        st.info(f"No swimmers found for {selected_event} in {selected_country} between {selected_years[0]}-{selected_years[1]}.")
    else:
        st.info("No data available for the current filter selection.")