import streamlit as st
import plotly.graph_objects as go
from shared_ui import render_navbar

render_navbar()

st.title("Performance & Context")

if 'swimmer_stats' not in st.session_state:
    st.warning("Please go back to the Control Room (App) and click 'Process Analytics' first.")
else:
    stats = st.session_state['swimmer_stats']
    name = st.session_state['swimmer_name']
    history = st.session_state['swimmer_history']
    event_df = st.session_state['event_df'] 
    
    st.write(f"### Current Standing: {name}")
    
    # --- 1. BENCHMARK EVALUATION LOGIC ---
    gap = stats['latest_gap_to_top10']
    if gap <= 0:
        gap_eval = "👑 Elite / Podium Pace"
        gap_text = f"{abs(gap):.2f}s (Top 10)"
    elif gap <= 0.5:
        gap_eval = "🚀 Finalist Pace"
        gap_text = f"+{gap:.2f}s (Slower)"
    elif gap <= 1.5:
        gap_eval = "🏊 Competitive"
        gap_text = f"+{gap:.2f}s (Slower)"
    else:
        gap_eval = "📈 Developing"
        gap_text = f"+{gap:.2f}s (Slower)"

    dist_pb = stats['distance_from_peak']
    if dist_pb == 0.0:
        pb_eval = "🔥 Absolute Peak"
    elif dist_pb <= 0.3:
        pb_eval = "⚡ Near Peak"
    else:
        pb_eval = "📉 Off Peak"

    # --- 2. DISPLAY METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Career Stage", stats['career_stage'], help="Based on their age in their most recent active year: Early (<20), Peak (20-26), Decline (>26).")
    col2.metric("Years Competing", int(stats['years_competing']), help="Total distinct years this athlete recorded a time.")
    
    col3.metric(
        label="Gap to Top 10", 
        value=gap_text,
        delta=gap_eval,
        delta_color="off",
        help="Difference between their latest best time and the 10th fastest global time that year."
    )
    
    col4.metric(
        label="Dist. from PB", 
        value=f"{dist_pb:.2f} s",
        delta=pb_eval,
        delta_color="off",
        help="Time difference between their latest season's best and their all-time personal best."
    )

    with st.expander("📚 How to read these benchmarks (Coach's Guide)"):
        st.markdown("""
        * **Gap to Top 10:** If they are inside the Top 10 (`<= 0s`), they are on **Elite / Podium Pace**. Being within 0.5s is considered **Finalist Pace**.
        * **Distance from PB:** If the distance is `0.00s`, it means their most recent season was their absolute fastest ever (**Absolute Peak**).
        """)

    st.write("---")
    
# --- 3. THE VISUALISATION: Swimmer vs. The World ---
    st.write("### Contextual Breakdown: Swimmer vs. The World")
    
    global_yearly = event_df.groupby('Year')['Time_Sec'].agg(
        top_10_time=lambda x: x.nsmallest(10).max() if len(x) >= 10 else x.max()
    ).reset_index()
    
    swimmer_yearly = history.groupby('Year')['Time_Sec'].min().reset_index()
    swimmer_yearly.rename(columns={'Time_Sec': 'Swimmer_Time'}, inplace=True)
    
    compare_df = swimmer_yearly.merge(global_yearly, on='Year', how='left')
    
    if len(compare_df) > 0:
        fig = go.Figure()
        
        # FIX: Dynamically calculate the ceiling so we don't ruin the scale!
        fastest_time = min(compare_df['top_10_time'].min(), compare_df['Swimmer_Time'].min())
        ceiling_time = fastest_time - 1.0 # Just 1 second faster than the best time on the chart
        
        # Add the invisible ceiling
        fig.add_trace(go.Scatter(
            x=compare_df['Year'], y=[ceiling_time]*len(compare_df), 
            mode='none', showlegend=False, hoverinfo='skip'
        ))
        
        # Then we draw the Top 10 line and fill the space between it and the invisible ceiling
        fig.add_trace(go.Scatter(
            x=compare_df['Year'], y=compare_df['top_10_time'], 
            mode='lines+markers', name='Global Top 10 Cutoff',
            line=dict(color='red', dash='dash'),
            fill='tonexty', fillcolor='rgba(255, 215, 0, 0.15)' # Faint Gold Shading
        ))
                                 
        # Add our Swimmer's line on top
        fig.add_trace(go.Scatter(
            x=compare_df['Year'], y=compare_df['Swimmer_Time'], 
            mode='lines+markers', name=f'{name} Best Time',
            line=dict(color='blue', width=3)
        ))
        
        fig.update_layout(
            title=f"Yearly Comparison: {name} vs. Global Top 10 Cutoff",
            xaxis_title="Year",
            yaxis_title="Time (Seconds) - Lower is Faster",
            hovermode="x unified"
        )
                          
        # Invert the Y-axis so "Faster" is visually UP
        fig.update_yaxes(autorange="reversed")
        
        # Add an annotation to explain the gold zone (dynamically placed now)
        fig.add_annotation(
            x=compare_df['Year'].iloc[0], y=compare_df['top_10_time'].iloc[0] - 0.2,
            text="🏆 Elite Zone", showarrow=False, font=dict(color="goldenrod")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to plot a comparison chart.")