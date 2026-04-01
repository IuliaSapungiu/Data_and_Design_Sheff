import pandas as pd
import numpy as np

def find_similar_swimmers(target_stats, features_df, event_df, max_n=10):
    """
    High-speed KNN Comparator.
    Uses pre-calculated 'best_time' from the Control Room.
    """
    target_id = target_stats['FINA ID']
    
    # Because app.py already perfectly filtered the data by Stroke and Distance,
    # we don't need to filter by event again here. 
    target_event = "Selected Event"

    # Start with everyone except the target
    pool = features_df[features_df['FINA ID'] != target_id].copy()
    
    # Extract EXACT columns from the filtered raw data
    raw_stats = event_df.groupby('FINA ID').agg(
        Country=('Country', 'first'),
        best_time=('Time_Sec', 'min') 
    ).reset_index()
    
    # Merge and drop anyone who doesn't have a time
    pool = pd.merge(pool, raw_stats, on='FINA ID', how='inner')
    
    target_raw = raw_stats[raw_stats['FINA ID'] == target_id]
    if target_raw.empty:
        return pd.DataFrame(), 0.0, target_event # Failsafe
        
    target_country = target_raw.iloc[0]['Country']
    target_best_time = target_raw.iloc[0]['best_time']

    # Features for KNN
    features_to_calc = ['best_time', 'consistency_score']
    if 'slope' in pool.columns:
        features_to_calc.append('slope')
        
    target_stats_filled = {
        'best_time': target_best_time,
        'consistency_score': target_stats.get('consistency_score', pool.get('consistency_score', pd.Series([80])).median()),
        'slope': target_stats.get('slope', pool.get('slope', pd.Series([0])).median())
    }

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
        
        weight = 0.60 if col == 'best_time' else (0.40 / max(1, len(features_to_calc) - 1))
        pool['similarity_distance'] += weight * ((pool_norm - target_norm) ** 2)
        
    pool['similarity_distance'] = np.sqrt(pool['similarity_distance'])
    pool.loc[pool['Country'] == target_country, 'similarity_distance'] *= 0.85 

    pool = pool.drop_duplicates(subset=['Swimmer'])
    pool = pool.sort_values('similarity_distance')

    # SMART THRESHOLD CUTOFF
    if not pool.empty:
        best_distance = pool.iloc[0]['similarity_distance']
        cutoff_threshold = best_distance * 3.0 
        cutoff_threshold = max(cutoff_threshold, 0.15) 
        pool = pool[pool['similarity_distance'] <= cutoff_threshold]

    return pool.head(max_n), target_best_time, target_event