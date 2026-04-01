import streamlit as st
import pandas as pd
import plotly.express as px
from data.data_processor import load_and_clean_data
from features.progression import build_progression_features
from features.performance import build_performance_features

st.set_page_config(page_title="Swimming Analytics Engine", layout="wide")
st.title("🏊‍♂️ Analytics Control Room")

with st.spinner("Loading master dataset..."):
    df = load_and_clean_data()

valid_events = ['50m Freestyle', '100m Freestyle', '200m Freestyle']
if 'Stroke' in df.columns:
    df = df[df['Stroke'] == 'Freestyle']
df = df[df['Event'].isin(valid_events)]

# --- 1. SELECT THE FIELD ---
st.write("### 1. Select the Field")
col1, col2 = st.columns(2)

with col1:
    selected_gender = st.selectbox("Select Gender", ['M', 'F'])
    gender_df = df[df['Gender'] == selected_gender]

with col2:
    selected_event = st.selectbox("Select Event", valid_events)
    event_df = gender_df[gender_df['Event'] == selected_event]
    
# Clean up swimmer names just in case there are weird spaces in the CSV
event_df['Swimmer'] = event_df['Swimmer'].str.strip() 

# --- 2. SMART DATA PROFILING & LEADERBOARD ---
# Figure out the most recent year in the whole dataset to define who is "Active"
current_year = event_df['Year'].max()

# Build a summary of every swimmer to power our smart dropdown and leaderboard
swimmer_summary = event_df.groupby('Swimmer').agg(
    latest_year=('Year', 'max'),
    years_competed=('Year', 'nunique'),
    best_time=('Time_Sec', 'min')
).reset_index()

# If they competed in the last 2 years of the dataset, we call them Active
swimmer_summary['Status'] = swimmer_summary['latest_year'].apply(
    lambda y: '🟢 Active' if y >= current_year - 1 else '🔴 Retired/Inactive'
)

st.write("---")
st.write(f"### 🏆 Top 10 Active Contenders ({selected_gender} - {selected_event})")
st.write("Need someone to analyze? Here are the fastest active swimmers to choose from.")

# Get top 10 active swimmers
top_10_active = swimmer_summary[swimmer_summary['Status'] == '🟢 Active'].nsmallest(10, 'best_time')

# Build a fast, clean horizontal bar chart
if len(top_10_active) > 0:
    # Sort descending so the fastest (smallest time) is at the top of the chart
    top_10_active = top_10_active.sort_values('best_time', ascending=False) 
    
    fig_leaderboard = px.bar(
        top_10_active, 
        x='best_time', 
        y='Swimmer', 
        orientation='h',
        text='best_time',
        color_discrete_sequence=['#1E90FF'] # Nice Olympic Blue
    )
    
    # Format the numbers and zoom in the X-axis so we can actually see the gaps
    fig_leaderboard.update_traces(texttemplate='%{text:.2f}s', textposition='inside')
    
    min_time = top_10_active['best_time'].min() - 0.5
    max_time = top_10_active['best_time'].max() + 0.5
    
    fig_leaderboard.update_layout(
        xaxis_title="Best Time (Seconds)",
        yaxis_title="",
        xaxis=dict(range=[min_time, max_time]), # Zooms the chart in to highlight differences
        height=400,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_leaderboard, use_container_width=True)
else:
    st.info("No active swimmers found for this event.")

st.write("---")

# --- 3. TARGET ATHLETE SELECTION ---
st.write("### 2. Target Athlete Selection")

# Create a fancy label for the dropdown
def format_dropdown(row):
    return f"{row['Swimmer']} [{row['Status']} | {row['years_competed']} yrs data]"

swimmer_summary['Dropdown_Label'] = swimmer_summary.apply(format_dropdown, axis=1)

# Sort the dropdown alphabetically but keep the mapping to the actual name
swimmer_summary = swimmer_summary.sort_values('Swimmer')
name_mapping = dict(zip(swimmer_summary['Dropdown_Label'], swimmer_summary['Swimmer']))

selected_label = st.selectbox(
    "Search and select an athlete to generate their predictive profile:", 
    options=list(name_mapping.keys())
)

# Extract the actual real name to pass to the analytics engine
swimmer_name = name_mapping[selected_label]

st.write("---")

@st.cache_data
def generate_all_features(working_df):
    prog_df = build_progression_features(working_df)
    perf_df = build_performance_features(working_df)
    return pd.merge(prog_df, perf_df, on='FINA ID')

# --- 4. RUN ENGINE ---
if st.button("🚀 Process Analytics & Load Pages"):
    with st.spinner("Calculating field statistics..."):
        features_df = generate_all_features(event_df)
        
        target_data = features_df[features_df['Swimmer'] == swimmer_name]
        
        # --- NEW GUARDRAIL APPLIED HERE ---
        if target_data.empty:
            st.error(f"⚠️ Not enough historical data to run Progression Analytics for {swimmer_name} in the {selected_event}. (The algorithm requires multiple seasons of data to calculate a trendline).")
        else:
            # Save to Session State ONLY if data exists
            st.session_state['swimmer_stats'] = target_data.iloc[0]
            st.session_state['swimmer_name'] = swimmer_name
            st.session_state['event'] = selected_event
            st.session_state['swimmer_history'] = event_df[event_df['Swimmer'] == swimmer_name]
            st.session_state['event_df'] = event_df
            
            st.success("✅ Analytics loaded! Click the pages in the sidebar to view the dashboards.")