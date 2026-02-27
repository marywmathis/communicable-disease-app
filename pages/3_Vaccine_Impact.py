import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import networkx as nx
import plotly.graph_objects as go
import json
import math
import time

# ============================================================
# DISEASE PRESET R₀ VALUES
# ============================================================
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

# ============================================================
# REAL-WORLD VACCINATION PRESETS
# ============================================================
vacc_presets = {
    "MMR": 94,
    "DTaP": 90,
    "Polio": 85,
    "Varicella": 90,
    "Hib": 90,
    "HepB": 91,
    "PCV": 92,
}

# ============================================================
# PAGE HEADER
# ============================================================
st.header("Impact of Vaccination on Disease Spread")

st.write("""
This page models how vaccination changes:
- The **effective reproduction number** (Rₑ)  
- The **size and speed** of outbreaks  
- Whether the population reaches **herd immunity**  
- **Dynamic SEIR behavior**  
- **Transmission trees**  
""")

# ============================================================
# CREATE TABS
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "Basic Vaccination Impact",
    "SEIR vs Exponential Growth",
    "Transmission Tree"
])

# ============================================================
# ============================================================
# TAB 1 — BASIC VACCINATION IMPACT (FULLY FIXED)
# ============================================================
# ============================================================

with tab1:

    st.subheader("Basic Vaccination Impact")

    # -------------------------------
    # Disease selection
    # -------------------------------
    disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
    R0 = disease_r0[disease]

    st.write(f"**Baseline R₀ for {disease}: {R0}**")

    # -------------------------------
    # Vaccination Coverage Control
    # -------------------------------
    if "coverage_slider" not in st.session_state:
        st.session_state.coverage_slider = 75

    st.markdown("### Vaccination Coverage")

    colA, colB = st.columns([2, 3])

    with colA:
        coverage = st.slider(
            "Vaccination Coverage (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.coverage_slider,
            key="coverage_slider"
        )

    with colB:
        st.write("Preset Coverage Values:")
        preset = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True
        )

        if preset != "None":
            val = vacc_presets[preset]
            st.session_state.coverage_slider = val
            coverage = val
            st.success(f"Using preset: {preset} = {val}%")

    # -------------------------------
    # Herd Immunity Threshold
    # -------------------------------
    herd_threshold = (1 - 1 / R0) * 100
    st.metric("Herd Immunity Threshold", f"{herd_threshold:.1f}%")

    if coverage >= herd_threshold:
        st.success("Population exceeds herd immunity threshold.")
    else:
        st.warning("Population is below herd immunity threshold.")

    # -------------------------------
    # Effective Reproduction Number (Rₑ)
    # -------------------------------
    Re = R0 * (1 - coverage / 100)
    st.metric("Effective Rₑ", f"{Re:.2f}")

    # -------------------------------
    # Generations
    # -------------------------------
    generations = st.slider("Number of generations", 1, 12, 6)

    infected_no_vax = [1]
    infected_vax = [1]

    for g in range(1, generations + 1):
        infected_no_vax.append(infected_no_vax[-1] * R0)
        infected_vax.append(infected_vax[-1] * Re)

    cumulative_no = sum(infected_no_vax)
    cumulative_yes = sum(infected_vax)

    df_no = pd.DataFrame({"Generation": range(generations + 1), "Infected": infected_no_vax})
    df_yes = pd.DataFrame({"Generation": range(generations + 1), "Infected": infected_vax})

    # -------------------------------
    # Linear vs Log
    # -------------------------------
    scale = st.radio("Chart Scale", ["Linear", "Log Scale"], horizontal=True)

    y_axis = alt.Y(
        "Infected:Q",
        scale=alt.Scale(type="log") if scale == "Log Scale" else alt.Scale(type="linear")
    )

    chart_no = alt.Chart(df_no).mark_line(color="#E53935", point=True).encode(
        x="Generation:O",
        y=y_axis
    ).properties(title="No Vaccination (R₀)")

    chart_yes = alt.Chart(df_yes).mark_line(color="#43A047", point=True).encode(
        x="Generation:O",
        y=y_axis
    ).properties(title=f"With Vaccination (Rₑ = {Re:.2f})")

    colA, colB = st.columns(2)
    colA.altair_chart(chart_no, use_container_width=True)
    colB.altair_chart(chart_yes, use_container_width=True)

    # -------------------------------
    # Summary
    # -------------------------------
    st.markdown("### Summary")
    st.write(f"""
    - **No vaccination:** {int(infected_no_vax[-1]):,} infections  
    - **With vaccination:** {int(infected_vax[-1]):,} infections  
    - **Cumulative infections:**  
      - No vaccination: {cumulative_no:,}  
      - With vaccination: {cumulative_yes:,}  
    - Herd immunity threshold = **{herd_threshold:.1f}%**  
    """)

# ============================================================
# ============================================================
# TAB 2 — SEIR VS EXPONENTIAL GROWTH
# ============================================================
# ============================================================

with tab2:

    st.subheader("SEIR vs Exponential Growth")

    incubation = st.slider("Incubation period (days)", 1, 10, 4)
    infectious_period = st.slider("Infectious period (days)", 1, 20, 6)
    days = st.slider("Simulation duration (days)", 30, 200, 100)

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

    df = pd.DataFrame({"S": S, "E": E, "I": I, "R": R})

    chart = (
        alt.Chart(df.reset_index())
        .mark_line()
        .encode(
            x="index",
            y="value:Q",
            color="variable:N"
        )
        .transform_fold(["S", "E", "I", "R"])
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)

