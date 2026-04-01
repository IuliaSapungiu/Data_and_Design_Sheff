import pandas as pd
import numpy as np

def find_similar_swimmers(target_stats, features_df, event_df, max_n=10):
    """
    High-speed KNN Comparator.
    Uses pre-calculated 'best_time' from the Control Room.
    """
    target_id = target_stats['FINA ID']
    target_best_time = target_stats['best_time']
    
    # Identify the event name for UI display
    target_history = event_df[event_df['FINA ID'] == target_id]
    target_event = target_history['Event'].iloc[0] if not target_history.empty else "Unknown Event"

    # 1. Setup the Pool (Everyone except the target)
    pool = features_df[features_df['FINA ID'] != target_id].copy()
    
    if pool.empty:
        return pd.DataFrame(), target_best_time, target_event

    # 2. Select columns for similarity math
    # We use these 4 pillars to find "Swimmer Twins"
    compare_cols = ['best_time', 'slope', 'consistency_score', 'distance_from_peak']
    existing_cols = [c for c in compare_cols if c in pool.columns]
    
    # 3. KNN Math (Vectorized for speed)
    pool['similarity_distance'] = 0.0
    
    for col in existing_cols:
        v_min, v_max = pool[col].min(), pool[col].max()
        v_range = v_max - v_min if v_max - v_min != 0 else 1.0
        
        # Normalize target and pool to 0-1 scale
        target_val = target_stats[col]
        
        # We weight 'best_time' at 70% because speed is the most important similarity
        weight = 0.7 if col == 'best_time' else 0.1
        
        dist = ((pool[col] - target_val) / v_range) ** 2
        pool['similarity_distance'] += weight * dist

    pool['similarity_distance'] = np.sqrt(pool['similarity_distance'])
    
    # 4. Sort and Return
    pool = pool.sort_values('similarity_distance')
    
    # Smart Quality Filter: Only show swimmers who are actually similar
    if not pool.empty:
        # If the distance is > 3x the best match, it's likely not a good comparison
        cutoff = pool.iloc[0]['similarity_distance'] * 3.0
        pool = pool[pool['similarity_distance'] <= cutoff]

    return pool.head(max_n), target_best_time, target_event