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

# Helper to safely extract metrics
def safe_get(series, key, default=0.0):
    val = series.get(key, default)
    return default if pd.isna(val) else val

# 2. Data Safety Check
if 'swimmer_stats' not in st.session_state or 'features_df' not in st.session_state:
    st.warning("Please go to the Control Room and hit 'Process Analytics' first!")
else:
    target = st.session_state['swimmer_stats']
    features_df = st.session_state['features_df']
    event_df = st.session_state['event_df']
    name = target['Swimmer']
    
    # Safely extract country for Tarun's National filtering
    raw_country = target.get('Country', target.get('country'))
    athlete_country = "Unknown" if pd.isna(raw_country) or not str(raw_country).strip() else str(raw_country)

    # Initialize map state variable if not present
    if 'map_focus' not in st.session_state:
        st.session_state.map_focus = None

    # --- COACH'S GUIDE ---
    with st.expander("📚 How to read these benchmarks (Coach's Guide)", expanded=False):
        st.markdown("""
        ### Understanding the AI Benchmarks
        This engine uses a **K-Nearest Neighbors (KNN)** algorithm with a **Smart Quality Threshold**. It doesn't just return a random top 10; it only returns athletes who are *statistically close* to your target in their specific primary event.

        #### The Top Match Cards Explained:
        * **Best Time vs Target:** The raw speed difference (colored pill). 
            * **Green (-)** means this peer was *faster* than your swimmer.
            * **Red (+)** means this peer was *slower* than your swimmer.
        * **📈 Trajectory:** Measures year-over-year improvement. A negative number means they are dropping time. `0.000` means they only have one year of data on record.
        * **🎯 Consistency:** How tightly clustered their race times are. A lower score means they swim very similar times in every race. A higher score means their performance fluctuates wildly.
        """)

    st.write("---")
    st.write(f"### Finding Peers for: **{name}**")

    # --- COMPACT UNIFIED CONTROL PANEL ---
    with st.container(border=True):
        st.markdown("#### ⚙️ Match Engine Settings")
        
        c1, c2 = st.columns([1.2, 2], gap="medium")
        
        with c1:
            scope_options = ["🌍 Global (All)"]
            if athlete_country != "Unknown":
                scope_options.append(f"📍 National ({athlete_country})")
                
            scope = st.radio(
                "**1️⃣ Comparison Scope**",
                scope_options,
                help="Global uses the full dataset. National restricts peers exclusively to the athlete's home country."
            )
            
            if athlete_country == "Unknown":
                st.caption("⚠️ *National scope disabled (Athlete's country is missing from the database).*")
            
        # --- RUN ENGINE IN THE BACKGROUND ---
        if "National" in scope:
            working_event_df = event_df[event_df['Country'] == athlete_country].copy()
            national_swimmers = working_event_df['Swimmer'].unique()
            working_features_df = features_df[features_df['Swimmer'].isin(national_swimmers)].copy()
        else:
            working_features_df = features_df.copy()
            working_event_df = event_df.copy()

        # 3. Run the optimized engine
        similar_df_full, target_best_time, target_event = find_similar_swimmers(target, working_features_df, working_event_df, max_n=10)

        if not similar_df_full.empty:
            with c2:
                max_available = len(similar_df_full)
                num_peers = st.selectbox(
                    "**2️⃣ Matches to Display**", 
                    options=list(range(1, max_available + 1)), 
                    index=min(2, max_available - 1), 
                    help="Select how many similar athletes to show in the cards and graph."
                )
                st.write("") # Spacer
                st.caption(f"🎯 **Target Event:** `{target_event}` | The AI is comparing performances strictly within this event.")
        else:
            st.error(f"Dataset Error: Not enough data to find peers for {name} in the selected scope.")

    # Only render the rest of the page if the engine found peers
    if not similar_df_full.empty:
        similar_df = similar_df_full.head(num_peers)
        peer_names = similar_df['Swimmer'].tolist()
        
        # --- 1. COMPACT DYNAMIC MATCHES SHOWCASE ---
        st.write("<br>", unsafe_allow_html=True)
        st.markdown(f"##### 🥇 Top {num_peers} closest matches:")
        
        cols = st.columns(3)
        for i, (_, row) in enumerate(similar_df.iterrows()):
            p_time = row['best_time']
            time_diff = p_time - target_best_time
            country = row.get('Country', 'Unknown')
            slope = safe_get(row, 'progression_slope', safe_get(row, 'slope', 0.0))
            cons = safe_get(row, 'consistency_score', 0)
            
            delta_bg = "rgba(248, 113, 113, 0.15)" if time_diff > 0 else "rgba(74, 222, 128, 0.15)"
            delta_col = "#F87171" if time_diff > 0 else "#4ADE80"
            slope_col = "#4ADE80" if slope < 0 else "#F87171"
            
            card_html = (
                f"<div style='border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: rgba(255,255,255,0.03);'>"
                f"<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;'>{row['Swimmer']}</div>"
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>"
                
                f"<div><div style='font-size: 0.75rem; color: #A0AEC0; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;'>Best Time</div>"
                f"<div style='font-size: 1.8rem; font-weight: 800; color: #FFFFFF;'>{p_time:.2f}<span style='font-size: 1rem; color: #A0AEC0; font-weight: 600;'>s</span></div></div>"
                
                f"<div style='text-align: right;'><div style='font-size: 0.75rem; color: #A0AEC0; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;'>vs Target</div>"
                f"<div style='font-size: 0.85rem; font-weight: 700; color: {delta_col}; background: {delta_bg}; padding: 4px 10px; border-radius: 4px;'>{time_diff:+.2f}s</div></div>"
                f"</div>"
                
                f"<div style='font-size: 0.85rem; color: #D1D5DB; margin-bottom: 16px; display: flex; align-items: center; gap: 6px;'>"
                f"📍 <span style='background: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 4px;'>{country}</span>"
                f"</div>"
                f"<div style='display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem; color: #A0AEC0; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;'>"
                f"<div style='display: flex; justify-content: space-between;'><span>📈 Trajectory:</span><span style='color: {slope_col}; font-weight: 700;'>{slope:.3f}</span></div>"
                f"<div style='display: flex; justify-content: space-between;'><span>🎯 Consistency:</span><span style='color: #FFFFFF; font-weight: 700;'>{cons:.2f}</span></div>"
                f"</div>"
                f"</div>"
            )
            
            with cols[i % 3]: 
                st.markdown(card_html, unsafe_allow_html=True)

        # --- 2. INTERACTIVE GLOBAL MAP ---
        st.write("---")
        st.write("### 🌍 Global Distribution of Peers")
        
        country_coords = {
            "United States": {"lat": 38, "lon": -97}, "Australia": {"lat": -25, "lon": 133},
            "China": {"lat": 35, "lon": 105}, "United Kingdom": {"lat": 55, "lon": -3},
            "Russia": {"lat": 60, "lon": 90}, "Italy": {"lat": 41, "lon": 12},
            "France": {"lat": 46, "lon": 2}, "Japan": {"lat": 36, "lon": 138},
            "South Korea": {"lat": 35, "lon": 127}, "Canada": {"lat": 56, "lon": -106},
            "Germany": {"lat": 51, "lon": 10}, "Brazil": {"lat": -14, "lon": -51},
            "South Africa": {"lat": -30, "lon": 25}, "Netherlands": {"lat": 52, "lon": 5},
            "Hungary": {"lat": 47, "lon": 19}, "Sweden": {"lat": 60, "lon": 18},
            "Spain": {"lat": 40, "lon": -4}, "Iran": {"lat": 32, "lon": 53},
            "Poland": {"lat": 51, "lon": 19}, "Switzerland": {"lat": 46, "lon": 8},
            "New Zealand": {"lat": -40, "lon": 174}, "Romania": {"lat": 45, "lon": 25},
            "Ireland": {"lat": 53, "lon": -8}, "Greece": {"lat": 39, "lon": 22},
            "Croatia": {"lat": 45, "lon": 15}, "Egypt": {"lat": 26, "lon": 30},
            "Mozambique": {"lat": -18, "lon": 35}
        }
        
        country_mapper = {
            "People's Republic of China": "China", "Great Britain": "United Kingdom",
            "United States of America": "United States", "Republic of Korea": "South Korea",
            "Russian Federation": "Russia", "Islamic Republic of Iran": "Iran"
        }
        
        map_df = similar_df.copy()
        map_df['Plotly_Country'] = map_df['Country'].replace(country_mapper)
        
        map_grouped = map_df.groupby('Plotly_Country').agg(
            Athletes=('Swimmer', lambda x: '<br>• ' + '<br>• '.join(x)),
            Count=('Swimmer', 'count'),
            Original_Country=('Country', 'first')
        ).reset_index()
        
        min_c = map_grouped['Count'].min()
        max_c = map_grouped['Count'].max()
        range_c = [min_c, max_c] if min_c != max_c else [0, max_c]
        
        col_list, col_map = st.columns([1, 2.5], gap="large")

        with col_list:
            st.write("#### 📍 Focus Country")
            
            display_df = map_grouped[['Plotly_Country', 'Count']].rename(columns={'Plotly_Country': 'Country', 'Count': 'Peers'})
            display_df = display_df.sort_values('Peers', ascending=False).reset_index(drop=True)
            
            # --- Dynamic Button Grid (Replicating Image UI) ---
            btn_cols = st.columns(2)
            for i, row in display_df.iterrows():
                country_name = row['Country']
                count = row['Peers']
                with btn_cols[i % 2]:
                    # Type="primary" provides the thematic background color automatically
                    if st.button(f"{country_name} ({count})", key=f"btn_{country_name}", use_container_width=True, type="primary"):
                        st.session_state.map_focus = country_name
            
