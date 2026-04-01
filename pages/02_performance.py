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
    
    # --- 1. METRIC CALCULATIONS ---
    gap = stats.get('latest_gap_to_top10', 0.0)
    dist_pb = stats.get('distance_from_peak', 0.0)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Career Stage", stats.get('career_stage', 'N/A'))
    col2.metric("Years Competing", int(stats.get('years_competing', 0)))
    col3.metric("Gap to Top 10", f"{gap:.2f}s")
    col4.metric("Dist. from PB", f"{dist_pb:.2f}s")

    st.write("---")
    
    # --- 2. ADVANCED BENCHMARK ENGINE (TOP 8) ---
    st.write(f"### Contextual Breakdown: {name} vs. The World")
    
    # NEW: Streamlit Multi-select for dynamic country comparison
    all_countries = sorted(event_df['Country'].dropna().unique().tolist())
    default_countries = [athlete_country] if athlete_country in all_countries else []
    
    selected_countries = st.multiselect(
        "🌍 Add Countries to Compare (Top 8 Avg):",
        options=all_countries,
        default=default_countries,
        help="Select multiple countries to overlay their Elite Top 8 averages. You can also remove the home country."
    )
    
    # A. Global Top 8 Average (3-Year Smoothing)
    global_yearly = event_df.groupby('Year')['Time_Sec'].apply(
        lambda x: x.nsmallest(8).mean()
    ).reset_index(name='global_avg')
    global_yearly['global_benchmark'] = global_yearly['global_avg'].rolling(window=3, min_periods=1).mean()
    
    # B. Dynamic Country Top 8 Averages
    country_dataframes = {}
    for country in selected_countries:
        country_df = event_df[event_df['Country'] == country]
        if not country_df.empty:
            country_yearly = country_df.groupby('Year')['Time_Sec'].apply(
                lambda x: x.nsmallest(8).mean() if len(x) >= 1 else x.mean()
            ).reset_index(name='country_avg')
            country_yearly['benchmark'] = country_yearly['country_avg'].rolling(window=3, min_periods=1).mean()
            country_dataframes[country] = country_yearly

    # C. Swimmer's Yearly Best
    swimmer_yearly = history.groupby('Year')['Time_Sec'].min().reset_index(name='swimmer_best')
    
    # Merge Global with Athlete for base plot dataframe
    plot_df = swimmer_yearly.merge(global_yearly[['Year', 'global_benchmark']], on='Year', how='left')
    
    # --- 3. THE VISUALIZATION ---
    if not plot_df.empty:
        fig = go.Figure()
        
        # 1. Global Benchmark Line (Red, thick, semi-transparent band)
        fig.add_trace(go.Scatter(
            x=plot_df['Year'], y=plot_df['global_benchmark'],
            mode='lines', name='Global Top 8 Avg',
            line=dict(color='rgba(252, 129, 129, 0.4)', width=8),
            hovertemplate="Global Elite: %{y:.2f}s<extra></extra>"
        ))
        
        # 2. Dynamic Country Lines
        # A list of distinct colors so multiple countries don't blend together
        color_palette = ['#4FD1C5', '#F6E05E', '#D6BCFA', '#F6AD55', '#68D391', '#F687B3']
        
        for idx, country in enumerate(selected_countries):
            if country in country_dataframes:
                c_df = country_dataframes[country]
                line_color = color_palette[idx % len(color_palette)] # Cycle through colors
                
                fig.add_trace(go.Scatter(
                    x=c_df['Year'], y=c_df['benchmark'],
                    mode='lines+markers', name=f'{country} Top 8 Avg',
                    line=dict(color=line_color, dash='dot', width=3),
                    marker=dict(size=6, color=line_color),
                    hovertemplate=f"{country} Elite: %{{y:.2f}}s<extra></extra>"
                ))
        
        # 3. Athlete Best Time Line (Thick Blue)
        fig.add_trace(go.Scatter(
            x=plot_df['Year'], y=plot_df['swimmer_best'],
            mode='lines+markers', name=f'{name} Best',
            line=dict(color='#1E90FF', width=4),
            marker=dict(size=10, color='white', line=dict(width=2, color='#1E90FF')),
            hovertemplate="Athlete: %{y:.2f}s<extra></extra>"
        ))
        
        fig.update_yaxes(autorange="reversed") # Faster is UP
        fig.update_layout(
            title=f"Career Context: {name} vs Regional Elite Averages",
            xaxis_title="Year",
            yaxis_title="Time (Seconds)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_dark"
        )
        
        fig.add_annotation(
            x=plot_df['Year'].iloc[0], y=plot_df['global_benchmark'].iloc[0],
            text="🏆 Global Top 8 Avg", showarrow=False, font=dict(color="#FC8181"),
            yshift=15
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data to generate Top 8 comparison benchmarks.")