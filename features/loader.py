import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    df = pd.read_csv("D:\\UoS\\Hackaton\\swimming-analytics\\data\\WA_Rankings_2000_2025_Master_v1.csv")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Year"] = df["Date"].dt.year
    # Create a combined event label if not already there
    if "FullEvent" not in df.columns:
        df["FullEvent"] = df["Stroke"] + " " + df["Event"]
    return df