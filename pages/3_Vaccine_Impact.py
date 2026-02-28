################################################################################
# 3_Vaccine_Impact.py — COMPLETE, FIXED, FULLY SYNCHRONIZED VERSION
################################################################################

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import networkx as nx
import plotly.graph_objects as go
import math

# =============================================================================
# BASELINE R₀ VALUES FOR DISEASES
# =============================================================================
disease_r0 = {
    # Vaccine-preventable diseases
    "Measles (MMR)": 15,
    "Pertussis (DTaP)": 12,
    "Polio (IPV)": 6,
    "Varicella (Chickenpox)": 10,
    "Hepatitis B (HepB)": 3,
    "HPV": 3,
    "Hib": 1.3,
    "Pneumococcal (PCV)": 2,

    # COVID-19 Variants
    "COVID-19 (Original Wuhan 2020)": 2.5,
    "COVID-19 (Alpha Variant)": 4,
    "COVID-19 (Delta Variant)": 6.5,
    "COVID-19 (Omicron BA.1)": 9,
    "COVID-19 (Omicron BA.5)": 12,
    "COVID-19 (Omicron XBB/BQ)": 13,
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
Explore:
- How vaccination coverage affects **Rₑ**
- Herd immunity thresholds
- Exponential vs SEIR disease progression
- Transmission network structures
""")

# =============================================================================
# CREATE TABS
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

    disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
    R0 = disease_r0[disease]
    st.write(f"**Baseline R₀ for {disease}: {R0}**")

    # Session state
    if "coverage_value" not in st.session_state:
        st.session_state.coverage_value = 75
    if "preset_choice" not in st.session_state:
        st.session_state.preset_choice = "None"
    if "override_preset" not in st.session_state:
        st.session_state.override_preset = False

    if st.session_state.override_preset:
        st.session_state.preset_choice = "None"
        st.session_state.override_preset = False

    st.markdown("### Vaccination Coverage Settings")
    colA, colB = st.columns([2, 3])

    # PRESET SELECTOR
    with colB:
        preset = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True,
            key="preset_choice"
        )
        if preset != "None":
            st.session_state.coverage_value = vacc_presets[preset]
            st.success(f"Preset applied: {preset} = {vacc_presets[preset]}%")

    # SLIDER
    with colA:
        slider_val = st.slider(
            "Vaccination Coverage (%)",
            0, 100,
            value=st.session_state.coverage_value,
            key="coverage_slider"
        )
        if slider_val != st.session_state.coverage_value:
            st.session_state.override_preset = True

        st.session_state.coverage_value = slider_val

    coverage = st.session_state.coverage_value

    # Herd immunity threshold
    herd_threshold = (1 - 1 / R0) * 100
    st.metric("Herd Immunity Threshold", f"{herd_threshold:.1f}%")

    if coverage >= herd_threshold:
        st.success("Population exceeds herd immunity threshold.")
    else:
        st.warning("Population is below herd immunity threshold.")

    # Effective R
    Re = R0 * (1 - coverage / 100)
    st.metric("Effective Rₑ", f"{Re:.2f}")

    # Growth modeling
    generations = st.slider("Number of generations", 1, 12, 6)

    infected_no = [1]
    infected_yes = [1]

    for g in range(1, generations + 1):
        infected_no.append(infected_no[-1] * R0)
        infected_yes.append(infected_yes[-1] * Re)

    df_no = pd.DataFrame({"Generation": range(generations + 1), "Infected": infected_no})
    df_yes = pd.DataFrame({"Generation": range(generations + 1), "Infected": infected_yes})

    # Scale toggle
    scale = st.radio("Chart Scale", ["Linear", "Log Scale"], horizontal=True)

    y_axis = alt.Y(
        "Infected:Q",
        scale=alt.Scale(type="log") if scale == "Log Scale" else alt.Scale(type="linear")
    )

    # Charts
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

    # Summary
    st.markdown("### Summary")
    st.write(f"""
    **Final generation infections**
    - No vaccination: {infected_no[-1]:,}
    - With vaccination: {infected_yes[-1]:,}

    **Cumulative infections**
    - No vaccination: {sum(infected_no):,}
    - With vaccination: {sum(infected_yes):,}
    """)

################################################################################
# TAB 2 — FIXED SEIR VS EXPONENTIAL GROWTH
################################################################################
################################################################################
# TAB 2 — SEIR VS EXPONENTIAL GROWTH (FINAL FIX — NO transform_fold)
################################################################################
with tab2:

    st.subheader("SEIR vs Exponential Growth")

    st.write("""
    **SEIR Model Definitions**
    - **S** = Susceptible  
    - **E** = Exposed  
    - **I** = Infectious  
    - **R** = Recovered  
    """)

    # User inputs
    days = st.slider("Simulation days", 30, 200, 120)
    incubation = st.slider("Incubation period (days)", 1, 14, 4)
    infectious_period = st.slider("Infectious period (days)", 1, 20, 6)

    # SEIR parameters
    N = 1_000_000
    I0, E0 = 10, 5
    S0 = N - I0 - E0

    beta = Re / infectious_period
    sigma = 1 / incubation
    gamma = 1 / infectious_period

    S, E, I, R = [S0], [E0], [I0], [0]

    for t in range(days):
        new_E = beta * S[-1] * I[-1] / N
        new_I = sigma * E[-1]
        new_R = gamma * I[-1]

        S.append(S[-1] - new_E)
        E.append(E[-1] + new_E - new_I)
        I.append(I[-1] + new_I - new_R)
        R.append(R[-1] + new_R)

    # Build DataFrame
    df = pd.DataFrame({
        "Day": range(days + 1),
        "Susceptible": S,
        "Exposed": E,
        "Infectious": I,
        "Recovered": R
    })

    # 🔥 FIX: Melt BEFORE passing to Altair — safest for v6
    df_long = df.melt(
        id_vars="Day",
        value_vars=["Susceptible", "Exposed", "Infectious", "Recovered"],
        var_name="State",
        value_name="Population"
    )

    # Clean, safe Altair chart (no fold, no reserved names)
    chart = (
        alt.Chart(df_long)
        .mark_line()
        .encode(
            x=alt.X("Day:Q", title="Day"),
            y=alt.Y("Population:Q", title="Population"),
            color=alt.Color(
                "State:N",
                title="SEIR State",
                scale=alt.Scale(range=[
                    "#2E86C1",  # S
                    "#F1C40F",  # E
                    "#E74C3C",  # I
                    "#27AE60",  # R
                ])
            ),
            tooltip=["Day:Q", "State:N", "Population:Q"]
        )
        .properties(
            height=500,
            title="SEIR Epidemic Curve (Validated for Altair v6)"
        )
    )

    st.altair_chart(chart, use_container_width=True)
################################################################################
# TAB 3 — TRANSMISSION TREE
################################################################################
with tab3:

    st.subheader("Transmission Tree Visualization")

    def generate_tree(Re, max_gen=5, max_nodes=1000):
        G = nx.DiGraph()
        G.add_node(0, generation=0)
        node_id = 1
        current = [0]

        for g in range(1, max_gen + 1):
            next_gen = []
            for parent in current:
                newR = max(1, int(Re))
                for _ in range(newR):
                    if node_id > max_nodes:
                        return G
                    G.add_node(node_id, generation=g)
                    G.add_edge(parent, node_id)
                    next_gen.append(node_id)
                    node_id += 1
            current = next_gen
        return G

    G = generate_tree(Re)
    pos = nx.kamada_kawai_layout(G)

    # Edges
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # Nodes
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_gen = [G.nodes[n]["generation"] for n in G.nodes()]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="gray", width=1),
        hoverinfo="none"
    ))

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        marker=dict(
            size=10,
            color=node_gen,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Generation")
        ),
        hoverinfo="text",
        text=[f"Node {n} (Gen {G.nodes[n]['generation']})" for n in G.nodes()]
    ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600,
        plot_bgcolor="white",
        margin=dict(t=30, b=20, l=20, r=20)
    )

    st.plotly_chart(fig, use_container_width=True)




