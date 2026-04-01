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
        ### Understanding the "Elite 5" Radar Metrics:
        
        * **Peak Speed:** This is the athlete's all-time fastest performance in this event. On the chart, a score of **100** means they are the fastest compared to their peers.
        * **Current Form:** Measures how close the most recent season best is to their all-time PB. A high score indicates they are currently swimming at their absolute peak.
        * **Momentum:** Calculated via the progression slope. High scores indicate an athlete who is rapidly dropping time year-over-year.
        * **Consistency:** Based on the standard deviation of race times. **100** represents "machine-like" precision with very little variation between meets.
        * **Global Threat:** Measures the gap between the athlete's best time and the average pace required to make a Global Top 8 final.
        """)

    st.write("---")
    
    # 3. Run the optimized engine
    similar_df_full, target_best_time, target_event = find_similar_swimmers(target, features_df, event_df, max_n=10)
    
    st.write(f"### Finding Historical & Active Peers for: **{name}**")
    st.caption(f"**Primary Event Detected:** `{target_event}`. The AI is strictly comparing performances in this event.")

    if similar_df_full.empty:
        st.error(f"Dataset Error: Not enough data to find peers for {name} in the {target_event}.")
    else:
        # --- NEW: ERA SELECTION SLIDER ---
        # This removes gaps in the graph by allowing the user to zoom into specific time periods
        with st.container(border=True):
            st.write("#### 🗓️ Career Comparison Timeframe")
            all_years = event_df['Year'].unique()
            min_y, max_y = int(min(all_years)), int(max(all_years))
            
            selected_years = st.slider(
                "Filter years to remove historical gaps or focus on a specific Olympic cycle:",
                min_value=min_y, 
                max_value=max_y, 
                value=(max(min_y, max_y - 15), max_y), # Default to last 15 years to minimize gaps
                help="Narrow the range to eliminate empty space between retired and active swimmers."
            )

        max_available = len(similar_df_full)
        num_peers = st.selectbox(
            f"Select how many similar athletes to display:", 
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
                    st.metric("Best Time vs Target", f"{p_time:.2f}s", delta=f"{time_diff:+.2f}s", delta_color="inverse")
                    st.markdown(f"**Country:** `{row.get('Country', 'Unknown')}`")
                    row_slope = row.get('progression_slope', row.get('slope', 0.0))
                    st.markdown(f"**Trajectory:** `{row_slope:.3f}`")
                    st.markdown(f"**Consistency:** `{row.get('consistency_score', 0):.2f}`")

        st.write("---")
        
        # --- 2. MULTI-SWIMMER PROGRESSION GRAPH (WITH ERA FILTER) ---
        st.write("### 📈 Career Trajectory Comparison")
        
        compare_group = [name] + peer_names
        # Filter the history based on the slider selection
        history_df = event_df[
            (event_df['Swimmer'].isin(compare_group)) & 
            (event_df['Year'] >= selected_years[0]) & 
            (event_df['Year'] <= selected_years[1])
        ].copy()
        
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
            for trace in fig_line.data:
                if trace.name == name:
                    trace.line.width = 5
                    trace.line.color = '#1E90FF'
                else:
                    trace.line.dash = 'dot'
                    trace.line.width = 2
                    
            fig_line.update_layout(
                yaxis_title="Time (Seconds) - Lower is Faster", 
                xaxis_title="Year",
                hovermode="x unified",
                xaxis=dict(dtick=1) # Ensures year integers are shown
            )
            fig_line.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_line, width="stretch")
        else:
            st.info("No data available for the selected timeframe. Try widening the slider.")
            
        st.write("---")
        
        # --- 3. HEAD-TO-HEAD RADAR & COACHING ---
        st.write("### ⚔️ Head-to-Head Deep Dive")
        
        compare_name = st.selectbox("Select a peer to analyze 1-on-1 against your target:", peer_names)
        compare_stats = similar_df[similar_df['Swimmer'] == compare_name].iloc[0]
        
        # [Metric Calculation Logic...]
        t_bt, c_bt = target_best_time, compare_stats['best_time']
        t_form, c_form = target.get('distance_from_peak', 0.0), compare_stats.get('distance_from_peak', 0.0)
        t_slope = target.get('progression_slope', 0.0)
        c_slope = compare_stats.get('progression_slope', 0.0)
        t_cons, c_cons = target.get('consistency_score', 0.0), compare_stats.get('consistency_score', 0.0)
        t_threat, c_threat = target.get('latest_gap_to_top10', 0.0), compare_stats.get('latest_gap_to_top10', 0.0)

        def fmt_d(val1, val2):
            diff = val2 - val1
            return f"({diff:+.2f})" if diff != 0 else "(Equal)"

        col_table, col_radar = st.columns([1, 1], gap="large")

        with col_table:
            st.write("#### 🥊 Tale of the Tape")
            st.markdown(f"""
            | Metric | {name} | {compare_name} |
            | :--- | :--- | :--- |
            | **Peak Speed** | **{t_bt:.2f}s** | {c_bt:.2f}s {fmt_d(t_bt, c_bt)} |
            | **Current Form**| **{t_form:.2f}s** | {c_form:.2f}s {fmt_d(t_form, c_form)} |
            | **Momentum** | **{t_slope:.3f}** | {c_slope:.3f} {fmt_d(t_slope, c_slope)} |
            | **Consistency** | **{t_cons:.2f}** | {c_cons:.2f} {fmt_d(t_cons, c_cons)} |
            | **Threat** | **{t_threat:.2f}s** | {c_threat:.2f}s {fmt_d(t_threat, c_threat)} |
            """)

        with col_radar:
            min_time, max_time = similar_df_full['best_time'].min(), similar_df_full['best_time'].max()

            def calc_radar_scores(bt, form, slope, cons, threat):
                speed_score = max(0, min(100, 100 - ((bt - min_time) / (max_time - min_time or 1) * 100)))
                form_score = max(0, min(100, 100 - (form * 20)))
                mom_score = max(0, min(100, 50 - (slope * 100)))
                cons_score = max(0, min(100, 100 - (cons * 30)))
                threat_score = max(0, min(100, 80 - (threat * 15)))
                return [speed_score, form_score, mom_score, cons_score, threat_score]

            target_scores = calc_radar_scores(t_bt, t_form, t_slope, t_cons, t_threat)
            compare_scores = calc_radar_scores(c_bt, c_form, c_slope, c_cons, c_threat)
            categories = ['Peak Speed', 'Current Form', 'Momentum', 'Consistency', 'Global Threat']
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=target_scores, theta=categories, fill='toself', name=name, line_color='#1E90FF'))
            fig_radar.add_trace(go.Scatterpolar(r=compare_scores, theta=categories, fill='toself', name=compare_name, line_color='#FFD700'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=400, margin=dict(l=50, r=50, t=20, b=20))
            st.plotly_chart(fig_radar, width="stretch")

        st.write("### 📋 Coach's Action Plan")
        with st.container(border=True):
            if t_bt < c_bt and t_cons > c_cons + 0.3:
                st.warning(f"**💡 The Glass Cannon:** {name} has superior speed, but {compare_name} is significantly more consistent.")
            elif t_slope < c_slope - 0.1:
                st.success(f"**🚀 Closing the Gap:** {name} has vastly superior Momentum right now.")
            else:
                st.success(f"**✅ Stable Matchup:** Victory depends on marginal gains in turns and transitions.")