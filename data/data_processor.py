import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# This finds the folder where data_processor.py lives (the 'data' folder)
# then looks for the CSV inside that same folder.
# Make sure this name matches what is inside the parentheses below
DATA_PATH = Path(__file__).parent / "WA_Rankings_2000_2025_Master_v1.csv"

@st.cache_data
def load_and_clean_data(filepath=DATA_PATH):
    # Convert to string so pandas doesn't complain
    df = pd.read_csv(str(filepath))
    
    # 1. Convert Time to Seconds
    def time_to_seconds(t):
        try:
            t = str(t).strip()
            if ':' in t:
                mins, secs = t.split(':')
                return int(mins) * 60 + float(secs)
            return float(t)
        except:
            return np.nan

    df['Time_Sec'] = df['Time'].apply(time_to_seconds)
    
    # 2. Ensure Year exists
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
    
    # 3. Drop invalid rows
    df = df.dropna(subset=['Time_Sec', 'Year', 'Gender'])
    
    return df