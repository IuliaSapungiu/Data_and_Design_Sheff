import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import Holt
from shared_ui import render_navbar

# 1. Setup and Navbar
st.set_page_config(page_title="Progression Analytics", layout="wide")
render_navbar()

# 2. Data Safety Check
if 'swimmer_stats' not in st.session_state:
    st.warning("Please go back to the Control Room and click 'Process Analytics' first.")
    st.stop()

stats = st.session_state['swimmer_stats']
history = st.session_state['swimmer_history'].copy()
event_df = st.session_state['event_df'].copy() # Need the full global data for context comparisons
name = st.session_state['swimmer_name']
event = st.session_state['event']
athlete_country = stats.get('country', 'Unknown')

st.title(f"📊 Career Intelligence Timeline")
st.write(f"**Athlete:** {name} ({athlete_country}) | **Event:** {event}")

# --- 3. DATA PREPARATION ---
history['Date'] = pd.to_datetime(history['Date'], errors='coerce')
valid_data = history.dropna(subset=['Date', 'Time_Sec']).sort_values('Date')

# Yearly Best for the "Career Best" line
yearly_best = valid_data.loc[valid_data.groupby('Year')['Time_Sec'].idxmin()].sort_values('Year')

# Trendline Calculation (Linear Regression)
x_vals = yearly_best['Year'].values
y_vals = yearly_best['Time_Sec'].values
if len(x_vals) > 1:
    slope, intercept = np.polyfit(x_vals, y_vals, 1)
    trend_line = slope * x_vals + intercept
else:
    slope = 0
    trend_line = y_vals

# PB Highlight (Find the absolute fastest race)
absolute_pb_row = yearly_best.loc[yearly_best['Time_Sec'].idxmin()]

# --- 4. TOGGLE CONTROLS ---
st.write("")
t1, t2, t3 = st.columns(3)
show_trend = t1.checkbox("📉 Trendline", value=True)
show_elite = t2.checkbox("🏆 Elite Avg", value=False)
show_pb = t3.checkbox("⭐ Highlight PB", value=True)

# --- 5. THE MASTER TIMELINE CHART ---
fig = go.Figure()

# A. Projected Confidence (Shaded Area)
if show_trend and len(x_vals) > 1:
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_vals, x_vals[::-1]]),
        y=np.concatenate([trend_line - 0.5, (trend_line + 0.5)[::-1]]),
        fill='toself',
        fillcolor='rgba(30, 144, 255, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="Projection Confidence",
        showlegend=True
    ))

# B. Career Best Line (Main Line)
fig.add_trace(go.Scatter(
    x=yearly_best['Year'],
    y=yearly_best['Time_Sec'],
    mode='lines+markers',
    name='Career Best',
    line=dict(color='#00CCFF', width=4),
    marker=dict(size=10, color='white', line=dict(width=2, color='#00CCFF')),
    customdata=yearly_best['Age'],
    hovertemplate="<b>%{x} (Age: %{customdata})</b><br>Time: %{y:.2f}s<extra></extra>"
))

# C. Progression Rate (Dashed Trendline)
if show_trend and len(x_vals) > 1:
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=trend_line,
        mode='lines',
        name='Progression Rate',
        line=dict(color='#FFD700', width=2, dash='dash'),
        hovertemplate="Trend: %{y:.2f}s<extra></extra>"
    ))

# D. Personal Best Highlight (The Star)
if show_pb:
    fig.add_trace(go.Scatter(
        x=[absolute_pb_row['Year']],
        y=[absolute_pb_row['Time_Sec']],
        mode='markers',
        name='Personal Best',
        marker=dict(symbol='star', size=18, color='#FFD700', line=dict(color='black', width=1)),
        hoverinfo="skip"
    ))

# E. Optional: Elite Average Overlay (If toggled)
if show_elite:
    global_top8_master = event_df.groupby('Year')['Time_Sec'].apply(lambda x: x.nsmallest(8).mean()).reset_index()
    fig.add_trace(go.Scatter(
        x=global_top8_master['Year'], y=global_top8_master['Time_Sec'],
        mode='lines', name='Global Top 8 Avg',
        line=dict(color='rgba(255, 100, 100, 0.4)', width=6)
    ))

