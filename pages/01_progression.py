import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import Holt
from shared_ui import render_navbar

render_navbar()
st.title("📈 Progression Analytics")

# Check if data exists in memory
if 'swimmer_stats' not in st.session_state:
    st.warning("Please go back to the Control Room (App) and click 'Process Analytics' first.")
else:
    stats = st.session_state['swimmer_stats']
    history = st.session_state['swimmer_history']
    name = st.session_state['swimmer_name']
    
    st.write(f"### Progression Profile: {name} ({st.session_state['event']})")
    
    # --- 1. BENCHMARK EVALUATION LOGIC ---
    # Progression Slope (Negative is better)
    slope = stats['progression_slope']
    if slope < -0.3: slope_eval = "🔥 Elite Trajectory"
    elif slope < -0.05: slope_eval = "📈 Improving"
    elif slope <= 0.05: slope_eval = "⚖️ Plateauing"
    else: slope_eval = "⚠️ Regressing"

    # Improvement Rate (Positive is better)
    rate = stats['rate_of_improvement']
    if rate > 0.4: rate_eval = "⚡ Rapid Paced"
    elif rate > 0.1: rate_eval = "📈 Steady Drop"
    elif rate >= -0.1: rate_eval = "⚖️ Stagnant"
    else: rate_eval = "⚠️ Slowing"
    
    # 2-Year Drop
    drop_2yr = stats['improvement_2yr']
    if drop_2yr > 0.5: drop_eval = "🔥 Huge Recent Gains"
    elif drop_2yr > 0: drop_eval = "📈 Upward Momentum"
    else: drop_eval = "🧊 Cold/Plateau"

    # Consistency (Lower is better)
    consistency = stats['consistency_score']
    if consistency < 0.3: cons_eval = "🎯 Machine-like"
    elif consistency < 0.8: cons_eval = "✅ Reliable"
    else: cons_eval = "⚠️ Highly Variable"

    # --- 2. DISPLAY METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        label="Progression Slope", 
        value=f"{slope:.3f}",
        delta=slope_eval,
        delta_color="off", 
        help="The overall career trendline using linear regression. A negative value means their times are dropping year over year."
    )
    
    col2.metric(
        label="Improvement Rate", 
        value=f"{rate:.3f} s/yr",
        delta=rate_eval,
        delta_color="off",
        help="The average number of seconds dropped per year from their first FINA race to their most recent."
    )
    
    col3.metric(
        label="2-Yr Drop", 
        value=f"{drop_2yr:.2f} s",
        delta=drop_eval,
        delta_color="off",
        help="The total time shaved off their personal best over the most recent two years of their career."
    )
    
    col4.metric(
        label="Consistency (Std Dev)", 
        value=f"{consistency:.2f}",
        delta=cons_eval,
        delta_color="off",
        help="The standard deviation of their best times over the last 3 years. Closer to 0 means highly stable."
    )
    
    # --- 3. THE COACH'S GUIDE (Collapsible) ---
    with st.expander("📚 How to read these benchmarks (Coach's Guide)"):
        st.markdown("""
        * **Progression Slope:** `< -0.3` is considered **Elite**. It shows aggressive, sustained long-term time dropping.
        * **Improvement Rate:** `> 0.4 s/yr` is considered **Rapid**. It means the athlete consistently shaves large chunks of time off annually.
        * **Consistency (Std Dev):** `< 0.3` is considered **Machine-like**. This indicates they swim almost the exact same time every single race, making them highly predictable for relays and medal contention.
        """)
    
    st.write("---")
    
    # --- 4. VISUALISATION: Career Timeline ---
    st.write("#### Career Timeline (Best Time per Year)")
    
    # Get best time per year for the chart
    yearly_best = history.groupby('Year')['Time_Sec'].min().reset_index()
    
    if len(yearly_best) > 1:
        fig = px.line(yearly_best, x='Year', y='Time_Sec', markers=True, 
                      title=f"{name} - Time Progression (Lower is faster)")
        # Invert Y-axis so "Faster" (lower times) visually moves upward
        fig.update_yaxes(autorange="reversed") 
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough historical data to plot a trendline (Only 1 year recorded for this event).")

