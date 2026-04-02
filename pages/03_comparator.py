import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from features.comparator import find_similar_swimmers
from features.progression import build_progression_features
from features.performance import build_performance_features
from shared_ui import render_navbar

# 1. Page Config and Navbar
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
    
    # Safely extract country
    athlete_country = target.get('country', target.get('Country', 'Unknown'))

    st.write(f"### Finding Peers for: **{name}**")
    
    # --- COMPACT UNIFIED CONTROL PANEL ---
    with st.container(border=True):
        st.markdown("#### ⚙️ Match Engine Settings")
        
        c1, c2, c3 = st.columns([1.2, 1, 2], gap="medium")
        
        with c1:
            scope = st.radio(
                "**1️⃣ Comparison Scope**",
                ["🌍 Global (All)", f"📍 National ({athlete_country})"],
                help="Global uses the full dataset. National restricts peers exclusively to the athlete's home country."
            )
            
        # --- 1. DEFINE TIMEFRAME SLIDER FIRST ---
        with c3:
            all_years = event_df['Year'].unique()
            min_y, max_y = int(min(all_years)), int(max(all_years))
            selected_years = st.slider(
                "**3️⃣ Evaluation Timeframe**",
                min_value=min_y, max_value=max_y, 
                value=(max(min_y, max_y - 15), max_y),
                help="Filter years to focus on a specific era. This dynamically recalculates peer matches and updates the tiles!"
            )
            
        # --- 2. APPLY TIMEFRAME FILTER AND DYNAMICALLY REBUILD FEATURES ---
        working_event_df = event_df[(event_df['Year'] >= selected_years[0]) & (event_df['Year'] <= selected_years[1])].copy()
        
        if "National" in scope:
            working_event_df = working_event_df[working_event_df['Country'] == athlete_country]
            
        # Helper function to natively recalculate stats for the chosen timeframe
        @st.cache_data(show_spinner=False)
        def generate_tf_features(df_in):
            if df_in.empty: return pd.DataFrame()
            prog = build_progression_features(df_in)
            perf = build_performance_features(df_in)
            if 'FINA ID' in prog.columns and 'FINA ID' in perf.columns:
                return pd.merge(prog, perf, on='FINA ID')
            return pd.merge(prog, perf, on='Swimmer')

        with st.spinner(f"Recalculating analytics for {selected_years[0]}-{selected_years[1]} era..."):
            working_features_df = generate_tf_features(working_event_df)
        
        # Ensure target athlete exists in this timeframe before running comparator
        if not working_features_df.empty and name in working_features_df['Swimmer'].values:
            target_data = working_features_df[working_features_df['Swimmer'] == name]
            target_copy = target_data.iloc[0].to_dict()
            target_copy['country'] = athlete_country
            
            similar_df_full, target_best_time, target_event = find_similar_swimmers(target_copy, working_features_df, working_event_df, max_n=20)
        else:
            similar_df_full = pd.DataFrame()

        # --- 3. RENDER MATCH SELECTBOX BASED ON ENGINE RESULTS ---
        if not similar_df_full.empty:
            with c2:
                max_available = len(similar_df_full)
                num_peers = st.selectbox(
                    "**2️⃣ Matches to Display**", 
                    options=list(range(1, max_available + 1)), 
                    index=min(9, max_available - 1), # Defaults to 10 if available
                    help="Select how many similar athletes to show in the cards and graph."
                )
                
            st.caption(f"🎯 **Target Event:** `{target_event}` | The AI is comparing performances strictly within the {selected_years[0]}-{selected_years[1]} timeframe.")
        else:
            with c2:
                st.selectbox("**2️⃣ Matches to Display**", options=[0])
            st.error(f"⚠️ {name} has insufficient data in the {selected_years[0]}-{selected_years[1]} timeframe to generate matches.")

    # Only render the rest of the page if the engine found peers
    if not similar_df_full.empty:
        similar_df = similar_df_full.head(num_peers)
        peer_names = similar_df['Swimmer'].tolist()
        
        # --- 1. COMPACT DYNAMIC MATCHES SHOWCASE ---
        st.write("<br>", unsafe_allow_html=True)
        
        explanation_text = (
            "**How to read these peer cards:**\n\n"
            "⏱️ **Time Delta (e.g., +0.13s in Red/Green):** The difference between this peer's best time and your athlete's best time. "
            "**Red** means this peer is slower (+). **Green** means this peer is faster (-).\n\n"
            "📈 **Trajectory:** Progression slope over time. A **negative value (Green)** means they are actively dropping time year-over-year. "
            "A **positive value (Red)** means their times are slowing down or plateauing.\n\n"
            "🎯 **Consistency:** Standard deviation of their race times. A **lower number** means they are highly predictable and reliable. "
            "A **higher number** indicates erratic, boom-or-bust performances."
        )
        st.markdown(f"##### 🥇 Top {num_peers} closest matches (Filtered by {selected_years[0]}-{selected_years[1]}):", help=explanation_text)
        
        cols = st.columns(3)
        for i, (_, row) in enumerate(similar_df.iterrows()):
            p_time = row['best_time']
            time_diff = p_time - target_best_time
            country = row.get('Country', 'Unknown')
            slope = row.get('progression_slope', row.get('slope', 0.0))
            cons = row.get('consistency_score', 0)
            
            delta_bg = "rgba(248, 113, 113, 0.15)" if time_diff > 0 else "rgba(74, 222, 128, 0.15)"
            delta_col = "#F87171" if time_diff > 0 else "#4ADE80"
            slope_col = "#4ADE80" if slope < 0 else "#F87171"
            
            card_html = (
                f"<div style='border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: rgba(255,255,255,0.03);'>"
                f"<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;'>{row['Swimmer']}</div>"
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>"
                f"<div style='font-size: 1.8rem; font-weight: 800; color: #FFFFFF;'>{p_time:.2f}<span style='font-size: 1rem; color: #A0AEC0; font-weight: 600;'>s</span></div>"
                f"<div style='font-size: 0.85rem; font-weight: 700; color: {delta_col}; background: {delta_bg}; padding: 4px 10px; border-radius: 4px;'>{time_diff:+.2f}s</div>"
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

        # --- 2. INTERACTIVE 2D GLOBAL MAP ---
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
            "Ireland": {"lat": 53, "lon": -8}, "Greece": {"lat": 39, "lon": 22}
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
            
            tile_cols = st.columns(2)
            for idx, row in enumerate(display_df.itertuples()):
                c_name = row.Country
                c_count = row.Peers
                if tile_cols[idx % 2].button(f"{c_name}\n({c_count})", key=f"tile_{c_name}", use_container_width=True):
                    st.session_state['map_focus'] = c_name
                    
            if st.button("Reset Map View", use_container_width=True):
                st.session_state['map_focus'] = None

            st.write("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("#### 💡 Scouting Insight")
                if not display_df.empty:
                    top_country = display_df.iloc[0]['Country']
                    st.info(f"The highest density of competitive peers during this era is in **{top_country}**. This suggests their training systems are producing the most direct rivals for {name}.")
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
            
            focus = st.session_state.get('map_focus', None)
            
            if focus and focus in country_coords:
                geo_center = dict(lat=country_coords[focus]['lat'], lon=country_coords[focus]['lon'])
                projection_scale = 2.5 
            else:
                geo_center = dict(lat=20, lon=0) 
                projection_scale = 1.0 

            fig_map.update_layout(
                geo=dict(
                    projection_type='natural earth', 
                    center=geo_center,
                    projection_scale=projection_scale, 
                    showframe=False, showcoastlines=True,
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
        st.write("### 📈 Career Trajectory Comparison")
        
        compare_group = [name] + peer_names
        
        # Graph uses the working_event_df which is already filtered by the selected slider!
        history_df = working_event_df[working_event_df['Swimmer'].isin(compare_group)].copy()
        
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
                yaxis_title="Time (Seconds) - Lower is Faster", xaxis_title="Year",
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
        
        t_bt, c_bt = target_best_time, compare_stats['best_time']
        t_form, c_form = target_copy.get('distance_from_peak', 0.0), compare_stats.get('distance_from_peak', 0.0)
        t_slope = target_copy.get('progression_slope', 0.0)
        c_slope = compare_stats.get('progression_slope', 0.0)
        t_cons, c_cons = target_copy.get('consistency_score', 0.0), compare_stats.get('consistency_score', 0.0)
        t_threat, c_threat = target_copy.get('latest_gap_to_top10', 0.0), compare_stats.get('latest_gap_to_top10', 0.0)

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
            st.plotly_chart(fig_radar, use_container_width=True)

        st.write("### 📋 Coach's Action Plan")
        with st.container(border=True):
            if t_bt < c_bt and t_cons > c_cons + 0.3:
                st.warning(f"**💡 The Glass Cannon:** {name} has superior speed, but {compare_name} is significantly more consistent.")
            elif t_slope < c_slope - 0.1:
                st.success(f"**🚀 Closing the Gap:** {name} has vastly superior Momentum right now.")
            else:
                st.success(f"**✅ Stable Matchup:** Victory depends on marginal gains in turns and transitions.")