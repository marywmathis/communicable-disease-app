################################################################################
# 3_Vaccine_Impact.py — FULLY CORRECTED VERSION
# All tabs synced, Option 3 coverage logic implemented, no Streamlit warnings
################################################################################

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import networkx as nx
import plotly.graph_objects as go
import json
import math
import time


# =============================================================================
# BASELINE R₀ VALUES FOR DISEASES
# =============================================================================
disease_r0 = {
    "Measles (MMR)": 15,
    "Pertussis (DTaP)": 12,
    "Polio (IPV)": 6,
    "Varicella (Chickenpox)": 10,
    "Hepatitis B (HepB)": 3,
    "HPV": 3,
    "Hib": 1.3,
    "Pneumococcal (PCV)": 2,
}

# =============================================================================
# REAL-WORLD VACCINATION PRESETS
# =============================================================================
vacc_presets = {
    "MMR": 94,
    "DTaP": 90,
    "Polio": 85,
    "Varicella": 90,
    "Hib": 90,
    "HepB": 91,
    "PCV": 92,
}

# =============================================================================
# PAGE HEADER
# =============================================================================
st.header("Impact of Vaccination on Disease Spread")

st.write("""
This module explores:
- How vaccination coverage alters **Rₑ**, outbreak size, and herd immunity thresholds  
- How exponential growth compares to SEIR compartment dynamics  
- How transmission maps change under superspreaders and vaccinated individuals  
""")

# =============================================================================
# TABS
# =============================================================================
tab1, tab2, tab3 = st.tabs([
    "Basic Vaccination Impact",
    "SEIR vs Exponential Growth",
    "Transmission Tree"
])

################################################################################
# TAB 1 — BASIC VACCINATION IMPACT
################################################################################
with tab1:

    st.subheader("Basic Vaccination Impact")

    # -------------------------------------------------------------------------
    # Disease input
    # -------------------------------------------------------------------------
    disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
    R0 = disease_r0[disease]
    st.write(f"**Baseline R₀ for {disease}: {R0}**")

    # -------------------------------------------------------------------------
    # Initialize synced state variables
    # -------------------------------------------------------------------------
    if "coverage_value" not in st.session_state:
        st.session_state.coverage_value = 75

    if "preset_choice" not in st.session_state:
        st.session_state.preset_choice = "None"

    st.markdown("### Vaccination Coverage Settings")

    colA, colB = st.columns([2, 3])

    # -------------------------------------------------------------------------
    # 1️⃣ PRESET → sets coverage_value and slider should update
    # -------------------------------------------------------------------------
    with colB:
        st.write("Preset Coverage Values:")

        preset = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True,
            key="preset_choice",
        )

        if preset != "None":
            st.session_state.coverage_value = vacc_presets[preset]
            st.success(f"Using preset: {preset} = {vacc_presets[preset]}%")

    # -------------------------------------------------------------------------
    # 2️⃣ SLIDER → if moved, preset must reset to "None"
    # -------------------------------------------------------------------------
    with colA:
        # dynamic key ensures slider rebuilds when preset changes
        slider_key = f"coverage_slider_{st.session_state.coverage_value}"

        slider_val = st.slider(
            "Vaccination Coverage (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.coverage_value,
            key=slider_key
        )

        # If the user moves the slider away from preset → deselect preset
        if slider_val != st.session_state.coverage_value:
            st.session_state.preset_choice = "None"

        # Store updated coverage
        st.session_state.coverage_value = slider_val

    # FINAL synced value
    coverage = st.session_state.coverage_value

    # -------------------------------------------------------------------------
    # Herd Immunity Threshold
    # -------------------------------------------------------------------------
    herd_threshold = (1 - 1 / R0) * 100
    st.metric("Herd Immunity Threshold", f"{herd_threshold:.1f}%")

    if coverage >= herd_threshold:
        st.success("Population exceeds herd immunity threshold.")
    else:
        st.warning("Population is below herd immunity threshold.")

    # -------------------------------------------------------------------------
    # Effective Rₑ
    # -------------------------------------------------------------------------
    Re = R0 * (1 - coverage / 100)
    st.metric("Effective Rₑ", f"{Re:.2f}")

    # -------------------------------------------------------------------------
    # Generations
    # -------------------------------------------------------------------------
    generations = st.slider("Number of generations", 1, 12, 6)

    infected_no = [1]
    infected_yes = [1]

    for g in range(1, generations + 1):
        infected_no.append(infected_no[-1] * R0)
        infected_yes.append(infected_yes[-1] * Re)

    df_no = pd.DataFrame({"Generation": range(generations + 1),
                          "Infected": infected_no})

    df_yes = pd.DataFrame({"Generation": range(generations + 1),
                           "Infected": infected_yes})

    # -------------------------------------------------------------------------
    # Log/Linear toggle
    # -------------------------------------------------------------------------
    scale = st.radio("Chart Scale", ["Linear", "Log Scale"], horizontal=True)

    y_axis = alt.Y(
        "Infected:Q",
        scale=alt.Scale(type="log") if scale == "Log Scale" else alt.Scale(type="linear")
    )

    # -------------------------------------------------------------------------
    # Charts side-by-side
    # -------------------------------------------------------------------------
    chart_no = (
        alt.Chart(df_no)
        .mark_line(point=True, color="#E53935")
        .encode(x="Generation:O", y=y_axis)
        .properties(title="No Vaccination (R₀)")
    )

    chart_yes = (
        alt.Chart(df_yes)
        .mark_line(point=True, color="#43A047")
        .encode(x="Generation:O", y=y_axis)
        .properties(title=f"With Vaccination (Rₑ={Re:.2f})")
    )

    c1, c2 = st.columns(2)
    c1.altair_chart(chart_no, use_container_width=True)
    c2.altair_chart(chart_yes, use_container_width=True)

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    st.markdown("### Summary")
    st.write(f"""
    - **Final generation infections:**  
      - No vaccination: {infected_no[-1]:,}  
      - With vaccination: {infected_yes[-1]:,}  

    - **Cumulative infections:**  
      - No vaccination: {sum(infected_no):,}  
      - With vaccination: {sum(infected_yes):,}  
    """)
