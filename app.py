import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data.data_processor import load_and_clean_data
from features.progression import build_progression_features
from features.performance import build_performance_features

st.set_page_config(page_title="Swimming Analytics Engine", layout="wide")
st.title("🏊‍♂️ Analytics Control Room")

with st.spinner("Loading master dataset..."):
    df = load_and_clean_data()

# --- 1. SELECT THE FIELD (FILTERS & TIMEFRAME) ---
st.write("### 1. Select the Field")
c1, c2, c3, c4 = st.columns(4)

with c1:
    # 1. Gender Filter (Default to 'M')
    gender_options = sorted(df['Gender'].dropna().unique())
    selected_gender = st.selectbox("Select Gender", gender_options, index=gender_options.index('M') if 'M' in gender_options else 0)
    filtered_df = df[df['Gender'] == selected_gender]

with c2:
    # 2. Country Filter (Includes "All Countries" option)
    country_options = ["All Countries"] + sorted(filtered_df['Country'].dropna().unique().tolist())
    selected_country = st.selectbox("Select Country", country_options)
    if selected_country != "All Countries":
        filtered_df = filtered_df[filtered_df['Country'] == selected_country]

with c3:
    # 3. Stroke Filter
    stroke_options = sorted(filtered_df['Stroke'].dropna().unique())
    selected_stroke = st.selectbox("Select Stroke", stroke_options)
    filtered_df = filtered_df[filtered_df['Stroke'] == selected_stroke]

with c4:
    # 4. Distance Filter
    distance_options = sorted(filtered_df['Distance'].dropna().unique())
    selected_distance = st.selectbox("Select Distance", distance_options)
    filtered_df = filtered_df[filtered_df['Distance'] == selected_distance]

# 5. Year Range Slider
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

# Define the specific event string for labels/titles
selected_event = f"{selected_distance} {selected_stroke}"

# Clean up swimmer names
filtered_df['Swimmer'] = filtered_df['Swimmer'].str.strip() 

# --- 2. SMART DATA PROFILING & LEADERBOARD ---
st.write("---")
st.write(f"### 🏆 Athlete Performance Analysis ({selected_country} | {selected_gender} - {selected_event})")