# --- THE FIX IS HERE ---
            if st.button("Reset Map View", use_container_width=True, type="primary"):
                st.session_state.map_focus = None
                st.rerun() # Forces the map to instantly zoom back out
                
            focus = st.session_state.get('map_focus', None)

            # --- SCOUTING INSIGHT ---
            st.write("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("#### 💡 Scouting Insight")
                if not display_df.empty:
                    top_country = display_df.iloc[0]['Country']
                    st.info(f"The highest density of competitive peers is in **{top_country}**.\n\nThis suggests their training systems are producing the most direct rivals for **{name}**.")
                else:
                    st.info("Not enough data to generate scouting insights.")

        with col_map:
            color_scale = [[0.0, "#FFD166"], [1.0, "#E63946"]]
            
            fig_map = px.choropleth(
                map_grouped, locations="Plotly_Country", locationmode="country names",
                color="Count", color_continuous_scale=color_scale, range_color=range_c,
                custom_data=["Original_Country", "Athletes", "Count"]
            )
            
            fig_map.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Total Peers: %{customdata[2]}<br>%{customdata[1]}<extra></extra>")
            
            if focus and focus in country_coords:
                geo_center = dict(lat=country_coords[focus]['lat'], lon=country_coords[focus]['lon'])
                projection_scale = 3.5 
            else:
                geo_center = dict(lat=20, lon=0) 
                projection_scale = 1.0 

            fig_map.update_layout(
                geo=dict(
                    projection_type='natural earth', 
                    center=geo_center,
                    projection_scale=projection_scale, showframe=False, showcoastlines=True,
                    coastlinecolor="rgba(255, 255, 255, 0.1)", bgcolor='rgba(0,0,0,0)', 
                    lakecolor='rgba(0,0,0,0)', landcolor='rgba(255, 255, 255, 0.05)',
                    showcountries=True, countrycolor="rgba(255, 255, 255, 0.1)"
                ),
                margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False, height=450
            )
            st.plotly_chart(fig_map, use_container_width=True)

        st.write("---")
        
        # --- 3. MULTI-SWIMMER PROGRESSION GRAPH ---
        c_head, c_slider = st.columns([1, 1], gap="large")
        with c_head:
            st.write("### 📈 Career Trajectory Comparison")
            
        with c_slider:
            # Shifted Graph Timeframe controls to be directly next to the graph
            min_year = int(event_df['Year'].min()) if not event_df.empty else 2000
            max_year = int(event_df['Year'].max()) if not event_df.empty else 2024
            
            selected_years = st.slider(
                "**🗓️ Graph Timeframe (Years)**",
                min_value=min_year, 
                max_value=max_year,
                value=(min_year, max_year),
                help="Adjust the years to instantly filter the trajectory chart below."
            )
        
        st.info("""
        **How to read this chart:**
        * **The Axes:** The bottom axis shows the progression of years. The side axis shows the race time. **Note that the chart is visually inverted:** higher up on the graph means a *faster* time.
        * **The Lines:** The thick solid blue line is your target athlete. The dotted lines are the selected peers.
        * **The Trend:** A line sloping upwards (getting faster) means the swimmer is dropping time year-over-year. A flat line indicates a plateau.
        """)
        
        compare_group = [name] + peer_names
        
        # DataFrame filtered dynamically by the new slider position
        history_df = event_df[
            (event_df['Swimmer'].isin(compare_group)) &
            (event_df['Year'] >= selected_years[0]) & 
            (event_df['Year'] <= selected_years[1])
        ].copy()
        
        if not history_df.empty:
            yearly_progression = history_df.groupby(['Year', 'Swimmer'])['Time_Sec'].min().reset_index()
            
            fig_line = px.line(
                yearly_progression, x='Year', y='Time_Sec', 
                color='Swimmer', markers=True, template="plotly_white"
            )
            for trace in fig_line.data:
                if trace.name == name:
                    trace.line.width = 5
                    trace.line.color = '#1E90FF'
                else:
                    trace.line.dash = 'dot'
                    trace.line.width = 2
                    
            fig_line.update_layout(
                yaxis_title="Time (Seconds) - Higher is Faster", xaxis_title="Year",
                hovermode="x unified", xaxis=dict(dtick=1)
            )
            fig_line.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_line, use_container_width=True)
            
        st.write("---")
        
        # --- 4. HEAD-TO-HEAD RADAR & COACHING ---
        st.write("### ⚔️ Head-to-Head Deep Dive")

        with st.expander("📚 How to read these radar benchmarks (Coach's Guide)", expanded=False):
            st.markdown("""
            **Understanding the "Elite 5" Radar Index:**
            *This 0-100 indexing system normalizes raw race data, allowing coaches to visually compare completely different variables (like speed vs. variance) on a single chart.*

            * ⚡ **Peak Speed (Maximal Output):** Based on the athlete's lifetime Personal Best (PB). A score of **100** represents the fastest absolute time within this specific generated peer group.
            * 🎯 **Current Form (Peak Proximity):** The actual time gap between their most recent recorded race and their lifetime PB. A score of **100** indicates the athlete is currently racing at—or surpassing—their historical peak capability.
            * 📈 **Momentum (Progression Trajectory):** Derived from the linear regression slope of their seasonal bests. A score of **100** means the athlete is rapidly and consistently dropping times year-over-year.
            * ⏱️ **Consistency (Variance Control):** Calculated using the standard deviation (σ) of the athlete's career times. A score of **100** indicates extremely low variance (machine-like pacing and reliability across multiple races).
            * 🌍 **Global Threat (Elite Gap):** The exact time gap between the athlete's PB and the historical Global Top 8 Finalist cutoff. A score of **100** means the athlete is currently swimming at true Olympic Finalist pace.
            """)
            
        st.write("##### 🔍 Select a Peer to Analyze:")
        
        compare_name = st.radio(
            "Peer Selection", 
            options=peer_names, 
            horizontal=True, 
            label_visibility="collapsed"
        )
        compare_stats = similar_df[similar_df['Swimmer'] == compare_name].iloc[0]
        
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
        
        def fmt_d(val1, val2):
            diff = val2 - val1
            return f"({diff:+.2f})" if diff != 0 else "(Equal)"

        st.write("#### 🥊 Tale of the Tape")
        st.markdown(f"""
        | Metric | {name} | {compare_name} |
        | :--- | :--- | :--- |
        | **Peak Speed (Best Time)** | **{t_bt:.2f}s** | {c_bt:.2f}s {fmt_d(t_bt, c_bt)} |
        | **Current Form (Off Peak)**| **{t_form:.2f}s** | {c_form:.2f}s {fmt_d(t_form, c_form)} |
        | **Momentum (Trajectory)** | **{t_slope:.3f}** | {c_slope:.3f} {fmt_d(t_slope, c_slope)} |
        | **Consistency (Std Dev)** | **{t_cons:.2f}** | {c_cons:.2f} {fmt_d(t_cons, c_cons)} |
        | **Threat (Gap to Top 8)** | **{t_threat:.2f}s** | {c_threat:.2f}s {fmt_d(t_threat, c_threat)} |
        """)

        st.write("") 

        st.info("""
        **How to read the Radar Chart (Head-to-Head Profile):** This chart maps five key career attributes on a scale of 0 to 100 relative to the peer group. 
        * **The Shape:** The polygon maps the athlete's **Peak Speed**, **Current Form**, **Momentum**, **Consistency**, and **Global Threat**. 
        * **The Size:** The further outward a point stretches toward the edge, the stronger that trait is. A larger overall area indicates a more dominant statistical profile.
        """)

        col_radar, col_coach = st.columns([1.5, 1], gap="large")
        
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
            
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=400, margin=dict(l=50, r=50, t=20, b=20), showlegend=True)
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with col_coach:
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