# F. Layout Customization
fig.update_layout(
    template="plotly_dark", height=500, margin=dict(l=20, r=20, t=20, b=20),
    hovermode="x unified",
    yaxis=dict(title="Best Time (s)", autorange="reversed", gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    xaxis=dict(title="Year", gridcolor='rgba(255,255,255,0.05)', dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)


# --- 6. PERFORMANCE & CONTEXT (Merged from old page) ---
st.write("---")
st.title("🌍 Performance & Context")
st.write(f"### Current Standing: {name} ({athlete_country})")

# Calculate Standing Metrics
years_competing = len(yearly_best)
if years_competing <= 3: career_stage = "Rising Talent"
elif years_competing <= 7: career_stage = "Prime"
else: career_stage = "Veteran/Peak"

latest_time = yearly_best['Time_Sec'].iloc[-1]
pb_time = absolute_pb_row['Time_Sec']
dist_from_pb = latest_time - pb_time

# Calculate Gap to Top 10 All-Time in this event
top_10_threshold = event_df.groupby('Swimmer')['Time_Sec'].min().nsmallest(10).max()
gap_to_top_10 = pb_time - top_10_threshold

# Render KPI Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Career Stage", career_stage)
m2.metric("Years Competing", f"{years_competing}")
m3.metric("Gap to Top 10 (All-Time)", f"{gap_to_top_10:+.2f}s", "Lower is better", delta_color="inverse")
m4.metric("Dist. from PB (Latest Race)", f"{dist_from_pb:+.2f}s", "Distance from peak", delta_color="inverse")

st.write("<br>", unsafe_allow_html=True)
st.write(f"### Contextual Breakdown: {name} vs. The World")

# Compare Logic
all_countries = sorted(event_df['Country'].dropna().unique().tolist())
default_country = [athlete_country] if athlete_country in all_countries else []

selected_countries = st.multiselect(
    "🌍 Add Countries to Compare (Top 8 Avg):",
    options=all_countries,
    default=default_country
)

fig_context = go.Figure()

# Plot Global Average Ribbon
global_top8 = event_df.groupby('Year')['Time_Sec'].apply(lambda x: x.nsmallest(8).mean()).reset_index()
fig_context.add_trace(go.Scatter(
    x=global_top8['Year'], y=global_top8['Time_Sec'],
    mode='lines', name='Global Top 8 Avg',
    line=dict(color='rgba(255, 100, 100, 0.4)', width=8), # Thick line for the "World" benchmark
    hovertemplate="Global Elite Avg: %{y:.2f}s<extra></extra>"
))

# Plot Selected Countries
colors = ['#2ECC71', '#9B59B6', '#E67E22', '#F1C40F']
for i, country in enumerate(selected_countries):
    country_df = event_df[event_df['Country'] == country]
    if not country_df.empty:
        c_top8 = country_df.groupby('Year')['Time_Sec'].apply(lambda x: x.nsmallest(8).mean()).reset_index()
        fig_context.add_trace(go.Scatter(
            x=c_top8['Year'], y=c_top8['Time_Sec'],
            mode='lines+markers', name=f'{country} Top 8 Avg',
            line=dict(width=3, dash='dot', color=colors[i % len(colors)]),
            marker=dict(size=6),
            hovertemplate=f"{country} Avg: %{{y:.2f}}s<extra></extra>"
        ))

# Plot Athlete Line
fig_context.add_trace(go.Scatter(
    x=yearly_best['Year'], y=yearly_best['Time_Sec'],
    mode='lines+markers', name=f'{name} Best',
    line=dict(color='#00CCFF', width=4),
    marker=dict(size=8, color='white', line=dict(width=2, color='#00CCFF')),
    hovertemplate=f"{name}: %{{y:.2f}}s<extra></extra>"
))

fig_context.update_layout(
    template="plotly_dark", height=450, margin=dict(l=20, r=20, t=20, b=20),
    hovermode="x unified",
    yaxis=dict(title="Time (Seconds)", autorange="reversed", gridcolor='rgba(255,255,255,0.05)'),
    xaxis=dict(title="Year", gridcolor='rgba(255,255,255,0.05)', dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_context, use_container_width=True)


# --- 7. LA 2028 PROJECTION ENGINE ---
st.write("---")
st.write("### 🌴 LA 2028 Projection")

la_2028_targets = {
    'M': {
        '50m Freestyle': {'Gold': 21.04, 'Bronze': 21.34, 'Final': 21.42},
        '100m Freestyle': {'Gold': 46.17, 'Bronze': 47.02, 'Final': 47.46},
        '200m Freestyle': {'Gold': 103.67, 'Bronze': 103.74, 'Final': 104.82}
    },
    'F': {
        '50m Freestyle': {'Gold': 23.47, 'Bronze': 24.20, 'Final': 24.50}, 
        '100m Freestyle': {'Gold': 51.64, 'Bronze': 51.81, 'Final': 52.65},
        '200m Freestyle': {'Gold': 112.14, 'Bronze': 113.41, 'Final': 115.21}
    }
}

current_gender = history['Gender'].iloc[0]

if event in la_2028_targets.get(current_gender, {}):
    targets = la_2028_targets[current_gender][event]
    latest_year = history['Year'].max()
    years_to_2028 = 2028 - latest_year
    
    projected_drop = stats['progression_slope'] * years_to_2028
    projected_2028_time = latest_time + projected_drop
    
    st.info(f"**Baseline Prediction:** Based on historical trajectory, {name} is projected to hit **{projected_2028_time:.2f}s** by LA 2028.")
    
    if projected_2028_time <= targets['Gold']: verdict = "🥇 Gold Medal Favorite"
    elif projected_2028_time <= targets['Bronze']: verdict = "🥉 Podium Contender"
    elif projected_2028_time <= targets['Final']: verdict = "🏁 Olympic Finalist"
    elif projected_2028_time <= targets['Final'] + 0.5: verdict = "⚠️ Striking Distance"
    else: verdict = "📈 Needs Major Improvement"
        
    st.success(f"**Forecasted Outcome:** {verdict}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🥇 Gold Target", f"{targets['Gold']:.2f}s")
    c2.metric("🥉 Bronze Target", f"{targets['Bronze']:.2f}s")
    c3.metric("🏁 Final Target", f"{targets['Final']:.2f}s")
else:
    st.warning(f"No LA 2028 targets defined for {event}.")