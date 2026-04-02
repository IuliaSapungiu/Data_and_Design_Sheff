import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from features.comparator import find_similar_swimmers
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

    with st.expander("📚 How to read these benchmarks (Coach's Guide)", expanded=False):
        st.markdown("""
        ### Understanding the "Elite 5" Radar Metrics:
        * **Peak Speed:** The athlete's all-time fastest performance. Score of **100** = fastest among peers.
        * **Current Form:** How close their recent season is to their PB. Score of **100** = at absolute peak.
        * **Momentum:** Progression slope. High scores = rapidly dropping time.
        * **Consistency:** Standard deviation. **100** = machine-like precision.
        * **Global Threat:** Gap to Global Top 8 final average.
        """)

    st.write("---")
    st.write(f"### Finding Peers for: **{name}**")
    
    # --- UNIFIED CONTROL PANEL ---
    with st.container(border=True):
        st.write("#### ⚙️ Match Engine Settings")
        
        # Step 1: Scope
        scope = st.radio(
            "**Step 1: Comparison Scope** (Select the talent pool to pull from)",
            ["🌍 Global (All Available)", f"📍 National ({athlete_country} Only)"],
            horizontal=True
        )
        
        # --- RUN ENGINE IN THE BACKGROUND ---
        # We must filter event_df first, then use those swimmers to filter features_df
        if "National" in scope:
            working_event_df = event_df[event_df['Country'] == athlete_country].copy()
            national_swimmers = working_event_df['Swimmer'].unique()
            working_features_df = features_df[features_df['Swimmer'].isin(national_swimmers)].copy()
        else:
            working_features_df = features_df.copy()
            working_event_df = event_df.copy()

        # Run the matching algorithm
        similar_df_full, target_best_time, target_event = find_similar_swimmers(target, working_features_df, working_event_df, max_n=10)
        
        st.caption(f"**Primary Event Detected for Matching:** `{target_event}`")

        # Step 2 & 3: Layout in Columns if Engine succeeds
        if not similar_df_full.empty:
            st.write("---")
            c1, c2 = st.columns([1, 2], gap="large")
            
            with c1:
                max_available = len(similar_df_full)
                num_peers = st.selectbox(
                    "**Step 2: Matches to Display**", 
                    options=list(range(1, max_available + 1)), 
                    index=min(2, max_available - 1)
                )
            
            with c2:
                all_years = event_df['Year'].unique()
                min_y, max_y = int(min(all_years)), int(max(all_years))
                selected_years = st.slider(
                    "**Step 3: Graph Timeframe** (Filter eras to remove gaps)",
                    min_value=min_y, max_value=max_y, 
                    value=(max(min_y, max_y - 15), max_y)
                )
        else:
            st.error(f"Dataset Error: Not enough data to find peers for {name} in the selected scope.")

    # Only render the rest of the page if the engine found peers
    if not similar_df_full.empty:
        similar_df = similar_df_full.head(num_peers)
        peer_names = similar_df['Swimmer'].tolist()
        
        # --- 1. DYNAMIC MATCHES SHOWCASE ---
        st.write("<br>", unsafe_allow_html=True)
        st.markdown(f"##### 🥇 Top {num_peers} closest matches:")
        cols = st.columns(3)
        for i, (_, row) in enumerate(similar_df.iterrows()):
            with cols[i % 3]: 
                with st.container(border=True):
                    st.write(f"#### {row['Swimmer']}")
                    p_time = row['best_time']
                    time_diff = p_time - target_best_time
                    st.metric("Best Time vs Target", f"{p_time:.2f}s", delta=f"{time_diff:+.2f}s", delta_color="inverse")
                    st.markdown(f"**Country:** `{row.get('Country', 'Unknown')}`")
                    st.markdown(f"**Trajectory:** `{row.get('progression_slope', row.get('slope', 0.0)):.3f}`")
                    st.markdown(f"**Consistency:** `{row.get('consistency_score', 0):.2f}`")

        # --- 2. INTERACTIVE 3D GLOBAL MAP ---
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
        
        def get_gradient_color(val):
            v_min, v_max = range_c[0], range_c[1]
            if v_max == v_min: return "#E63946" 
            ratio = max(0.0, min(1.0, (val - v_min) / (v_max - v_min)))
            r = int(255 + ratio * (230 - 255))
            g = int(209 + ratio * (57 - 209))
            b = int(102 + ratio * (70 - 102))
            return f"#{r:02x}{g:02x}{b:02x}"

        col_list, col_map = st.columns([1, 2.5], gap="large")

        with col_list:
            st.write("#### 📍 Focus Country")
            st.caption("Click a colored row to fly to that country. Click again to reset.")
            
            display_df = map_grouped[['Plotly_Country', 'Count']].rename(columns={'Plotly_Country': 'Country', 'Count': 'Peers'})
            display_df = display_df.sort_values('Peers', ascending=False).reset_index(drop=True)
            
            def style_rows(row):
                bg = get_gradient_color(row['Peers'])
                return [f"background-color: {bg}; color: #1E1E1E; font-weight: 700; border-bottom: 2px solid #0E1117;"] * len(row)
            
            styled_df = display_df.style.apply(style_rows, axis=1)
            
            selection = st.dataframe(
                styled_df, hide_index=True, on_select="rerun", 
                selection_mode="single-row", use_container_width=True, height=350
            )
            
            focus = None
            if len(selection.selection.rows) > 0:
                idx = selection.selection.rows[0]
                focus = display_df.iloc[idx]['Country']

        with col_map:
            color_scale = [[0.0, "#FFD166"], [1.0, "#E63946"]]
            
            fig_map = px.choropleth(
                map_grouped, locations="Plotly_Country", locationmode="country names",
                color="Count", color_continuous_scale=color_scale, range_color=range_c,
                custom_data=["Original_Country", "Athletes", "Count"]
            )
            
            fig_map.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Total Peers: %{customdata[2]}<br>%{customdata[1]}<extra></extra>")
            
            if focus and focus in country_coords:
                geo_rotation = dict(lat=country_coords[focus]['lat'], lon=country_coords[focus]['lon'], roll=0)
                projection_scale = 1.5 
            else:
                geo_rotation = dict(lat=20, lon=0, roll=0) 
                projection_scale = 1 

            fig_map.update_layout(
                geo=dict(
                    projection_type='orthographic', projection_rotation=geo_rotation,
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
        st.write("### 📈 Career Trajectory Comparison")
        
        compare_group = [name] + peer_names
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
                yaxis_title="Time (Seconds) - Lower is Faster", xaxis_title="Year",
                hovermode="x unified", xaxis=dict(dtick=1)
            )
            fig_line.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_line, use_container_width=True)
            
        st.write("---")
        
        # --- 4. HEAD-TO-HEAD RADAR & COACHING ---
        st.write("### ⚔️ Head-to-Head Deep Dive")
        compare_name = st.selectbox("Select a peer to analyze 1-on-1 against your target:", peer_names)
        compare_stats = similar_df[similar_df['Swimmer'] == compare_name].iloc[0]
        
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
            st.plotly_chart(fig_radar, use_container_width=True)

        st.write("### 📋 Coach's Action Plan")
        with st.container(border=True):
            if t_bt < c_bt and t_cons > c_cons + 0.3:
                st.warning(f"**💡 The Glass Cannon:** {name} has superior speed, but {compare_name} is significantly more consistent.")
            elif t_slope < c_slope - 0.1:
                st.success(f"**🚀 Closing the Gap:** {name} has vastly superior Momentum right now.")
            else:
                st.success(f"**✅ Stable Matchup:** Victory depends on marginal gains in turns and transitions.")