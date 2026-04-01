import streamlit as st
import pandas as pd
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
        * **Trajectory:** Measures year-over-year improvement (slope). A negative number means they are dropping time.
        * **Consistency:** How tightly clustered their race times are. Higher is better.
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
                    st.markdown(
                        f"**Trajectory:** `{row.get('slope', 0.0):.3f}`", 
                        help="Negative is good (dropping time). 0.000 means only 1 year of data exists."
                    )
                    st.markdown(
                        f"**Consistency:** `{row.get('consistency_score', 0):.1f}%`",
                        help="Higher percentage means fewer wild fluctuations in race times."
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
                    
            fig_line.update_layout(yaxis_title="Time (Seconds)", xaxis_title="Year")
            fig_line.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_line, use_container_width=True)
            
        st.write("---")
        
        # --- 3. HEAD-TO-HEAD RADAR & COACHING ---
        st.write("### ⚔️ Head-to-Head Deep Dive")
        
        compare_name = st.selectbox("Select a peer to analyze 1-on-1 against your target:", peer_names)
        compare_stats = similar_df[similar_df['Swimmer'] == compare_name].iloc[0]
        
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            def safe_get(series, key, default=50.0):
                val = series.get(key, default)
                return default if pd.isna(val) else val

            # Normalize scores for radar chart
            dist_score_target = max(0, 100 - (safe_get(target, 'distance_from_peak', 0) * 20))
            dist_score_compare = max(0, 100 - (safe_get(compare_stats, 'distance_from_peak', 0) * 20))

            categories = ['Consistency (%)', 'Age Percentile', 'Proximity to PB']
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[safe_get(target, 'consistency_score'), safe_get(target, 'percentile', 0.5)*100, dist_score_target],
                theta=categories, fill='toself', name=name, line_color='#1E90FF'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[safe_get(compare_stats, 'consistency_score'), safe_get(compare_stats, 'percentile', 0.5)*100, dist_score_compare],
                theta=categories, fill='toself', name=compare_name, line_color='#FFD700'
            ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                showlegend=True, margin=dict(l=40, r=40, t=20, b=20), height=400
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with c2:
            st.write("### 📋 Coach's Action Plan")
            st.info(f"Comparing **{name}** vs **{compare_name}**.")
            
            t_cons = safe_get(target, 'consistency_score')
            c_cons = safe_get(compare_stats, 'consistency_score')
            t_slope = safe_get(target, 'slope', 0)
            c_slope = safe_get(compare_stats, 'slope', 0)
            
            if t_cons < c_cons - 5:
                st.warning(f"**💡 Volatility Risk:** {compare_name} was more consistent. Focus {name}'s training on race execution under fatigue.")
            else:
                st.success(f"**✅ Reliable Execution:** {name} matches or exceeds {compare_name}'s consistency.")
                
            if t_slope > c_slope:
                if c_slope == 0.0:
                     st.write(f"**💡 Trajectory Note:** Limited data for {compare_name} makes slope comparison difficult.")
                else:
                    st.warning(f"**💡 Plateau Warning:** {compare_name} dropped time at a faster historical rate. Review peak power phase.")
            elif t_slope < 0:
                st.success(f"**✅ Outpacing Peer:** {name} is on a steeper improvement curve than {compare_name}.")