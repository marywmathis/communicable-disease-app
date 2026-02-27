import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time

# ---------------------------------------------
# Disease R₀ values
# ---------------------------------------------
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

# ---------------------------------------------
# Vaccination presets (your custom values)
# ---------------------------------------------
vacc_presets = {
    "MMR": 94,
    "DTaP": 90,
    "Polio": 85,
    "Varicella": 90,
    "Hib": 90,
    "HepB": 91,
    "PCV": 92
}

# ---------------------------------------------
# Page Title
# ---------------------------------------------
st.header("Vaccination Impact Simulation Suite")

st.markdown("""
This dashboard demonstrates how vaccination alters the course of an epidemic using:

**• Exponential outbreak models**  
**• SEIR compartmental models**  
**• Animations & herd immunity thresholds**  
""")


# ============================================================
# CREATE TABS
# ============================================================
tab1, tab2, tab3 = st.tabs(
    ["📊 Basic Vaccination Impact",
     "🎬 Animated Outbreak Comparison",
     "🔬 SEIR vs Exponential"]
)


# ============================================================
# TAB 1 — BASIC VACCINATION IMPACT
# ============================================================
with tab1:

    st.subheader("Basic Vaccination Impact")

    disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
    R0 = disease_r0[disease]

    st.write(f"**Baseline R₀ for {disease}: {R0}**")

    st.markdown("### Vaccination Coverage")

    colA, colB = st.columns([2, 3])

    with colA:
        coverage = st.slider(
            "Vaccination Coverage (%)",
            min_value=0, max_value=100,
            value=75
        )

    with colB:
        st.write("Preset Coverage Values:")
        preset_selection = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True
        )
        if preset_selection != "None":
            coverage = vacc_presets[preset_selection]
            st.success(f"Using preset: {preset_selection} = {coverage}%")

    # Herd Immunity Threshold
    herd_threshold = (1 - 1/R0) * 100
    st.metric("Herd Immunity Threshold", f"{herd_threshold:.1f}%")

    if coverage >= herd_threshold:
        st.success("Population exceeds herd immunity threshold.")
    else:
        st.warning("Population is below herd immunity threshold.")

    # Effective Reproduction Number
    Re = R0 * (1 - coverage/100)
    st.metric("Effective Rₑ", f"{Re:.2f}")

    generations = st.slider(
        "Number of generations",
        min_value=1, max_value=12, value=6
    )

    # Calculate infections
    infected_no_vax = [1]
    infected_vax = [1]

    for g in range(1, generations + 1):
        infected_no_vax.append(infected_no_vax[-1] * R0)
        infected_vax.append(infected_vax[-1] * Re)

    cumulative_no_vax = sum(infected_no_vax)
    cumulative_vax = sum(infected_vax)

    # Build dataframes
    df_no = pd.DataFrame({
        "Generation": list(range(generations + 1)),
        "Infected": infected_no_vax
    })

    df_yes = pd.DataFrame({
        "Generation": list(range(generations + 1)),
        "Infected": infected_vax
    })

    # Toggle for log scale
    scale_type = st.radio(
        "Chart Scale",
        ["Linear", "Log Scale (base 10)"],
        horizontal=True
    )

    y_axis = alt.Y(
        "Infected:Q",
        scale=alt.Scale(type="log") if scale_type == "Log Scale (base 10)" else alt.Scale(type="linear"),
        title="Infected"
    )

    # Create charts
    chart_no = (
        alt.Chart(df_no)
        .mark_line(point=True, color="#E53935", strokeWidth=3)
        .encode(
            x="Generation:O",
            y=y_axis,
            tooltip=["Generation", "Infected"]
        )
        .properties(
            width=350,
            height=350,
            title="No Vaccination (R₀)"
        )
    )

    chart_yes = (
        alt.Chart(df_yes)
        .mark_line(point=True, color="#43A047", strokeWidth=3)
        .encode(
            x="Generation:O",
            y=y_axis,
            tooltip=["Generation", "Infected"]
        )
        .properties(
            width=350,
            height=350,
            title=f"With Vaccination (Rₑ = {Re:.2f})"
        )
    )

    # Display side-by-side
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_no, use_container_width=True)
    with col2:
        st.altair_chart(chart_yes, use_container_width=True)

    # Summary
    st.markdown("---")
    st.markdown(f"""
    ### Summary
    - **No vaccination:** {int(infected_no_vax[-1]):,} infections by generation {generations}.  
    - **With {coverage}% vaccination:** {int(infected_vax[-1]):,} infections.  
    - **Cumulative infections reduced** from {cumulative_no_vax:,} → {cumulative_vax:,}.  
    """)


