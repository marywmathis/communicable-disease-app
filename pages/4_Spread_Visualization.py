import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import networkx as nx
import time

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
    "Pneumococcal (PCV)": 2,
    "COVID-19 (Ancestral Wuhan)": 3,
    "COVID-19 Delta Variant": 6,
    "COVID-19 Omicron BA.1": 9,
    "COVID-19 Omicron BA.5": 12,
}

# -------------------------------------------------
# PAGE TITLE
# -------------------------------------------------
st.header("Spread Visualization (Animated or Node Tree)")

st.markdown("""
Use the dropdown below to explore either:
- an **animated generation-by-generation outbreak**, or  
- a **true branching infection tree** with hierarchical or radial layout.
""")

# -------------------------------------------------
# VISUALIZATION MODE SELECTOR
# -------------------------------------------------
mode = st.selectbox(
    "Choose visualization mode:",
    ["Animated Spread (Click to Advance)", "Node Tree Spread"]
)

# -------------------------------------------------
# SELECT DISEASE + R₀
# -------------------------------------------------
disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
R0_default = float(disease_r0[disease])

R0 = st.slider(
    "R₀ (Basic Reproduction Number)",
    min_value=1.0, max_value=20.0,
    value=R0_default, step=0.1
)

max_gen = 8  # Maximum number of generations

# -------------------------------------------------
# ANIMATED MODE
# -------------------------------------------------
if mode == "Animated Spread (Click to Advance)":
    
    st.subheader("Animated Spread — Click to Advance")

    if "current_gen" not in st.session_state:
        st.session_state.current_gen = 0

    if st.button("Next Generation →"):
        if st.session_state.current_gen < max_gen:
            st.session_state.current_gen += 1

    st.write(f"### Showing up to Generation: {st.session_state.current_gen}")

    infected = [1]
    for g in range(1, st.session_state.current_gen + 1):
        infected.append(infected[-1] * R0)

    df = pd.DataFrame({
        "Generation": list(range(st.session_state.current_gen + 1)),
        "Infected": infected
    })

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="Generation:O",
            y="Infected:Q",
            color=alt.Color(
                "Infected:Q",
                scale=alt.Scale(scheme="redyellowgreen"),
                legend=None
            )
        )
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)
    st.metric("Total Infected So Far", f"{int(infected[-1]):,}")

    st.markdown("""
    ### Teaching Notes
    - Click *Next Generation* to illustrate exponential growth visually.  
    """)

# -------------------------------------------------
# NODE TREE VISUALIZATION — FULL VERSION
# -------------------------------------------------
else:
    st.subheader("Node Tree Spread Visualization")

    st.markdown("""
    This visualization shows who infected whom using a **branching transmission tree**.

    You may choose:
    - hierarchical layout (Ebola/SARS-style)
    - radial layout (infection explosion)
    - manual or auto animation
    """)

    # ------------------------------------------------
    # GENERATE THE TREE
    # ------------------------------------------------
    def generate_tree(R0, max_gen=6, max_nodes=1500):
        G = nx.DiGraph()
        G.add_node(0, generation=0, parent=None)

        node_id = 1
        current_gen_nodes = [0]

        for gen in range(1, max_gen + 1):
            next_gen_nodes = []
            for parent in current_gen_nodes:
                for _ in range(int(R0)):
                    if node_id > max_nodes:
                        return G
                    G.add_node(node_id, generation=gen, parent=parent)
                    G.add_edge(parent, node_id)
                    next_gen_nodes.append(node_id)
                    node_id += 1
            current_gen_nodes = next_gen_nodes

        return G

    # ------------------------------------------------
    # LAYOUT FUNCTIONS
    # ------------------------------------------------
    def layout_tree_hierarchical(G):
        pos = {}
        gens = {}

        for node, data in G.nodes(data=True):
            gens.setdefault(data["generation"], []).append(node)

        for gen, nodes in gens.items():
            xs = np.linspace(-1, 1, len(nodes))
            for i, node in enumerate(nodes):
                pos[node] = (xs[i], -gen)

        return pos

    def layout_tree_radial(G):
        pos = {}
        gens = {}

        for node, data in G.nodes(data=True):
            gens.setdefault(data["generation"], []).append(node)

        for gen, nodes in gens.items():
            radius = 0.4 + gen * 0.5
            angles = np.linspace(0, 2*np.pi, len(nodes), endpoint=False)
            for angle, node in zip(angles, nodes):
                pos[node] = (radius * np.cos(angle), radius * np.sin(angle))

        return pos

    # ------------------------------------------------
    # DRAWING FUNCTION
    # ------------------------------------------------
    def draw_tree(G, pos):
        edge_x, edge_y = [], []

        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(width=1, color="#AAAAAA"),
            hoverinfo="none"
        )

        node_x, node_y, generations, hovertext = [], [], [], []

        for node, data in G.nodes(data=True):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            generations.append(data["generation"])
            hovertext.append(
                f"<b>Node:</b> {node}<br>"
                f"<b>Generation:</b> {data['generation']}<br>"
                f"<b>Parent:</b> {data['parent']}"
            )

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers",
            hovertext=hovertext,
            hoverinfo="text",
            marker=dict(
                size=14,
                color=generations,
                colorscale=[
                    [0.00, "#FFFF00"],  # bright yellow (Gen 0)
                    [0.25, "#FFB000"],  # orange
                    [0.50, "#FF0000"],  # red
                    [0.75, "#8B00FF"],  # purple
                    [1.00, "#002080"],  # deep blue (Gen 4+)
                ],
                cmin=0,
                cmax=max(generations),
                showscale=True,
                colorbar=dict(
                    title="Generation",
                    ticks="outside",
                    tickvals=list(range(max(generations) + 1)),
                    ticktext=[str(i) for i in range(max(generations) + 1)],
                ),
                line=dict(width=1, color="black")
            )
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    # ------------------------------------------------
    # USER CONTROLS
    # ------------------------------------------------
    layout_mode = st.radio(
        "Choose layout:",
        ["Hierarchical (CDC-style)", "Radial (infection explosion)"]
    )

    animation_mode = st.radio(
        "Animation mode:",
        ["Manual (Next Generation)", "Auto-Play", "None"]
    )

    if "current_gen_tree" not in st.session_state:
        st.session_state.current_gen_tree = 0

    if animation_mode == "Manual (Next Generation)":
        if st.button("Next Generation →"):
            if st.session_state.current_gen_tree < max_gen:
                st.session_state.current_gen_tree += 1

    elif animation_mode == "Auto-Play":
        play = st.checkbox("Play", value=False)
        if play:
            for g in range(st.session_state.current_gen_tree, max_gen + 1):
                st.session_state.current_gen_tree = g
                time.sleep(0.7)
                st.experimental_rerun()

    else:
        st.session_state.current_gen_tree = max_gen

    current_gen = st.session_state.current_gen_tree
    st.write(f"### Showing generations 0 → {current_gen}")

    G = generate_tree(R0, max_gen=current_gen)

    pos = (
        layout_tree_hierarchical(G)
        if layout_mode.startswith("Hierarchical")
        else layout_tree_radial(G)
    )

    fig = draw_tree(G, pos)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    ### Teaching Notes
    - Yellow = index case (Gen 0)
    - Orange → Red → Purple → Blue = deeper generations
    - Hierarchical view mirrors CDC diagrams.
    - Radial view illustrates infection explosion visually.
    """)
