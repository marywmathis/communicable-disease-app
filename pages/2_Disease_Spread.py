import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# -------------------------------------------------
# DISEASE PRESET R₀ VALUES
# -------------------------------------------------
disease_r0 = {
    "Measles (MMR)": 15,
    "Pertussis (DTaP)": 12,
    "Polio (IPV)": 6,
    "Varicella (Chickenpox)": 10,
    "Hepatitis B (HepB)": 3,
    "HPV": 3,
    "Hib": 1.3,
    "Pneumococcal (PCV)": 2
}

# -------------------------------------------------
# PAGE TITLE
# -------------------------------------------------
st.header("Exponential Disease Spread")

st.markdown("""
This page shows **basic exponential transmission** assuming no immunity in the population.
""")

# -------------------------------------------------
# SELECT DISEASE + R₀
# -------------------------------------------------
disease = st.selectbox(
    "Choose a disease:",
    list(disease_r0.keys())
)

R0_default = disease_r0[disease]

R0 = st.slider(
    "R₀ (Basic Reproduction Number)",
    min_value=1.0,
    max_value=20.0,
    value=float(R0_default),
    step=0.1
)

# -------------------------------------------------
# GENERATIONS
# -------------------------------------------------
generations = st.slider(
    "Number of generations",
    min_value=1,
    max_value=12,
    value=6
)

# -------------------------------------------------
# CALCULATE INFECTIONS
# -------------------------------------------------
infected = [1]  # generation 0 starts with a single infected person

for g in range(1, generations + 1):
    infected.append(infected[-1] * R0)

df = pd.DataFrame({
    "Generation": list(range(generations + 1)),
    "Infected": infected
})

# -------------------------------------------------
# CHART — COLOR GRADIENT (GREEN → YELLOW → RED)
# -------------------------------------------------
chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("Generation:O"),
        y=alt.Y("Infected:Q"),
        color=alt.Color(
            "Infected:Q",
            scale=alt.Scale(scheme="redyellowgreen"),
            legend=None
        )
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

# -------------------------------------------------
# SUMMARY STAT
# -------------------------------------------------
st.markdown("---")

st.metric(
    label="Total infected after all generations",
    value=f"{int(infected[-1]):,}"
)

st.markdown("""
### Interpretation
- Exponential growth means **each generation multiplies by R₀**.  
- Higher R₀ → **faster spread** and **larger outbreaks**.  
- Later pages show how vaccination and immunity slow this growth.
""")
