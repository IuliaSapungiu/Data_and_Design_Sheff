import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def load_and_clean_data(filepath=r"D:\UoS\Hackaton\swimming-analytics\data\WA_Rankings_2000_2025_Master_v1.csv"):
    df = pd.read_csv(filepath)
    
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
    
    # 2. Ensure Year exists (If your 'Year' column is already perfect, this just acts as a backup)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
    
    # 3. Drop invalid rows (We also make sure Gender is not empty just in case)
    df = df.dropna(subset=['Time_Sec', 'Year', 'Gender'])
    
    return df