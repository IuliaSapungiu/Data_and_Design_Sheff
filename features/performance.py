import pandas as pd

def build_performance_features(df):
    # 1. Get each swimmer's best time per year, and grab their Age
    # We group by FINA ID to ensure one record per athlete per year
    yearly_best = df.groupby(['FINA ID', 'Swimmer', 'Year']).agg({
        'Time_Sec': 'min',
        'Age': 'max' 
    }).reset_index()
    
    # 2. Calculate the 'Championship Pace' (Top 8 Average) for EACH YEAR
    # Instead of looking at one person (the 10th), we average the Top 8 
    # This represents the average speed required to be in an Olympic Final.
    yearly_stats = yearly_best.groupby('Year')['Time_Sec'].agg(
        championship_pace=lambda x: x.nsmallest(8).mean() if len(x) >= 8 else x.mean()
    ).reset_index()
    
    # Merge these yearly benchmarks back to the individual swimmers
    yearly_best = yearly_best.merge(yearly_stats, on='Year', how='left')
    
    # 3. Calculate Percentile per year 
    # This tells us where they sit relative to the entire field that year.
    yearly_best['percentile'] = yearly_best.groupby('Year')['Time_Sec'].rank(pct=True)
    
    # 4. Gap to Championship Pace
    # Negative = Faster than the Top 8 average (Elite). 
    # Positive = Slower than the average.
    yearly_best['gap_to_top8'] = yearly_best['Time_Sec'] - yearly_best['championship_pace']
    
    career_stats = []
    
    # 5. Calculate Career Stages & Distance from Peak
    for fina_id, group in yearly_best.groupby('FINA ID'):
        years_competing = group['Year'].nunique()
        personal_best = group['Time_Sec'].min()
        
        # Look at their most recent active year
        latest_year_data = group.loc[group['Year'].idxmax()]
        distance_from_peak = latest_year_data['Time_Sec'] - personal_best
        
        # Career Stage logic based on latest age
        latest_age = latest_year_data['Age']
        if pd.isna(latest_age):
            career_stage = 'Unknown'
        elif latest_age < 20:
            career_stage = 'Early'
        elif 20 <= latest_age <= 26:
            career_stage = 'Peak'
        else:
            career_stage = 'Decline'
            
        career_stats.append({
            'FINA ID': fina_id,
            'years_competing': years_competing,
            'distance_from_peak': distance_from_peak,
            'career_stage': career_stage,
            'latest_percentile': latest_year_data['percentile'],
            'latest_gap_to_top10': latest_year_data['gap_to_top8'] # Keep key name same for app.py compatibility
        })
        
    return pd.DataFrame(career_stats)