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
event_df = st.session_state['event_df'].copy() 
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

# --- 4. TOGGLE CONTROLS (WITH TOOLTIPS) ---
st.write("")
t1, t2 = st.columns(2)
show_trend = t1.checkbox("📉 Trendline", value=True, 
                         help="Displays a linear trajectory of the athlete's progression rate, accompanied by a shaded confidence band to forecast near-future times.")
show_pb = t2.checkbox("⭐ Highlight PB", value=True, 
                      help="Drops a star on the absolute fastest recorded time of this athlete's career.")

# --- SHORT-TERM PREDICTION LOGIC ---
ts_data = valid_data.groupby('Date')['Time_Sec'].min().reset_index()
prediction = None
if len(ts_data) >= 6:
    try:
        model = Holt(np.asarray(ts_data['Time_Sec']), initialization_method="estimated")
        fit_model = model.fit()
        forecast = fit_model.forecast(1) 
        prediction = forecast[0]
    except:
        pass

# --- 5. THE MASTER TIMELINE CHART ---
fig = go.Figure()

# A. Projected Confidence (Shaded Area)
if show_trend and len(x_vals) > 1:
    # Extend the line slightly for visual effect
    future_x = np.append(x_vals, x_vals[-1] + 1)
    future_trend = slope * future_x + intercept
    fig.add_trace(go.Scatter(
        x=np.concatenate([future_x, future_x[::-1]]),
        y=np.concatenate([future_trend - 0.5, (future_trend + 0.5)[::-1]]),
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
    future_x = np.append(x_vals, x_vals[-1] + 1)
    future_trend = slope * future_x + intercept
    fig.add_trace(go.Scatter(
        x=future_x,
        y=future_trend,
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

# E. Short-Term Prediction Point
if prediction:
    last_year = yearly_best['Year'].iloc[-1]
    last_time = yearly_best['Time_Sec'].iloc[-1]
    
    fig.add_trace(go.Scatter(
        x=[last_year, last_year + 1],
        y=[last_time, prediction],
        mode='lines+markers',
        name='Short-Term Forecast',
        line=dict(color='#00CCFF', width=3, dash='dot'),
        marker=dict(size=10, symbol='circle-open', color='#00CCFF', line=dict(width=3)),
        hovertemplate="Forecast Year: %{x}<br>Est. Time: %{y:.2f}s<extra></extra>"
    ))

# F. Layout Customization
fig.update_layout(
    template="plotly_dark", height=500, margin=dict(l=20, r=20, t=20, b=20),
    hovermode="x unified",
    yaxis=dict(title="Best Time (s)", autorange="reversed", gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    xaxis=dict(title="Year", gridcolor='rgba(255,255,255,0.05)', dtick=1)
    # Legend is removed from update_layout to default to right-side vertical
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

# Render KPI Metrics (WITH TOOLTIPS)
m1, m2, m3, m4 = st.columns(4)

m1.metric("Career Stage", career_stage, 
          help="Classified based on active years: Rising Talent (1-3 yrs), Prime (4-7 yrs), or Veteran/Peak (8+ yrs).")

m2.metric("Years Competing", f"{years_competing}", 
          help="The total number of calendar years this athlete has recorded a competitive time in this specific event.")

m3.metric("Gap to Top 10 (All-Time)", f"{gap_to_top_10:+.2f}s", "Lower is better", delta_color="inverse", 
          help="The time gap between the athlete's Personal Best and the 10th fastest swimmer in recorded history. A negative number means they are inside the Top 10 globally.")

m4.metric("Dist. from PB (Latest Race)", f"{dist_from_pb:+.2f}s", "Distance from peak", delta_color="inverse", 
          help="The difference between their most recent recorded time and their absolute lifetime Personal Best. A number close to zero indicates they are currently in peak form.")

st.write("<br>", unsafe_allow_html=True)
st.write(f"### Contextual Breakdown: {name} vs. The World")

# Compare Logic (WITH TOOLTIPS)
all_countries = sorted(event_df['Country'].dropna().unique().tolist())
default_country = [athlete_country] if athlete_country in all_countries else []

selected_countries = st.multiselect(
    "🌍 Add Countries to Compare (Top 8 Avg):",
    options=all_countries,
    default=default_country,
    help="Select one or more nations to plot their historical Top 8 averages. This allows coaches to see if the athlete is on pace with regional powerhouses."
)

fig_context = go.Figure()

# Plot Global Average Ribbon
global_top8 = event_df.groupby('Year')['Time_Sec'].apply(lambda x: x.nsmallest(8).mean()).reset_index()
fig_context.add_trace(go.Scatter(
    x=global_top8['Year'], y=global_top8['Time_Sec'],
    mode='lines', name='Global Top 8 Avg',
    line=dict(color='rgba(255, 100, 100, 0.4)', width=8),
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
    xaxis=dict(title="Year", gridcolor='rgba(255,255,255,0.05)', dtick=1)
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
    
    st.info(f"**Baseline Prediction:** Based on their historical trajectory, {name}'s projected best time for LA 2028 is **{projected_2028_time:.2f}s**.")
    
    if projected_2028_time <= targets['Gold']: 
        verdict = "🥇 Gold Medal Favorite"
        marker_color = "gold"
    elif projected_2028_time <= targets['Bronze']: 
        verdict = "🥉 Podium Contender"
        marker_color = "#CD7F32" # Bronze
    elif projected_2028_time <= targets['Final']: 
        verdict = "🏁 Olympic Finalist"
        marker_color = "white"
    elif projected_2028_time <= targets['Final'] + 0.5: 
        verdict = "⚠️ Striking Distance"
        marker_color = "#1E90FF" # Blue
    else: 
        verdict = "📉 Needs Major Improvement"
        marker_color = "#1E90FF" # Blue
        
    if "🥇" in verdict or "🥉" in verdict or "🏁" in verdict:
        st.success(f"**Forecasted Outcome:** {verdict}")
    elif "⚠️" in verdict:
        st.warning(f"**Forecasted Outcome:** {verdict}")
    else:
        st.error(f"**Forecasted Outcome:** {verdict}")

    st.write("#### 📏 Projected Placement Zones")
    
    # Generate the placement zones visual
    fig_zones = go.Figure()
    
    gold_t = targets['Gold']
    bronze_t = targets['Bronze']
    final_t = targets['Final']
    
    # Calculate a buffer to frame the chart well
    min_x = min(gold_t, projected_2028_time) - 0.8
    max_x = max(final_t, projected_2028_time) + 1.2
    
    # Add colored background zones
    fig_zones.add_vrect(x0=bronze_t, x1=final_t, fillcolor="rgba(255, 255, 255, 0.05)", layer="below", line_width=0, annotation_text="Finalist Pace", annotation_position="top left", annotation_font_color="white")
    fig_zones.add_vrect(x0=gold_t, x1=bronze_t, fillcolor="rgba(205, 127, 50, 0.15)", layer="below", line_width=0, annotation_text="Podium Pace", annotation_position="top left", annotation_font_color="white")
    fig_zones.add_vrect(x0=min_x, x1=gold_t, fillcolor="rgba(255, 215, 0, 0.15)", layer="below", line_width=0, annotation_text="Gold Pace", annotation_position="top left", annotation_font_color="white")

    # Add dividing target lines
    fig_zones.add_vline(x=gold_t, line_dash="dash", line_color="gold", opacity=0.8)
    fig_zones.add_vline(x=bronze_t, line_dash="dash", line_color="#CD7F32", opacity=0.8)
    fig_zones.add_vline(x=final_t, line_dash="dash", line_color="white", opacity=0.5)

    # Plot the athlete's projected time
    fig_zones.add_trace(go.Scatter(
        x=[projected_2028_time],
        y=[0],
        mode="markers+text",
        marker=dict(symbol="diamond", size=18, color=marker_color),
        text=[f"{name} ({projected_2028_time:.2f}s)"],
        textposition="middle right",
        textfont=dict(color=marker_color, size=14, weight="bold"),
        hoverinfo="skip"
    ))

    # Layout for the timeline
    fig_zones.update_layout(
        template="plotly_dark",
        height=200,
        margin=dict(l=20, r=20, t=30, b=30),
        yaxis=dict(visible=False, range=[-1, 1]), # Lock y-axis to keep marker centered vertically
        xaxis=dict(
            title="Time in Seconds (Further Left = Faster)",
            range=[max_x, min_x], # By setting max first, it automatically reverses the axis
            gridcolor='rgba(255,255,255,0.05)',
            zeroline=False
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig_zones, use_container_width=True)
    
    # Calculate performance gap strings for the metrics
    def get_gap_delta(target_t, proj_t):
        diff = proj_t - target_t
        if diff <= 0:
            return f"✅ Reached ({-diff:.2f}s under)"
        else:
            return f"❌ Missed (+{diff:.2f}s)"

    # Render LA 2028 Metrics (WITH TOOLTIPS AND HIT/MISS DELTAS)
    c1, c2, c3 = st.columns(3)
    c1.metric("🥇 Gold Target", f"{targets['Gold']:.2f}s", 
              delta=get_gap_delta(targets['Gold'], projected_2028_time), delta_color="inverse",
              help="Estimated time required to win Gold at LA 2028.")
              
    c2.metric("🥉 Bronze Target", f"{targets['Bronze']:.2f}s", 
              delta=get_gap_delta(targets['Bronze'], projected_2028_time), delta_color="inverse",
              help="Estimated time required to make the Podium at LA 2028.")
              
    c3.metric("🏁 Final Target", f"{targets['Final']:.2f}s", 
              delta=get_gap_delta(targets['Final'], projected_2028_time), delta_color="inverse",
              help="Estimated time required to qualify for the Top 8 Olympic Final at LA 2028.")
else:
    st.warning(f"No LA 2028 targets defined for {event}.")