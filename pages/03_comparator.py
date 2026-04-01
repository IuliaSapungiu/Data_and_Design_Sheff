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

        #### The "Elite 5" Profile Metrics Explained:
        * **Peak Speed:** How their absolute Best Time ranks against this specific group of peers (100 = Fastest in group).
        * **Current Form:** How close their most recent season was to their all-time peak (100 = Currently at Absolute Peak).
        * **Momentum:** Their historical time-dropping trajectory. (100 = Rapidly dropping time. 50 = Flatlining).
        * **Consistency:** The standard deviation of their race times (100 = Machine-like precision).
        * **Global Threat:** How their average speed compares to the pace required to make a Global Final (100 = Comfortably faster than Top 8 average).
        """)

    st.write("---")
    
    # 3. Run the optimized engine
    # This uses the pre-calculated features for instant results
    similar_df_full, target_best_time, target_event = find_similar_swimmers(target, features_df, event_df, max_n=10)
    
    st.write(f"### Finding Historical & Active Peers for: **{name}**")
    st.caption(f"**Primary Event Detected:** `{target_event}`. The AI is strictly comparing performances in this event.")

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
                    
                    st.markdown(f"**Country:** `{row.get('Country', 'Unknown')}`")
                    
                    # Safe get slope (handling different naming conventions in progression.py vs comparator.py)
                    row_slope = row.get('progression_slope', row.get('slope', 0.0))
                    
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
        
        compare_group = [name] + peer_names
        # FIX: Changed 'Time' to 'Time_Sec' to match optimized data processor
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
                    
            fig_line.update_layout(yaxis_title="Time (Seconds) - Lower is Faster", xaxis_title="Year")
            fig_line.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_line, width="stretch")
            
        st.write("---")
        
        # --- 3. HEAD-TO-HEAD RADAR & COACHING ---
        st.write("### ⚔️ Head-to-Head Deep Dive")
        
        compare_name = st.selectbox("Select a peer to analyze 1-on-1 against your target:", peer_names)
        compare_stats = similar_df[similar_df['Swimmer'] == compare_name].iloc[0]
        
        # Helper to safely extract metrics
        def safe_get(series, key, default=0.0):
            val = series.get(key, default)
            return default if pd.isna(val) else val

        # Extract Raw Metrics for the "Tale of the Tape"
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
        
        # Format delta strings (+/-)
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
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            # Radar Normalizer Logic (Translates raw metrics to a 0-100 score where 100 is always better)
            min_time = similar_df_full['best_time'].min()
            max_time = similar_df_full['best_time'].max()

            def calc_radar_scores(bt, form, slope, cons, threat):
                # 1. Peak Speed (100 = fastest in this specific peer group)
                if max_time == min_time: speed_score = 100
                else: speed_score = max(0, min(100, 100 - ((bt - min_time) / (max_time - min_time) * 100)))

                # 2. Current Form (100 = 0s off their absolute PB)
                form_score = max(0, min(100, 100 - (form * 20)))

                # 3. Momentum (100 = steep negative time drop. 50 = flatline)
                mom_score = max(0, min(100, 50 - (slope * 100)))

                # 4. Consistency (100 = 0 standard deviation)
                cons_score = max(0, min(100, 100 - (cons * 30)))

                # 5. Global Threat (100 = Way faster than Top 8 average. 50 = Exactly Top 8)
                threat_score = max(0, min(100, 80 - (threat * 15)))

                return [speed_score, form_score, mom_score, cons_score, threat_score]

            target_scores = calc_radar_scores(t_bt, t_form, t_slope, t_cons, t_threat)
            compare_scores = calc_radar_scores(c_bt, c_form, c_slope, c_cons, c_threat)
            
            categories = ['Peak Speed', 'Current Form', 'Momentum', 'Consistency', 'Global Threat']
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=target_scores, theta=categories, fill='toself', name=name, line_color='#1E90FF'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=compare_scores, theta=categories, fill='toself', name=compare_name, line_color='#FFD700'
            ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                showlegend=True, margin=dict(l=50, r=50, t=20, b=20), height=400
            )
            st.plotly_chart(fig_radar, width="stretch")
            
        # --- THE COACH'S ACTION PLAN ---
        with c2:
            st.write("### 📋 Coach's Action Plan")
            st.info(f"Comparing **{name}** vs **{compare_name}**.")
            
            # Scenario 1: The Glass Cannon
            if t_bt < c_bt and t_cons > c_cons + 0.3:
                st.warning(f"**💡 The Glass Cannon:** {name} has superior raw Peak Speed, but {compare_name} is significantly more consistent. In a high-pressure tournament, {name} must focus heavily on race reliability to avoid being upset.")
            elif c_bt < t_bt and c_cons > t_cons + 0.3:
                st.warning(f"**💡 High Volatility:** {compare_name} has both superior Peak Speed AND better consistency. {name} needs to drastically stabilize their execution to compete.")
            
            # Scenario 2: Closing the Gap (Momentum)
            elif t_bt > c_bt and t_slope < c_slope - 0.1:
                st.success(f"**🚀 Closing the Gap:** {compare_name} has a faster historical peak, but {name} has vastly superior Momentum right now. {name} is on a trajectory to overtake them soon.")
            elif c_bt > t_bt and c_slope < t_slope - 0.1:
                st.error(f"**⚠️ Threat Approaching:** {name} is historically faster, but {compare_name} is dropping time at a much faster rate. Review taper and training strategies to break {name}'s plateau.")
                
            # Scenario 3: Form vs Speed
            elif t_form > 1.0 and c_form < 0.5:
                st.warning(f"**📉 Off-Peak Risk:** {name} is currently struggling to find their historical form, while {compare_name} is swimming near their absolute best. Current conditioning favors the opponent.")
            
            # Default / Stable Matchup
            else:
                st.success(f"**✅ Stable Matchup:** Both athletes present highly comparable profiles. Victory will come down to marginal gains in race day execution, reaction time, and turns.")