# ============================================================
# TAB 2 — ANIMATED OUTBREAK COMPARISON
# ============================================================
with tab2:

    st.subheader("Animated Generation-by-Generation Outbreak")

    st.markdown("""
    This animation compares two outbreaks:
    - **No vaccination (R₀)**  
    - **With vaccination (Rₑ)**  
    """)

    disease2 = st.selectbox(
        "Disease (animation)", list(disease_r0.keys()), key="anim_disease"
    )

    R0_anim = disease_r0[disease2]

    coverage_anim = st.slider(
        "Vaccination Coverage (%)",
        0, 100, 75, key="anim_coverage"
    )

    Re_anim = R0_anim * (1 - coverage_anim/100)

    st.metric("R₀ (No Vax)", f"{R0_anim}")
    st.metric("Rₑ (With Vax)", f"{Re_anim:.2f}")

    max_gen_anim = st.slider(
        "Total generations to simulate",
        1, 12, 8, key="anim_gens"
    )

    if "anim_gen_state" not in st.session_state:
        st.session_state.anim_gen_state = 0

    colL, colR = st.columns(2)
    if colL.button("Next Generation →"):
        st.session_state.anim_gen_state = min(
            max_gen_anim, st.session_state.anim_gen_state + 1
        )

    if colR.button("Reset Animation"):
        st.session_state.anim_gen_state = 0

    curr = st.session_state.anim_gen_state
    st.write(f"### Current Generation: {curr}")

    # Calculate infections dynamically
    infections_no = [1]
    infections_yes = [1]

    for g in range(1, curr + 1):
        infections_no.append(infections_no[-1] * R0_anim)
        infections_yes.append(infections_yes[-1] * Re_anim)

    # Time to extinction
    extinction_msg = ""
    if Re_anim < 1:
        if infections_yes[-1] < 1:
            extinction_msg = "✔ Outbreak dies out by this generation."
        else:
            extinction_msg = "✔ Outbreak will eventually die out (Rₑ < 1)."
    else:
        extinction_msg = "⚠ Outbreak grows indefinitely (Rₑ ≥ 1)."

    st.info(extinction_msg)

    # Build DF for charts
    df_anim_no = pd.DataFrame({
        "Generation": list(range(curr + 1)),
        "Infected": infections_no
    })

    df_anim_yes = pd.DataFrame({
        "Generation": list(range(curr + 1)),
        "Infected": infections_yes
    })

    # Draw charts
    colA, colB = st.columns(2)
    with colA:
        st.altair_chart(
            alt.Chart(df_anim_no)
            .mark_line(point=True, color="red")
            .encode(x="Generation:O", y="Infected:Q")
            .properties(title="No Vaccination", height=350),
            use_container_width=True
        )

    with colB:
        st.altair_chart(
            alt.Chart(df_anim_yes)
            .mark_line(point=True, color="green")
            .encode(x="Generation:O", y="Infected:Q")
            .properties(title="With Vaccination", height=350),
            use_container_width=True
        )

    # Auto-play animation
    if st.button("Play Animation"):
        for step in range(curr, max_gen_anim + 1):
            time.sleep(1.0)  # slow mode (your choice)
            st.session_state.anim_gen_state = step
            st.experimental_rerun()


# ============================================================
# TAB 3 — SEIR VS EXPONENTIAL
# ============================================================
with tab3:

    st.subheader("SEIR vs Exponential Comparison")

    disease3 = st.selectbox(
        "Disease (SEIR)", list(disease_r0.keys()), key="seir_disease"
    )

    R0_seir = disease_r0[disease3]

    coverage_seir = st.slider(
        "Vaccination Coverage (%)",
        0, 100, 75, key="seir_coverage"
    )

    Re_seir = R0_seir * (1 - coverage_seir/100)

    days = st.slider("Days to simulate", 30, 200, 100)

    # SEIR parameters
    incubation = st.slider("Incubation period (days)", 2, 10, 4)
    infectious = st.slider("Infectious period (days)", 2, 14, 6)

    N = 1_000_000
    S0 = N - 10
    E0 = 5
    I0 = 5
    R0_start = 0

    beta = Re_seir / infectious
    sigma = 1/incubation
    gamma = 1/infectious

    S, E, I, R = [S0], [E0], [I0], [R0_start]

    for t in range(days):
        new_E = beta * S[-1] * I[-1] / N
        new_I = sigma * E[-1]
        new_R = gamma * I[-1]

        S.append(S[-1] - new_E)
        E.append(E[-1] + new_E - new_I)
        I.append(I[-1] + new_I - new_R)
        R.append(R[-1] + new_R)

    df = pd.DataFrame({"S": S, "E": E, "I": I, "R": R})

    exp_curve = [1 * (Re_seir**t) for t in range(days + 1)]
    df_exp = pd.DataFrame({"Day": list(range(days + 1)), "Exponential": exp_curve})

    colX, colY = st.columns(2)

    with colX:
        st.altair_chart(
            alt.Chart(df.reset_index())
            .mark_line()
            .encode(
                x="index",
                y="value:Q",
                color="variable:N"
            )
            .transform_fold(["S", "E", "I", "R"])
            .properties(height=350, title="SEIR Model"),
            use_container_width=True
        )

    with colY:
        st.altair_chart(
            alt.Chart(df_exp)
            .mark_line(color="orange")
            .encode(
                x="Day",
                y="Exponential:Q"
            )
            .properties(height=350, title="Exponential Model"),
            use_container_width=True
        )

    st.markdown("""
    ### Interpretation:
    - **SEIR outbreaks grow slower** due to exposed/incubation stages.  
    - **Exponential models assume immediate infectiousness**, so they grow faster.  
    - Vaccination reduces both SEIR and exponential growth by lowering Rₑ.  
    """)
