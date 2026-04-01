import pandas as pd
import numpy as np

def find_similar_swimmers(target_stats, features_df, event_df, max_n=10):
    target_id = target_stats['FINA ID']
    
    # The data is ALREADY filtered by the Control Room for Gender, Stroke, and Distance.
    # Therefore, everyone in features_df is exactly matching the selected event!
    target_event = "Selected Event"

    # Start with everyone except the target
    pool = features_df[features_df['FINA ID'] != target_id].copy()
    
    # We drop country from the pool temporarily to avoid merge conflicts
    if 'Country' in pool.columns:
        pool = pool.drop(columns=['Country'])
    
    # Extract EXACT columns from the filtered raw data using 'Time_Sec'
    raw_stats = event_df.groupby('FINA ID').agg(
        Country=('Country', 'first'),
        best_time=('Time_Sec', 'min') 
    ).reset_index()
    
    # Merge and drop anyone who doesn't have a time
    pool = pd.merge(pool, raw_stats, on='FINA ID', how='inner')
    
    target_raw = raw_stats[raw_stats['FINA ID'] == target_id]
    if target_raw.empty:
        return pd.DataFrame(), 0.0, target_event # Failsafe
        
    target_best_time = target_raw.iloc[0]['best_time']

    # Features for KNN - Purely Performance Based!
    features_to_calc = ['best_time', 'consistency_score']
    
    slope_col = None
    if 'progression_slope' in pool.columns:
        slope_col = 'progression_slope'
    elif 'slope' in pool.columns:
        slope_col = 'slope'
        
    if slope_col:
        features_to_calc.append(slope_col)
        
    target_slope = target_stats.get('progression_slope', target_stats.get('slope', pool.get(slope_col, pd.Series([0])).median() if slope_col else 0.0))

    target_stats_filled = {
        'best_time': target_best_time,
        'consistency_score': target_stats.get('consistency_score', pool.get('consistency_score', pd.Series([80])).median()),
    }
    if slope_col:
        target_stats_filled[slope_col] = target_slope

    for col in features_to_calc:
        if col not in pool.columns:
            pool[col] = 0.0
        pool[col] = pool[col].fillna(pool[col].median())

    # KNN Distance Logic
    pool['similarity_distance'] = 0.0
    for col in features_to_calc:
        min_val, max_val = pool[col].min(), pool[col].max()
        val_range = max_val - min_val if max_val - min_val != 0 else 1
        
        pool_norm = (pool[col] - min_val) / val_range
        target_norm = (target_stats_filled[col] - min_val) / val_range
        
        # WEIGHTING: 60% importance on Speed, 40% split between Consistency and Trajectory
        weight = 0.60 if col == 'best_time' else (0.40 / max(1, len(features_to_calc) - 1))
        pool['similarity_distance'] += weight * ((pool_norm - target_norm) ** 2)
        
    pool['similarity_distance'] = np.sqrt(pool['similarity_distance'])
    
    # NOTE: The 15% country bias logic has been completely removed from here.
    # Matches are now strictly based on the mathematical distance of their performances.

    pool = pool.drop_duplicates(subset=['Swimmer'])
    pool = pool.sort_values('similarity_distance')

    # SMART THRESHOLD CUTOFF
    if not pool.empty:
        best_distance = pool.iloc[0]['similarity_distance']
        cutoff_threshold = max(best_distance * 3.0, 0.15) 
        pool = pool[pool['similarity_distance'] <= cutoff_threshold]

    return pool.head(max_n), target_best_time, target_event