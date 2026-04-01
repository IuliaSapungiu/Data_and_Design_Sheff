import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from features.comparator import find_similar_swimmers
from shared_ui import render_navbar

# 1. Page Config and Navbar (Must be at the very top)
st.set_page_config(page_title="Comparator Dashboard", layout="wide")
render_navbar()

st.title("🤝 Athlete Comparator & Coach's Corner")

# 2. Data Safety Check
if 'swimmer_stats' not in st.session_state or 'features_df' not in st.session_state:
    st.warning("Please go to the Control Room and hit 'Process Analytics' first!")
else:
    target = st.session_state['swimmer_stats']
    features_df = st.session_state['features_df']
    event_df = st.session_state['event_df']
    name = target['Swimmer']

    # --- COACH'S GUIDE ---
    with st.expander("📚 How to read these benchmarks (Coach's Guide)", expanded=False):
        st.markdown("""
        ### Understanding the AI Benchmarks
        This engine uses a **K-Nearest Neighbors (KNN)** algorithm with a **Smart Quality Threshold**. It doesn't just return a random top 10; it only returns athletes who are *statistically close* to your target in their specific primary event.

        #### The Metrics Explained:
        * **Best Time vs Target:** The raw speed difference. A negative delta means this peer was *faster*.
        * **Trajectory:** Measures year-over-year improvement. A negative number means they are dropping time. `0.000` means they only have one year of data on record.
        * **Consistency:** How tightly clustered their race times are. Higher is better.
        """)

    st.write("---")
    
    # 3. Run the optimized engine
    similar_df_full, target_best_time, target_event = find_similar_swimmers(target, features_df, event_df, max_n=10)
    
    st.write(f"### Finding Historical & Active Peers for: **{name}**")
    st.caption(f"**Primary Event Detected:** `{target_event}`. The AI is strictly comparing performances in this event globally.")

    if similar_df_full.empty:
        st.error(f"Dataset Error: Not enough data to find peers for {name} in the {target_event}.")
    else:
        max_available = len(similar_df_full)
        
        # DYNAMIC DROPDOWN
        num_peers = st.selectbox(
            f"Select how many similar athletes to display (The AI approved {max_available} highly accurate matches):", 
            options=list(range(1, max_available + 1)), 
            index=min(2, max_available - 1)
        )
        
        similar_df = similar_df_full.head(num_peers)
        peer_names = similar_df['Swimmer'].tolist()
        
        # --- 1. DYNAMIC MATCHES SHOWCASE ---
        st.markdown(f"##### 🥇 Top {num_peers} closest historical/active matches:")
        
        cols = st.columns(3)
        for i, (_, row) in enumerate(similar_df.iterrows()):
            with cols[i % 3]: 
                with st.container(border=True):
                    st.write(f"#### {row['Swimmer']}")
                    
                    p_time = row['best_time']
                    time_diff = p_time - target_best_time
                    
                    st.metric(
                        "Best Time vs Target", 
                        f"{p_time:.2f}s", 
                        delta=f"{time_diff:+.2f}s", 
                        delta_color="inverse",
                        help="The absolute fastest time this athlete achieved in this event compared to your target."
                    )
                    
                    row_slope = row.get('progression_slope', row.get('slope', 0.0))
                    
                    st.markdown(f"**Country:** `{row.get('Country', 'N/A')}`")
                    st.markdown(
                        f"**Trajectory:** `{row_slope:.3f}`", 
                        help="Negative is good (dropping time). 0.000 means only 1 year of data exists."
                    )
                    st.markdown(
                        f"**Consistency:** `{row.get('consistency_score', 0):.2f}`",
                        help="Standard deviation. Closer to 0 is better."
                    )

        st.write("---")
        
        # --- 2. MULTI-SWIMMER PROGRESSION GRAPH ---
        st.write("### 📈 Career Trajectory Comparison")
        
        st.info("""
        **How to read this chart:**
        * **The Axes:** The bottom axis shows the progression of years. The side axis shows the race time. **Note that the chart is visually inverted:** higher up on the graph means a *faster* time.
        * **The Lines:** The thick solid blue line is your target athlete. The dotted lines are the selected peers.
        * **The Trend:** A line sloping upwards (getting faster) means the swimmer is dropping time year-over-year. A flat line indicates a plateau.
        """)
        
        compare_group = [name] + peer_names
        history_df = event_df[(event_df['Swimmer'].isin(compare_group))].copy()
        
        if not history_df.empty:
            yearly_progression = history_df.groupby(['Year', 'Swimmer'])['Time_Sec'].min().reset_index()
            
            fig_line = px.line(
                yearly_progression, 
                x='Year', 
                y='Time_Sec', 
                color='Swimmer',
                markers=True,
                template="plotly_white"
            )
            # Highlighting the target swimmer
            for trace in fig_line.data:
                if trace.name == name:
                    trace.line.width = 5
                    trace.line.color = '#1E90FF'
                else:
                    trace.line.dash = 'dot'
                    trace.line.width = 2
                    
            fig_line.update_layout(yaxis_title="Time (Seconds) - Higher is Faster", xaxis_title="Year")
            fig_line.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_line, use_container_width=True)
            
        st.write("---")
        
        # --- 3. HEAD-TO-HEAD RADAR & COACHING ---
        st.write("### ⚔️ Head-to-Head Deep Dive")
        
        compare_name = st.selectbox("Select a peer to analyze 1-on-1 against your target:", similar_df_full['Swimmer'].tolist())
        compare_stats = similar_df_full[similar_df_full['Swimmer'] == compare_name].iloc[0]
        
        # Helper to safely extract metrics
        def safe_get(series, key, default=0.0):
            val = series.get(key, default)
            return default if pd.isna(val) else val

        t_bt = target_best_time
        c_bt = safe_get(compare_stats, 'best_time')
        t_form = safe_get(target, 'distance_from_peak')
        c_form = safe_get(compare_stats, 'distance_from_peak')
        t_slope = safe_get(target, 'progression_slope', safe_get(target, 'slope', 0.0))
        c_slope = safe_get(compare_stats, 'progression_slope', safe_get(compare_stats, 'slope', 0.0))
        t_cons = safe_get(target, 'consistency_score')
        c_cons = safe_get(compare_stats, 'consistency_score')
        t_threat = safe_get(target, 'latest_gap_to_top10')
        c_threat = safe_get(compare_stats, 'latest_gap_to_top10')
        
        # --- THE TALE OF THE TAPE (RAW NUMBERS) ---
        st.write("#### 🥊 Tale of the Tape")
        
        def fmt_d(val1, val2):
            diff = val2 - val1
            return f"({diff:+.2f})" if diff != 0 else "(Equal)"

        st.markdown(f"""
        | Metric | {name} | {compare_name} |
        | :--- | :--- | :--- |
        | **Peak Speed (Best Time)** | **{t_bt:.2f}s** | {c_bt:.2f}s {fmt_d(t_bt, c_bt)} |
        | **Current Form (Off Peak)**| **{t_form:.2f}s** | {c_form:.2f}s {fmt_d(t_form, c_form)} |
        | **Momentum (Trajectory)** | **{t_slope:.3f}** | {c_slope:.3f} {fmt_d(t_slope, c_slope)} |
        | **Consistency (Std Dev)** | **{t_cons:.2f}** | {c_cons:.2f} {fmt_d(t_cons, c_cons)} |
        | **Threat (Gap to Top 8)** | **{t_threat:.2f}s** | {c_threat:.2f}s {fmt_d(t_threat, c_threat)} |
        """)
        
        st.write("") # Spacer

        # --- THE HEXAGON RADAR CHART ---
        st.info("""
        **How to read the Radar Chart (The Triangle):** This chart maps three key career attributes on a scale of 0 to 100. 
        * **The Shape:** The three points of the triangle represent the athlete's score in **Consistency**, **Age**, and **Proximity to PB**. 
        * **The Size:** The further outward a point stretches toward the edge, the stronger that trait is. A larger overall triangle indicates a more robust or dominant statistical profile.
        * **The Metrics:**
            * **Consistency (%):** Closer to the edge means they almost always swim their typical time (highly reliable).
            * **Age Percentile:** Closer to the edge means they are younger relative to the historical dataset.
            * **Proximity to PB:** Closer to the edge means their typical, everyday form is extremely close to their all-time personal best.
        """)

        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            dist_score_target = max(0, 100 - (safe_get(target, 'distance_from_peak', 0) * 20))
            dist_score_compare = max(0, 100 - (safe_get(compare_stats, 'distance_from_peak', 0) * 20))

            categories = ['Consistency (%)', 'Age Percentile', 'Proximity to PB']
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[safe_get(target, 'consistency_score', 50), safe_get(target, 'age_percentile', 50), dist_score_target],
                theta=categories, fill='toself', name=name, line_color='#1E90FF'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[safe_get(compare_stats, 'consistency_score', 50), safe_get(compare_stats, 'age_percentile', 50), dist_score_compare],
                theta=categories, fill='toself', name=compare_name, line_color='#FFD700'
            ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                showlegend=True, margin=dict(l=50, r=50, t=20, b=20), height=400
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
        # --- THE COACH'S ACTION PLAN ---
        with c2:
            st.write("### 📋 Coach's Action Plan")
            st.caption(f"Comparing **{name}** vs **{compare_name}**.")
            
            if t_cons < c_cons - 5:
                st.warning(f"**💡 Volatility Risk:** {compare_name} was more consistent. Focus {name}'s training on race execution under fatigue.")
            else:
                st.success(f"**✅ Reliable Execution:** {name} matches or exceeds {compare_name}'s consistency.")
                
            if t_slope > c_slope:
                if c_slope == 0.0:
                     st.write(f"**💡 Trajectory Note:** Not enough multi-year data for {compare_name} to generate a historical trajectory comparison.")
                else:
                    st.warning(f"**💡 Plateau Warning:** {compare_name} dropped time at a faster historical rate. Review taper strategies.")
            elif t_slope < c_slope and t_slope < 0:
                st.success(f"**✅ Outpacing Peer:** {name} is on a steeper improvement curve than {compare_name}.")