if not filtered_df.empty:
    current_year = filtered_df['Year'].max()

    # Highly optimized vectorised grouping to extract Best and Latest stats
    idx_best = filtered_df.groupby('Swimmer')['Time_Sec'].idxmin()
    best_df = filtered_df.loc[idx_best, ['Swimmer', 'Time_Sec', 'Year', 'Country']]
    best_df.columns = ['Swimmer', 'best_time', 'best_year', 'country']

    # Extract Latest Time, Year, AND Age
    idx_latest = filtered_df.groupby('Swimmer')['Year'].idxmax()
    
    # Safely pull Age if it exists in the raw data
    cols_to_extract = ['Swimmer', 'Time_Sec', 'Year']
    if 'Age' in filtered_df.columns:
        cols_to_extract.append('Age')
        latest_df = filtered_df.loc[idx_latest, cols_to_extract]
        latest_df.columns = ['Swimmer', 'latest_time', 'latest_year', 'latest_age']
    else:
        latest_df = filtered_df.loc[idx_latest, cols_to_extract]
        latest_df.columns = ['Swimmer', 'latest_time', 'latest_year']
        latest_df['latest_age'] = np.nan # Fallback if Age column is totally missing

    years_df = filtered_df.groupby('Swimmer')['Year'].nunique().reset_index(name='years_competed')

    # Merge them all together
    swimmer_summary = best_df.merge(latest_df, on='Swimmer').merge(years_df, on='Swimmer')

    # Status relies on the upper bound of the slider
    swimmer_summary['Status'] = swimmer_summary['latest_year'].apply(
        lambda y: '🟢 Active' if y >= selected_years[1] - 1 else '🔴 Retired/Inactive'
    )

    # Isolate the Top 10 Contenders based on BEST TIME
    top_swimmers = swimmer_summary.nsmallest(10, 'best_time')

    if not top_swimmers.empty:
        with st.spinner("Crunching models for the leaderboard..."):
            
            leaderboard = top_swimmers.sort_values('best_time', ascending=True).reset_index(drop=True)
            
            # Calculate the Gap from Rank 1 (Based on Best Time)
            best_overall = leaderboard['best_time'].iloc[0]
            leaderboard['Gap'] = leaderboard['best_time'] - best_overall
            
            # Heuristic Probabilities based on Current Gap
            leaderboard['Medal %'] = np.clip(85 - (leaderboard['Gap'] * 60), 1, 99).astype(int).astype(str) + "%"
            leaderboard['Finalist %'] = np.clip(95 - (leaderboard['Gap'] * 35), 5, 99).astype(int).astype(str) + "%"
            
            # Format the Final DataFrame for UI - Now including Age
            display_df = pd.DataFrame({
                'Rank': [f"Rank {i+1}" for i in range(len(leaderboard))],
                'Athlete': leaderboard['Swimmer'],
                'Age': leaderboard['latest_age'].apply(lambda x: str(int(x)) if pd.notna(x) else "N/A"),
                'Country': leaderboard['country'],
                'Latest Time': leaderboard.apply(lambda row: f"{row['latest_time']:.2f}s ({int(row['latest_year'])})", axis=1),
                'Best Time': leaderboard.apply(lambda row: f"{row['best_time']:.2f}s ({int(row['best_year'])})", axis=1),
                'Medal %': leaderboard['Medal %'],
                'Finalist %': leaderboard['Finalist %'],
                'Gap': leaderboard['Gap'].apply(lambda x: f"+{x:.2f}s")
            })
            
            # Apply Pandas Styling (Rank-based Podium & Gradient)
            def highlight_rows(row):
                rank = int(row['Rank'].replace('Rank ', ''))
                total_rows = len(display_df)
                
                if rank == 1:
                    color = 'background-color: rgba(255, 215, 0, 0.3); color: white;' # Gold
                elif rank == 2:
                    color = 'background-color: rgba(192, 192, 192, 0.3); color: white;' # Silver
                elif rank == 3:
                    color = 'background-color: rgba(205, 127, 50, 0.3); color: white;' # Bronze
                else:
                    if total_rows > 3:
                        intensity = 1.0 - ((rank - 4) / max(1, (total_rows - 4)))
                        alpha = 0.1 + (0.3 * intensity)
                    else:
                        alpha = 0.2
                    color = f'background-color: rgba(30, 144, 255, {alpha:.2f}); color: white;' # Blue Gradient
                    
                return [color] * len(row)
            
            # Apply color style ONLY
            styled_df = display_df.style.apply(highlight_rows, axis=1)
            
            # Render the styled dataframe
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Update swimmer_summary to ONLY include the Top 10 for the dropdown below
            swimmer_summary = top_swimmers
    else:
        st.info(f"No swimmers found for {selected_event} in {selected_country} between {selected_years[0]}-{selected_years[1]}.")
        swimmer_summary = pd.DataFrame() # Clear summary to prevent selection errors below
else:
    st.info("No data available for the current filter selection.")
    swimmer_summary = pd.DataFrame()

st.write("---")

# --- 3. TARGET ATHLETE SELECTION ---
st.write("### 2. Target Athlete Selection")

if not swimmer_summary.empty:
    def format_dropdown(row):
        return f"{row['Swimmer']} [{row['Status']} | {row['years_competed']} yrs data]"

    swimmer_summary['Dropdown_Label'] = swimmer_summary.apply(format_dropdown, axis=1)
    swimmer_summary = swimmer_summary.sort_values('Swimmer')
    name_mapping = dict(zip(swimmer_summary['Dropdown_Label'], swimmer_summary['Swimmer']))

    selected_label = st.selectbox(
        "Search and select an athlete to generate their predictive profile:", 
        options=list(name_mapping.keys())
    )
    swimmer_name = name_mapping[selected_label]
else:
    st.warning("No athletes available for the current filter selection.")
    swimmer_name = None

st.write("---")

# --- 4. RUN ENGINE ---
@st.cache_data
def generate_all_features(working_df):
    prog_df = build_progression_features(working_df)
    perf_df = build_performance_features(working_df)
    return pd.merge(prog_df, perf_df, on='FINA ID')

if st.button("🚀 Process Analytics & Load Pages") and swimmer_name:
    with st.spinner("Calculating field statistics..."):
        features_df = generate_all_features(filtered_df)
        target_data = features_df[features_df['Swimmer'] == swimmer_name]
        
        if target_data.empty:
            st.error(f"⚠️ Not enough historical data for {swimmer_name} in the {selected_event}.")
        else:
            st.session_state['swimmer_stats'] = target_data.iloc[0]
            st.session_state['swimmer_name'] = swimmer_name
            st.session_state['event'] = selected_event
            st.session_state['swimmer_history'] = filtered_df[filtered_df['Swimmer'] == swimmer_name]
            st.session_state['event_df'] = filtered_df
            st.success("✅ Analytics loaded! Switch pages in the sidebar.")