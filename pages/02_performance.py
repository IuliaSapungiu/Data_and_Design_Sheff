import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from shared_ui import render_navbar

render_navbar()

st.title("Performance & Context")

if 'swimmer_stats' not in st.session_state:
    st.warning("Please go back to the Control Room and click 'Process Analytics' first.")
else:
    stats = st.session_state['swimmer_stats']
    name = st.session_state['swimmer_name']
    history = st.session_state['swimmer_history']
    event_df = st.session_state['event_df'] 
    
    athlete_country = stats.get('country', 'Unknown')
    
    st.write(f"### Current Standing: {name} ({athlete_country})")
    
    # --- 1. BENCHMARK EVALUATION LOGIC (Your Logic) ---
    gap = stats.get('latest_gap_to_top10', 0.0) 
    if gap <= 0:
        gap_eval = "👑 Elite / Podium Pace"
        gap_text = f"{abs(gap):.2f}s (Top 8)"
    elif gap <= 0.5:
        gap_eval = "🚀 Finalist Pace"
        gap_text = f"+{gap:.2f}s (Slower)"
    elif gap <= 1.5:
        gap_eval = "🏊 Competitive"
        gap_text = f"+{gap:.2f}s (Slower)"
    else:
        gap_eval = "📈 Developing"
        gap_text = f"+{gap:.2f}s (Slower)"

    dist_pb = stats.get('distance_from_peak', 0.0)
    if dist_pb == 0.0:
        pb_eval = "🔥 Absolute Peak"
    elif dist_pb <= 0.3:
        pb_eval = "⚡ Near Peak"
    else:
        pb_eval = "📉 Off Peak"

    # --- 2. DISPLAY METRICS (Your Layout) ---
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Career Stage", stats.get('career_stage', 'N/A'), help="Based on their age in their most recent active year: Early (<20), Peak (20-26), Decline (>26).")
    col2.metric("Years Competing", int(stats.get('years_competing', 0)), help="Total distinct years this athlete recorded a time.")
    
    col3.metric(
        label="Gap to Champ Pace", 
        value=gap_text,
        delta=gap_eval,
        delta_color="off",
        help="Difference between their latest best time and the Top 8 Average (Championship Pace) for that year."
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
        * **Gap to Champ Pace:** We take the average time of the Top 8 globally to find the 'Championship Pace'. If the athlete is beating this time (`<= 0s`), they are on **Elite / Podium Pace**. Being within 0.5s is considered **Finalist Pace**.
        * **Distance from PB:** If the distance is `0.00s`, it means their most recent season was their absolute fastest ever (**Absolute Peak**).
        """)

    st.write("---")
    
    # --- 3. THE VISUALISATION: Swimmer vs. The World ---
    st.write("### Contextual Breakdown: Swimmer vs. The World")
    
    # NEW: Tarun's Streamlit Multi-select for dynamic country comparison
    all_countries = sorted(event_df['Country'].dropna().unique().tolist())
    default_countries = [athlete_country] if athlete_country in all_countries else []
    
    selected_countries = st.multiselect(
        "🌍 Add Countries to Compare (Top 8 Avg):",
        options=all_countries,
        default=default_countries,
        help="Select multiple countries to overlay their Elite Top 8 averages. You can also remove the home country."
    )
    
    # A. Global Top 8 Average (Your Champ Pace Logic)
    global_yearly = event_df.groupby('Year')['Time_Sec'].agg(
        championship_pace=lambda x: x.nsmallest(8).mean() if len(x) >= 8 else x.mean()
    ).reset_index()

    # B. Dynamic Country Top 8 Averages (Tarun's Logic)
    country_dataframes = {}
    for country in selected_countries:
        country_df = event_df[event_df['Country'] == country]
        if not country_df.empty:
            country_yearly = country_df.groupby('Year')['Time_Sec'].apply(
                lambda x: x.nsmallest(8).mean() if len(x) >= 1 else x.mean()
            ).reset_index(name='country_avg')
            country_dataframes[country] = country_yearly

    # C. Swimmer's Yearly Best
    swimmer_yearly = history.groupby('Year')['Time_Sec'].min().reset_index(name='Swimmer_Time')
    
    # Merge Global with Athlete for base plot dataframe
    plot_df = pd.merge(global_yearly, swimmer_yearly, on='Year', how='inner')

    # --- 4. RENDER THE GRAPH ---
    if not plot_df.empty:
        fig = go.Figure()
        
        # Your logic: Dynamically calculate the ceiling so we don't ruin the scale
        fastest_time = min(plot_df['championship_pace'].min(), plot_df['Swimmer_Time'].min())
        ceiling_time = fastest_time - 1.0 # Just 1 second faster than the best time on the chart
        
        # Add the invisible ceiling (Your feature)
        fig.add_trace(go.Scatter(
            x=plot_df['Year'], y=[ceiling_time]*len(plot_df),
            mode='lines', line=dict(color='rgba(0,0,0,0)'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # Draw the Championship Pace line and fill the space between it and the invisible ceiling (Your Feature)
        fig.add_trace(go.Scatter(
            x=plot_df['Year'], y=plot_df['championship_pace'], 
            mode='lines+markers', name='Top 8 Champ Pace',
            line=dict(color='red', dash='dash', width=2),
            fill='tonexty', fillcolor='rgba(255, 215, 0, 0.15)', # Faint Gold Shading
            hovertemplate="Global Elite: %{y:.2f}s<extra></extra>"
        ))
        
        # Add Tarun's Dynamic Country Lines over the top
        color_palette = ['#4FD1C5', '#F6E05E', '#D6BCFA', '#F6AD55', '#68D391', '#F687B3']
        for idx, country in enumerate(selected_countries):
            if country in country_dataframes:
                c_df = country_dataframes[country]
                line_color = color_palette[idx % len(color_palette)] 
                
                fig.add_trace(go.Scatter(
                    x=c_df['Year'], y=c_df['country_avg'],
                    mode='lines+markers', name=f'{country} Top 8 Avg',
                    line=dict(color=line_color, dash='dot', width=2),
                    marker=dict(size=6, color=line_color),
                    hovertemplate=f"{country} Elite: %{{y:.2f}}s<extra></extra>"
                ))
                                 
        # Add our Swimmer's line on top (Combined Styling)
        fig.add_trace(go.Scatter(
            x=plot_df['Year'], y=plot_df['Swimmer_Time'], 
            mode='lines+markers', name=f'{name} Best Time',
            line=dict(color='#1E90FF', width=4), # Tarun's Thicker Blue Line
            marker=dict(size=10, color='white', line=dict(width=2, color='#1E90FF')),
            hovertemplate="Athlete: %{y:.2f}s<extra></extra>"
        ))
        
        fig.update_yaxes(autorange="reversed") # Faster is UP
        fig.update_layout(
            title=f"Career Context: {name} vs Global & Regional Elite Averages",
            xaxis_title="Year",
            yaxis_title="Time (Seconds) - Higher is Faster",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) # Tarun's horizontal legend
        )
        
        # Your Annotation to explain the gold zone
        fig.add_annotation(
            x=plot_df['Year'].iloc[0], y=plot_df['championship_pace'].iloc[0] - 0.2,
            text="🏆 Elite Zone", showarrow=False, font=dict(color="goldenrod")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data to generate Top 8 comparison benchmarks.")