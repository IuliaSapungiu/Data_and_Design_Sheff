import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# Define both paths relative to this file
CURRENT_DIR = Path(__file__).parent
CSV_PATH = CURRENT_DIR / "WA_Rankings_2000_2025_Master_v1.csv"
PARQUET_PATH = CURRENT_DIR / "WA_Rankings_2000_2025_Master_v1.parquet"

@st.cache_data
def load_and_clean_data():
    # --- 1. FAST PATH: Instant Load ---
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
        
    # --- 2. SLOW PATH: First-Time Setup ---
    elif CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        
        # --- VECTORIZED TIME CONVERSION (Lightning Fast) ---
        time_str = df['Time'].astype(str).str.strip()
        has_colon = time_str.str.contains(':', na=False)
        df['Time_Sec'] = np.nan
        
        if has_colon.any():
            split_times = time_str[has_colon].str.split(':', expand=True)
            df.loc[has_colon, 'Time_Sec'] = split_times[0].astype(float) * 60 + split_times[1].astype(float)
            
        if (~has_colon).any():
            df.loc[~has_colon, 'Time_Sec'] = pd.to_numeric(time_str[~has_colon], errors='coerce')
            
        # --- OPTIMIZED DATE PARSING ---
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce', exact=False)
            df['Year'] = df['Date'].dt.year
        
        # --- DROP INVALID ROWS ---
        df = df.dropna(subset=['Time_Sec', 'Year', 'Gender'])
        
        # Save the CLEANED dataframe to Parquet
        df.to_parquet(PARQUET_PATH)
        
        return df
        
    # --- 3. CRITICAL ERROR ---
    else:
        # Instead of Streamlit UI errors, raise a proper Python exception
        raise FileNotFoundError(f"Critical Error: Could not find the database file at {CSV_PATH}. Please ensure the dataset is downloaded.")