# --- 4.5 NEW: SHORT-TERM FORM Forecast (TIME SERIES) ---
    st.write("---")
    st.write(f"### 🔮 Short-Term Form Forecast (Time Series)")
    st.write("Using Holt's Exponential Smoothing to predict their next upcoming race times based on recent form.")

    # 1. Prepare the Data
    ts_data = history.copy()
    ts_data['Date'] = pd.to_datetime(ts_data['Date'], errors='coerce')
    ts_data = ts_data.dropna(subset=['Date', 'Time_Sec'])
    ts_data = ts_data.sort_values('Date')

    # 2. Guardrails & Aggregation (Take min time per date for Prelims/Finals)
    ts_data = ts_data.groupby('Date')['Time_Sec'].min().reset_index()

    if len(ts_data) < 6:
        st.warning("⚠️ Not enough race history to generate a reliable short-term forecast. (Minimum 6 distinct race dates required).")
    else:
        # 3. Build the Time Series Model
        times_array = np.asarray(ts_data['Time_Sec'])
        
        try:
            model = Holt(times_array, initialization_method="estimated")
            fit_model = model.fit()
            
            # Forecast the next 3 races
            forecast_steps = 3
            forecast = fit_model.forecast(forecast_steps)
            
            # --- UPGRADE: SHORT-TERM BENCHMARKS ---
            last_time = ts_data['Time_Sec'].iloc[-1]
            next_predicted = forecast[0]
            form_delta = next_predicted - last_time
            
            # Benchmark Evaluation Logic
            if form_delta < -0.2:
                form_status = "🔥 Peaking Fast"
            elif form_delta <= 0.1:
                form_status = "⚖️ Holding Form"
            else:
                form_status = "⚠️ Fatigued / Building"
                
            # Display the Metrics
            col_ts1, col_ts2, col_ts3 = st.columns(3)
            
            col_ts1.metric(
                label="Last Recorded Race",
                value=f"{last_time:.2f}s"
            )
            
            col_ts2.metric(
                label="Next Race Prediction",
                value=f"{next_predicted:.2f}s",
                delta=f"{form_delta:+.2f}s ({form_status})",
                delta_color="inverse", # Inverts color so negative drops are Green
                help="Prediction for their immediate next race. Green means dropping time."
            )
            
            # Calculate momentum across the 3 forecasted races
            trend_delta = forecast[-1] - forecast[0]
            if trend_delta < 0: 
                trend_status = "📉 Accelerating"
            else: 
                trend_status = "📈 Decelerating"
            
            col_ts3.metric(
                label="3-Race Momentum",
                value=trend_status,
                help="Does the model expect them to keep getting faster over the next 3 races, or slow down?"
            )
            
            st.write("") # Spacer
            
            # 4. Visualization (UPGRADED DATE LOGIC)
            last_date = ts_data['Date'].iloc[-1]
            current_real_date = pd.Timestamp.now() # Gets today's real-world date
            
            # Force the forecast to start from either their last race OR today, whichever is later
            base_date = max(last_date, current_real_date)
            
            future_dates = [base_date + pd.DateOffset(months=2*i) for i in range(1, forecast_steps + 1)]
            
            fig_ts = go.Figure()

            fig_ts.add_trace(go.Scatter(
                x=ts_data['Date'], 
                y=ts_data['Time_Sec'], 
                mode='lines+markers',
                name='Historical Races',
                line=dict(color='lightgray', width=2),
                marker=dict(color='gray', size=6)
            ))

            fig_ts.add_trace(go.Scatter(
                x=[ts_data['Date'].iloc[-1]] + future_dates,
                y=[ts_data['Time_Sec'].iloc[-1]] + list(forecast), 
                mode='lines+markers',
                name='Upcoming Forecast',
                line=dict(color='blue', width=3, dash='dash'),
                marker=dict(color='blue', size=10, symbol='star')
            ))

            fig_ts.update_layout(
                title=f"Predicted Trajectory for Next {forecast_steps} Races",
                xaxis_title="Date",
                yaxis_title="Time (Seconds) - Lower is Faster",
                hovermode="x unified",
                height=350
            )
            fig_ts.update_yaxes(autorange="reversed")
            
            st.plotly_chart(fig_ts, use_container_width=True)
            
        except Exception as e:
            st.error("⚠️ The Time Series model could not converge on this athlete's data pattern.")

    # --- 5. LA 2028 PROJECTION ENGINE ---
    st.write("---")
    st.write("### 🌴 LA 2028 Projection")
    
    # Hardcoded Target Dictionary in Total Seconds
    la_2028_targets = {
        'M': {
            '50m Freestyle': {'Gold': 21.04, 'Bronze': 21.34, 'Final': 21.42},
            '100m Freestyle': {'Gold': 46.17, 'Bronze': 47.02, 'Final': 47.46},
            '200m Freestyle': {'Gold': 103.67, 'Bronze': 103.74, 'Final': 104.82}
        },
        'F': {
            '50m Freestyle': {'Gold': 23.47, 'Bronze': 24.20, 'Final': 24.50}, 
            '100m Freestyle': {'Gold': 51.64, 'Bronze': 51.81, 'Final': 52.65},
            '200m Freestyle': {'Gold': 112.14, 'Bronze': 113.41, 'Final': 115.21}
        }
    }
    
    current_gender = history['Gender'].iloc[0]
    current_event = st.session_state['event']
    
    if current_event in la_2028_targets[current_gender]:
        targets = la_2028_targets[current_gender][current_event]
        
        # Calculate Projected 2028 Time
        latest_year = history['Year'].max()
        latest_time = history[history['Year'] == latest_year]['Time_Sec'].min()
        years_to_2028 = 2028 - latest_year
        
        projected_drop = stats['progression_slope'] * years_to_2028
        projected_2028_time = latest_time + projected_drop
        
        st.info(f"**Baseline Prediction:** Based on their historical trajectory, {name}'s projected best time for LA 2028 is **{projected_2028_time:.2f}s**.")
        
        # --- THE DEFINITIVE VERDICT ---
        if projected_2028_time <= targets['Gold']:
            verdict = "🥇 Gold Medal Favorite"
            verdict_subtext = "Projected to hit or beat the Gold Medal target."
        elif projected_2028_time <= targets['Bronze']:
            verdict = "🥉 Podium Contender"
            verdict_subtext = "Projected to medal, falling between the Gold and Bronze targets."
        elif projected_2028_time <= targets['Final']:
            verdict = "🏁 Olympic Finalist"
            verdict_subtext = "Projected to securely make the Top 8 final."
        elif projected_2028_time <= targets['Final'] + 0.5:
            verdict = "⚠️ Striking Distance of Final"
            verdict_subtext = "Projected just outside the final, but within 0.5s. Can close the gap."
        else:
            verdict = "📈 Needs Major Improvement"
            verdict_subtext = "Projected well outside the finalist times."
            
        st.success(f"**Forecasted Outcome:** {verdict}  \n*{verdict_subtext}*")
        
        # Display Likelihood Metrics
        col1, col2, col3 = st.columns(3)
        
        def evaluate_target(projected, target):
            diff = projected - target
            if diff <= 0: return "✅ Reached", "off"
            elif diff <= 0.5: return "⚠️ Close", "off"
            else: return "❌ Missed", "off"
            
        g_status, g_color = evaluate_target(projected_2028_time, targets['Gold'])
        b_status, b_color = evaluate_target(projected_2028_time, targets['Bronze'])
        f_status, f_color = evaluate_target(projected_2028_time, targets['Final'])
        
        col1.metric("🥇 Gold Target", f"{targets['Gold']:.2f}s", delta=g_status, delta_color=g_color)
        col2.metric("🥉 Bronze Target", f"{targets['Bronze']:.2f}s", delta=b_status, delta_color=b_color)
        col3.metric("🏁 Final Target", f"{targets['Final']:.2f}s", delta=f_status, delta_color=f_color)
        
        # --- VISUAL GAP ANALYSIS WITH COLORED ZONES ---
        st.write("#### 📏 Projected Placement Zones")
        
        fig_gap = go.Figure()
        
        min_axis = min(projected_2028_time, targets['Gold']) - 0.5
        max_axis = max(projected_2028_time, targets['Final']) + 1.0

        fig_gap.add_vrect(x0=min_axis, x1=targets['Gold'], fillcolor="gold", opacity=0.2, layer="below", line_width=0)
        fig_gap.add_vrect(x0=targets['Gold'], x1=targets['Bronze'], fillcolor="peru", opacity=0.2, layer="below", line_width=0)
        fig_gap.add_vrect(x0=targets['Bronze'], x1=targets['Final'], fillcolor="gray", opacity=0.1, layer="below", line_width=0)

        fig_gap.add_vline(x=targets['Gold'], line_dash="dash", line_color="goldenrod", annotation_text="Gold Pace")
        fig_gap.add_vline(x=targets['Bronze'], line_dash="dash", line_color="peru", annotation_text="Podium Pace")
        fig_gap.add_vline(x=targets['Final'], line_dash="dash", line_color="black", annotation_text="Finalist Pace")
        
        fig_gap.add_trace(go.Scatter(
            x=[projected_2028_time],
            y=["Projected"],
            mode="markers+text",
            marker=dict(color="blue", size=18, symbol="diamond"),
            text=[f"  {name} ({projected_2028_time:.2f}s)"],
            textposition="middle right",
            textfont=dict(size=14, color="blue"),
            showlegend=False
        ))

        fig_gap.update_layout(
            xaxis_title="Time in Seconds (Further Left = Faster)",
            yaxis_visible=False,
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode=False
        )
        
        fig_gap.update_xaxes(range=[max_axis, min_axis]) 
        
        st.plotly_chart(fig_gap, use_container_width=True)
        
    else:
        st.warning(f"No LA 2028 prediction targets available for {current_event}.")