import pandas as pd
import numpy as np
from scipy.stats import linregress

def build_progression_features(df):
    yearly_best = df.groupby(['FINA ID', 'Swimmer', 'Year'])['Time_Sec'].min().reset_index()
    progression_data = []
    
    for fina_id, group in yearly_best.groupby('FINA ID'):
        group = group.sort_values('Year')
        times = group['Time_Sec'].values
        years = group['Year'].values
        
        # FIX: Handle swimmers with only 1 year of data gracefully
        if len(group) < 2:
            rate_of_improvement = 0.0
            improvement_2yr = 0.0
            slope = 0.0
            consistency_score = 0.0
        else:
            rate_of_improvement = (times[0] - times[-1]) / (years[-1] - years[0]) if years[-1] != years[0] else 0
            
            if len(times) >= 3:
                improvement_2yr = times[-3] - times[-1]
                consistency_score = np.std(times[-3:])
            else:
                improvement_2yr = times[-2] - times[-1]
                consistency_score = np.std(times[-2:])
                
            slope, _, _, _, _ = linregress(years, times)
            
        progression_data.append({
            'FINA ID': fina_id,
            'Swimmer': group['Swimmer'].iloc[0],
            'rate_of_improvement': rate_of_improvement,
            'improvement_2yr': improvement_2yr,
            'progression_slope': slope,
            'consistency_score': consistency_score
        })
        
    return pd.DataFrame(progression_data)