# ============================================================
# ============================================================
# TAB 3 — TRANSMISSION TREE
# ============================================================
# ============================================================

with tab3:

    st.subheader("Transmission Tree Visualization")

    # ----------------------------------------------------------
    # Controls
    # ----------------------------------------------------------
    layout_mode = st.radio("Layout", ["Hierarchical", "Radial"], horizontal=True)
    show_labels = st.checkbox("Show node labels", False)
    superspreader_pct = st.slider("Superspreader %", 0, 50, 10)
    vacc_pct = st.slider("Vaccination % (blocks onward spread)", 0, 80, 20)

    if "tree_gen" not in st.session_state:
        st.session_state.tree_gen = 0

    if st.button("Next Generation"):
        st.session_state.tree_gen = min(st.session_state.tree_gen + 1, 8)

    gen = st.session_state.tree_gen
    st.write(f"Showing generations 0 → {gen}")

    # ----------------------------------------------------------
    # Generate Tree
    # ----------------------------------------------------------
    def generate_tree(Re, max_gen, superspreader_pct, vacc_pct, max_nodes=2000):
        G = nx.DiGraph()
        G.add_node(0, generation=0, parent=None, vacc=False, super=False)
        node_id = 1
        current = [0]

        for gen in range(1, max_gen + 1):
            next_gen = []
            for parent in current:

                if G.nodes[parent]["vacc"]:
                    continue

                is_super = np.random.rand() < superspreader_pct / 100
                newR = int(Re * (3 if is_super else 1))
                newR = max(1, newR)

                for _ in range(newR):
                    if node_id > max_nodes:
                        return G

                    vacc_status = np.random.rand() < vacc_pct / 100

                    G.add_node(node_id,
                               generation=gen,
                               parent=parent,
                               vacc=vacc_status,
                               super=is_super)
                    G.add_edge(parent, node_id)

                    if not vacc_status:
                        next_gen.append(node_id)

                    node_id += 1

            current = next_gen

        return G

    G = generate_tree(Re, gen, superspreader_pct, vacc_pct)

    # ----------------------------------------------------------
    # Layouts
    # ----------------------------------------------------------
    def layout_h(G):
        pos = {}
        gens = {}
        for n, d in G.nodes(data=True):
            gens.setdefault(d["generation"], []).append(n)
        for g, nodes in gens.items():
            xs = np.linspace(-1, 1, len(nodes))
            for i, n in enumerate(nodes):
                pos[n] = (xs[i], -g)
        return pos

    def layout_r(G):
        pos = {}
        gens = {}
        for n, d in G.nodes(data=True):
            gens.setdefault(d["generation"], []).append(n)
        for g, nodes in gens.items():
            radius = g + 0.5
            angles = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
            for ang, n in zip(angles, nodes):
                pos[n] = (radius * math.cos(ang), radius * math.sin(ang))
        return pos

    pos = layout_h(G) if layout_mode == "Hierarchical" else layout_r(G)

    # ----------------------------------------------------------
    # Draw curved edges
    # ----------------------------------------------------------
    def curved_edge(x0, y0, x1, y1, steps=20):
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2 + 0.1
        xs, ys = [], []
        for t in np.linspace(0, 1, steps):
            xs.append((1-t)**2 * x0 + 2*(1-t)*t * xm + t**2 * x1)
            ys.append((1-t)**2 * y0 + 2*(1-t)*t * ym + t**2 * y1)
        return xs + [None], ys + [None]

    edge_x, edge_y = [], []
    for u, v in G.edges():
        xs, ys = curved_edge(pos[u][0], pos[u][1], pos[v][0], pos[v][1])
        edge_x += xs
        edge_y += ys

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                            line=dict(color="#BBB", width=1),
                            hoverinfo="none")

    node_x, node_y, col, size, hover = [], [], [], [], []

    for n, data in G.nodes(data=True):
        x, y = pos[n]
        node_x.append(x); node_y.append(y)
        col.append(-1 if data["vacc"] else data["generation"])
        size.append(22 if data["super"] else 14)
        hover.append(
            f"Node {n}<br>Gen {data['generation']}<br>"
            f"Super: {data['super']}<br>Vaccinated: {data['vacc']}"
        )

    colorscale = [
        [0.00, "#00AA00"],
        [0.01, "#FFFF00"],
        [0.25, "#FF9000"],
        [0.50, "#FF0000"],
        [0.75, "#8B00FF"],
        [1.00, "#002060"]
    ]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text" if show_labels else "markers",
        text=[str(n) for n in G.nodes()] if show_labels else None,
        marker=dict(
            size=size,
            color=col,
            colorscale=colorscale,
            cmin=-1,
            cmax=max(col),
            showscale=True,
            colorbar=dict(
                title="Legend",
                tickvals=list(range(-1, max(col)+1)),
                ticktext=["Vaccinated"] + [f"Gen {i}" for i in range(max(col)+1)]
            ),
            line=dict(color="black", width=1)
        ),
        hovertext=hover,
        hoverinfo="text"
    )

    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------------------
    # Export
    # ----------------------------------------------------------
    st.subheader("Export Options")
    fmt = st.selectbox("Export format", ["Interactive HTML", "JSON"])

    if st.button("Export"):

        if fmt == "JSON":
            data = json.dumps(nx.node_link_data(G), indent=2)
            st.download_button("Download JSON", data,
                               file_name="tree.json", mime="application/json")

        else:
            html = fig.to_html(include_plotlyjs="cdn")
            st.download_button("Download HTML", html,
                               file_name="tree.html", mime="text/html")

            st.info("Open the HTML file in a browser → click the camera icon to export PNG/SVG.")
