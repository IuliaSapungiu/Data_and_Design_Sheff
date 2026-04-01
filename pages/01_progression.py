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
    
    # Fix the double "m" bug (e.g., turning "200mm" into "200m")
    current_event = st.session_state['event'].replace('mm ', 'm ')
    
    st.write(f"### Progression Profile: {name} ({current_event})")
    
    # --- 1. BENCHMARK EVALUATION LOGIC ---
    slope = stats['progression_slope']
    if slope < -0.3: slope_eval = "🔥 Elite Trajectory"
    elif slope < -0.05: slope_eval = "📈 Improving"
    elif slope <= 0.05: slope_eval = "⚖️ Plateauing"
    else: slope_eval = "⚠️ Regressing"

    rate = stats['rate_of_improvement']
    if rate > 0.4: rate_eval = "⚡ Rapid Paced"
    elif rate > 0.1: rate_eval = "📈 Steady Drop"
    elif rate >= -0.1: rate_eval = "⚖️ Stagnant"
    else: rate_eval = "⚠️ Slowing"
    
    drop_2yr = stats['improvement_2yr']
    if drop_2yr > 0.5: drop_eval = "🔥 Huge Recent Gains"
    elif drop_2yr > 0: drop_eval = "📈 Upward Momentum"
    else: drop_eval = "🧊 Cold/Plateau"

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
    
    plot_df = history.copy()
    plot_df['Date'] = pd.to_datetime(plot_df['Date'], errors='coerce')

    valid_plot_df = plot_df.dropna(subset=['Date', 'Time_Sec'])
    if not valid_plot_df.empty:
        idx_best = valid_plot_df.groupby('Year')['Time_Sec'].idxmin()
        yearly_best = valid_plot_df.loc[idx_best].sort_values('Date')
        yearly_best['Age'] = yearly_best['Age'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "N/A")

        if len(yearly_best) > 1:
            fig = px.line(
                yearly_best,
                x='Date',
                y='Time_Sec',
                markers=True,
                title=f"{name} - Time Progression (Lower is faster)",
                hover_data={
                    'Date': '|%b %d, %Y', 
                    'Time': True,         
                    'Age': True,
                    'Event': True,
                    'Time_Sec': False     
                }
            )
            fig.update_xaxes(tickformat="%Y", dtick="M12", title_text="Year")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough historical data to plot a trendline (Only 1 year recorded for this event).")
    else:
        st.info("No valid date records found for this swimmer to plot.")

    # --- 4.5 SHORT-TERM FORM Forecast (TIME SERIES) ---
    st.write("---")
    st.write(f"### 🔮 Short-Term Form Forecast (Time Series)")
    st.write("Using Holt's Exponential Smoothing to predict their next upcoming race times based on recent form.")

    ts_data = history.copy()
    ts_data['Date'] = pd.to_datetime(ts_data['Date'], errors='coerce')
    ts_data = ts_data.dropna(subset=['Date', 'Time_Sec']).sort_values('Date')
    ts_data = ts_data.groupby('Date')['Time_Sec'].min().reset_index()

    if len(ts_data) < 6:
        st.warning("⚠️ Not enough race history to generate a reliable short-term forecast. (Minimum 6 distinct race dates required).")
    else:
        times_array = np.asarray(ts_data['Time_Sec'])
        try:
            model = Holt(times_array, initialization_method="estimated")
            fit_model = model.fit()
            forecast_steps = 3
            forecast = fit_model.forecast(forecast_steps)
            
            last_time = ts_data['Time_Sec'].iloc[-1]
            next_predicted = forecast[0]
            form_delta = next_predicted - last_time
            
            if form_delta < -0.2: form_status = "🔥 Peaking Fast"
            elif form_delta <= 0.1: form_status = "⚖️ Holding Form"
            else: form_status = "⚠️ Fatigued / Building"
                
            col_ts1, col_ts2, col_ts3 = st.columns(3)
            col_ts1.metric("Last Recorded Race", f"{last_time:.2f}s")
            col_ts2.metric(
                "Next Race Prediction", f"{next_predicted:.2f}s", 
                delta=f"{form_delta:+.2f}s ({form_status})", delta_color="inverse", 
                help="Prediction for their immediate next race. Green means dropping time."
            )
            
            trend_delta = forecast[-1] - forecast[0]
            trend_status = "📉 Accelerating" if trend_delta < 0 else "📈 Decelerating"
            col_ts3.metric("3-Race Momentum", trend_status, help="Does the model expect them to keep getting faster over the next 3 races, or slow down?")
            
            st.write("") 
            
            last_date = ts_data['Date'].iloc[-1]
            current_real_date = pd.Timestamp.now() 
            base_date = max(last_date, current_real_date)
            future_dates = [base_date + pd.DateOffset(months=2*i) for i in range(1, forecast_steps + 1)]
            
            fig_ts = go.Figure()
            fig_ts.add_trace(go.Scatter(x=ts_data['Date'], y=ts_data['Time_Sec'], mode='lines+markers', name='Historical Races', line=dict(color='lightgray', width=2), marker=dict(color='gray', size=6)))
            fig_ts.add_trace(go.Scatter(x=[ts_data['Date'].iloc[-1]] + future_dates, y=[ts_data['Time_Sec'].iloc[-1]] + list(forecast), mode='lines+markers', name='Upcoming Forecast', line=dict(color='blue', width=3, dash='dash'), marker=dict(color='blue', size=10, symbol='star')))

            fig_ts.update_layout(title=f"Predicted Trajectory for Next {forecast_steps} Races", xaxis_title="Date", yaxis_title="Time (Seconds) - Lower is Faster", hovermode="x unified", height=350)
            fig_ts.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_ts, use_container_width=True)
            
        except Exception as e:
            st.error("⚠️ The Time Series model could not converge on this athlete's data pattern.")

    # --- 5. LA 2028 PROJECTION ENGINE ---
    st.write("---")
    st.write("### 🌴 Olympic LA 2028 Projection")
    
    la_2028_targets = {
        'M': {
            '50m Freestyle': {'Gold': 21.04, 'Bronze': 21.34, 'Final': 21.96},
            '100m Freestyle': {'Gold': 46.17, 'Bronze': 47.02, 'Final': 48.34},
            '200m Freestyle': {'Gold': 103.67, 'Bronze': 103.74, 'Final': 106.26},
            '400m Freestyle': {'Gold': 222.00, 'Bronze': 224.00, 'Final': 226.78},
            '100m Backstroke': {'Gold': 51.50, 'Bronze': 52.20, 'Final': 53.74},
            '200m Backstroke': {'Gold': 113.50, 'Bronze': 115.00, 'Final': 117.50},
            '100m Breaststroke': {'Gold': 57.50, 'Bronze': 58.50, 'Final': 59.49},
            '200m Breaststroke': {'Gold': 126.00, 'Bronze': 128.00, 'Final': 129.68},
            '100m Butterfly': {'Gold': 49.50, 'Bronze': 50.50, 'Final': 51.67},
            '200m Butterfly': {'Gold': 111.00, 'Bronze': 113.00, 'Final': 115.78},
            '200m Medley': {'Gold': 115.00, 'Bronze': 116.50, 'Final': 117.94},
        },
        'F': {
            '50m Freestyle': {'Gold': 23.47, 'Bronze': 24.20, 'Final': 24.70}, 
            '100m Freestyle': {'Gold': 51.64, 'Bronze': 51.81, 'Final': 53.61},
            '200m Freestyle': {'Gold': 112.14, 'Bronze': 113.41, 'Final': 117.26},
            '400m Freestyle': {'Gold': 236.00, 'Bronze': 239.00, 'Final': 247.90},
            '100m Backstroke': {'Gold': 57.50, 'Bronze': 58.50, 'Final': 59.99},
            '200m Backstroke': {'Gold': 124.00, 'Bronze': 126.00, 'Final': 130.39},
            '100m Breaststroke': {'Gold': 64.50, 'Bronze': 65.50, 'Final': 66.79},
            '200m Breaststroke': {'Gold': 139.00, 'Bronze': 141.00, 'Final': 143.91},
            '100m Butterfly': {'Gold': 55.50, 'Bronze': 56.50, 'Final': 57.92},
            '200m Butterfly': {'Gold': 124.00, 'Bronze': 126.00, 'Final': 128.43},
            '200m Medley': {'Gold': 127.00, 'Bronze': 129.00, 'Final': 131.47},
        }
    }
    
    current_gender = history['Gender'].dropna().iloc[0] if 'Gender' in history.columns and not history['Gender'].dropna().empty else 'M'
    
    if current_event in la_2028_targets.get(current_gender, {}):
        targets = la_2028_targets[current_gender][current_event]
    else:
        st.info(f"Specific LA 2028 FINA cuts are not mapped for {current_event}. Generating dynamic baseline targets based on recent world-class margins.")
        baseline = stats['best_time']
        targets = {'Gold': baseline * 0.96, 'Bronze': baseline * 0.98, 'Final': baseline * 0.995}
        
    # --- UPGRADED: Diminishing Returns Projection Algorithm ---
    latest_year = history['Year'].max()
    years_to_2028 = max(1, 2028 - latest_year)
    baseline_time = stats['best_time'] # We anchor strictly to their ALL-TIME PB, not their last swim
    
    raw_slope = stats['progression_slope']
    projected_drop = 0
    
    # Apply physiological limits: athletes cannot drop time at a linear rate forever
    if raw_slope < 0:
        current_rate = raw_slope
        for _ in range(years_to_2028):
            projected_drop += current_rate
            # Decay the improvement rate by 50% each year (harder to drop time the closer you get to your peak)
            current_rate *= 0.50 
    else:
        # If regressing, dampen the regression so the model doesn't over-punish them
        projected_drop = raw_slope * (years_to_2028 * 0.3)

    projected_2028_time = baseline_time + projected_drop
    
    st.info(f"**Advanced Physiological Forecast:** Applying a diminishing returns algorithm to their career slope, {name}'s projected best time for LA 2028 is **{projected_2028_time:.2f}s**.")
    
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