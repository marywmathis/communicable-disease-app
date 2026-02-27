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
st.header("Impact of Vaccination on Disease Spread")

st.markdown("""
This page compares an outbreak **with no vaccination** to an outbreak under **real-world vaccination coverage**.
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
# VACCINATION SLIDER
# -------------------------------------------------
coverage = st.slider(
    "Vaccination Coverage (%)",
    min_value=0,
    max_value=100,
    value=75
)

# -------------------------------------------------
# EFFECTIVE R (Rₑ)
# -------------------------------------------------
Re = R0 * (1 - coverage / 100)

st.metric("Effective Reproduction Number (Rₑ)", f"{Re:.2f}")

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
infected_no_vax = [1]
infected_vax = [1]

for g in range(1, generations + 1):
    infected_no_vax.append(infected_no_vax[-1] * R0)
    infected_vax.append(infected_vax[-1] * Re)

df = pd.DataFrame({
    "Generation": list(range(generations + 1)),
    "No Vaccination": infected_no_vax,
    "With Vaccination": infected_vax
})

plot_df = df.melt(id_vars=["Generation"], var_name="Scenario", value_name="Infected")

# -------------------------------------------------
# LINE CHART COMPARISON
# -------------------------------------------------
chart = (
    alt.Chart(plot_df)
    .mark_line(point=True, strokeWidth=3)
    .encode(
        x="Generation:O",
        y="Infected:Q",
        color=alt.Color(
            "Scenario:N",
            scale=alt.Scale(
                range=["#E53935", "#43A047"]  # red = no vax, green = vax
            ),
            legend=alt.Legend(title="Scenario")
        )
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

# -------------------------------------------------
# SUMMARY STATEMENTS
# -------------------------------------------------
st.markdown("---")

st.markdown(f"""
### Summary
- **No vaccination** leads to **{int(infected_no_vax[-1]):,} infections** after {generations} generations.  
- **With {coverage}% vaccination**, infections fall to **{int(infected_vax[-1]):,}**.  
- Effective R drops from **{R0:.1f} → {Re:.2f}**, slowing transmission dramatically.
""")
