import streamlit as st
from pathlib import Path

# -------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------
st.set_page_config(
    page_title="Communicable Disease Spread Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# LOAD CUSTOM THEME CSS
# -------------------------------------------------
theme_path = Path("assets/theme.css")
if theme_path.exists():
    with open(theme_path, "r") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# -------------------------------------------------
# MAIN TITLE
# -------------------------------------------------
st.title("Communicable Disease Spread Simulator")

st.markdown("""
Welcome to the **Communicable Disease Spread Simulator**, designed to help visualize:

- How infectious diseases spread  
- How vaccination affects the effective R (Rₑ)  
- How herd immunity reduces transmission  
- How outbreaks unfold across generations  

Use the **navigation menu on the left** to explore:
1. Herd Immunity Calculator  
2. Exponential Disease Spread  
3. Vaccine Impact  
4. Spread Visualization (Animated or Node Tree)
""")

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("---")
st.caption("Developed for epidemiology teaching — includes R₀ presets, vaccination effects, and transmission visuals.")
