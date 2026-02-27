################################################################################
# 3_Vaccine_Impact.py — FULLY REWRITTEN, CLEAN, NO SESSION ERRORS, 3 TABS
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
    # Safe session variable for coverage value
    # -------------------------------------------------------------------------
    if "coverage_value" not in st.session_state:
        st.session_state.coverage_value = 75

    st.markdown("### Vaccination Coverage Settings")

    colA, colB = st.columns([2, 3])

    # SLIDER
    with colA:
        slider_value = st.slider(
            "Vaccination Coverage (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.coverage_value
        )
        st.session_state.coverage_value = slider_value

    # PRESETS
    with colB:
        st.write("Preset Coverage Values:")
        preset_choice = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True
        )

        if preset_choice != "None":
            preset_val = vacc_presets[preset_choice]
            st.session_state.coverage_value = preset_val
            st.success(f"Using preset: {preset_choice} = {preset_val}%")

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
    # Effective Reproduction Number (Rₑ)
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

    col1, col2 = st.columns(2)
    col1.altair_chart(chart_no, use_container_width=True)
    col2.altair_chart(chart_yes, use_container_width=True)

    st.markdown("### Summary")
    st.write(f"""
    - **Final generation infections:**  
      - No vaccination: {infected_no[-1]:,}  
      - With vaccination: {infected_yes[-1]:,}  
    - **Cumulative infections:**  
      - No vaccination: {sum(infected_no):,}  
      - With vaccination: {sum(infected_yes):,}  
    """)

################################################################################
# TAB 2 — SEIR VS EXPONENTIAL
################################################################################
with tab2:

    st.subheader("SEIR Model vs Exponential Growth")

    incubation = st.slider("Incubation period (days)", 1, 10, 4)
    infectious_period = st.slider("Infectious period (days)", 1, 20, 6)
    days = st.slider("Simulation duration (days)", 30, 200, 100)

    # initial population
    N = 1_000_000
    I0, E0 = 10, 5
    S0 = N - I0 - E0

    beta = Re / infectious_period
    sigma = 1 / incubation
    gamma = 1 / infectious_period

    S, E, I, R = [S0], [E0], [I0], [0]

    for t in range(days):
        new_exposed = beta * S[-1] * I[-1] / N
        new_infectious = sigma * E[-1]
        new_recovered = gamma * I[-1]

        S.append(S[-1] - new_exposed)
        E.append(E[-1] + new_exposed - new_infectious)
        I.append(I[-1] + new_infectious - new_recovered)
        R.append(R[-1] + new_recovered)

    df = pd.DataFrame({"S": S, "E": E, "I": I, "R": R})

    chart = (
        alt.Chart(df.reset_index())
        .mark_line()
        .encode(
            x="index:Q",
            y="value:Q",
            color="variable:N"
        )
        .transform_fold(["S", "E", "I", "R"])
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)

