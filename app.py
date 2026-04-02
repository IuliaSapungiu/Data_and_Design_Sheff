import streamlit as st

# 1. Page Config at the very top
st.set_page_config(page_title="SwimMetrics", layout="wide")

# 2. Define your pages natively (Emojis removed, renamed to Home)
home = st.Page("control_room.py", title="Home")
progression = st.Page("pages/01_progression.py", title="Progression")
comparator = st.Page("pages/03_comparator.py", title="Comparator")

# 3. Group them into a router and entirely hide the native sidebar
pg = st.navigation(
    [home, progression, comparator], 
    position="hidden" 
)

# 4. Run the router
pg.run()