################################################################################
# TAB 3 — TRANSMISSION TREE
################################################################################
with tab3:

    st.subheader("Transmission Tree Visualization")

    layout_mode = st.radio("Layout", ["Hierarchical", "Radial"], horizontal=True)
    show_labels = st.checkbox("Show node labels", False)
    superspreader_pct = st.slider("Superspreader %", 0, 50, 10)
    vacc_pct = st.slider("Vaccination % (blocks spread)", 0, 80, 20)

    if "tree_gen" not in st.session_state:
        st.session_state.tree_gen = 0

    if st.button("Next Generation →"):
        st.session_state.tree_gen += 1

    gen = st.session_state.tree_gen
    st.write(f"Showing generations 0 → {gen}")

    # -------------------------------------------------------------------------
    # Generate transmission tree
    # -------------------------------------------------------------------------
    def generate_tree(Re, max_gen, superspreader_pct, vacc_pct, max_nodes=2000):
        G = nx.DiGraph()
        G.add_node(0, generation=0, vacc=False, super=False)
        next_id = 1
        frontier = [0]

        for g in range(1, max_gen + 1):
            new_frontier = []
            for parent in frontier:

                if G.nodes[parent]["vacc"]:
                    continue

                is_super = (np.random.rand() < superspreader_pct/100)
                effective_R = int(Re * (3 if is_super else 1))
                effective_R = max(1, effective_R)

                for _ in range(effective_R):
                    if next_id > max_nodes:
                        return G

                    vaccinated = (np.random.rand() < vacc_pct/100)
                    G.add_node(next_id,
                               generation=g,
                               vacc=vaccinated,
                               super=is_super)
                    G.add_edge(parent, next_id)

                    if not vaccinated:
                        new_frontier.append(next_id)

                    next_id += 1

            frontier = new_frontier

        return G

    G = generate_tree(Re, gen, superspreader_pct, vacc_pct)

    # -------------------------------------------------------------------------
    # Layout functions
    # -------------------------------------------------------------------------
    def hierarchical(G):
        pos = {}
        gens = {}
        for n, d in G.nodes(data=True):
            gens.setdefault(d["generation"], []).append(n)
        for g, nodes in gens.items():
            xs = np.linspace(-1, 1, len(nodes))
            for i, node in enumerate(nodes):
                pos[node] = (xs[i], -g)
        return pos

    def radial(G):
        pos = {}
        gens = {}
        for n, d in G.nodes(data=True):
            gens.setdefault(d["generation"], []).append(n)
        for g, nodes in gens.items():
            radius = g + 0.5
            angles = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
            for ang, node in zip(angles, nodes):
                pos[node] = (radius * math.cos(ang), radius * math.sin(ang))
        return pos

    pos = hierarchical(G) if layout_mode == "Hierarchical" else radial(G)

    # -------------------------------------------------------------------------
    # Draw edges (curved)
    # -------------------------------------------------------------------------
    def curved_edge(x0, y0, x1, y1):
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2 + 0.1
        xs, ys = [], []
        for t in np.linspace(0, 1, 20):
            xs.append((1 - t)**2 * x0 + 2 * (1 - t) * t * xm + t**2 * x1)
            ys.append((1 - t)**2 * y0 + 2 * (1 - t) * t * ym + t**2 * y1)
        xs.append(None); ys.append(None)
        return xs, ys

    edge_x, edge_y = [], []
    for u, v in G.edges():
        xs, ys = curved_edge(pos[u][0], pos[u][1], pos[v][0], pos[v][1])
        edge_x += xs
        edge_y += ys

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="#BBBBBB", width=1),
        hoverinfo="none"
    )

    # -------------------------------------------------------------------------
    # Node scatter
    # -------------------------------------------------------------------------
    node_x, node_y, colors, sizes, hover = [], [], [], [], []

    for n, data in G.nodes(data=True):
        x, y = pos[n]
        node_x.append(x); node_y.append(y)

        if data["vacc"]:
            colors.append(-1)
        else:
            colors.append(data["generation"])

        sizes.append(22 if data["super"] else 14)

        hover.append(
            f"Node {n}<br>"
            f"Generation: {data['generation']}<br>"
            f"Vaccinated: {data['vacc']}<br>"
            f"Superspreader: {data['super']}"
        )

    colorscale = [
        [0.00, "#00AA00"],
        [0.01, "#FFFF00"],
        [0.25, "#FF8800"],
        [0.50, "#FF0000"],
        [0.75, "#8B00FF"],
        [1.00, "#002080"],
    ]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text" if show_labels else "markers",
        text=[str(n) for n in G.nodes()] if show_labels else None,
        marker=dict(
            size=sizes,
            color=colors,
            colorscale=colorscale,
            cmin=-1,
            cmax=max(colors),
            showscale=True,
            colorbar=dict(
                title="Legend",
                tickvals=list(range(-1, max(colors)+1)),
                ticktext=["Vaccinated"] + [f"Gen {i}" for i in range(max(colors)+1)]
            ),
            line=dict(color="black", width=1)
        ),
        hovertext=hover,
        hoverinfo="text"
    )

    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(
        height=600,
        showlegend=False,
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # Export Options
    # -------------------------------------------------------------------------
    st.subheader("Export Options")
    fmt = st.selectbox("Choose export format:", ["Interactive HTML", "JSON"])

    if st.button("Export"):
        if fmt == "JSON":
            obj = json.dumps(nx.node_link_data(G), indent=2)
            st.download_button("Download JSON", obj, "tree.json", "application/json")
        else:
            html = fig.to_html(include_plotlyjs="cdn")
            st.download_button("Download HTML", html, "tree.html", "text/html")
            st.info("Open the HTML file → use camera icon for PNG/SVG export.")
