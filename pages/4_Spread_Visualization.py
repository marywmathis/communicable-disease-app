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
    "Pneumococcal (PCV)": 2
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

    # Track generation in session state
    if "current_gen" not in st.session_state:
        st.session_state.current_gen = 0

    if st.button("Next Generation →"):
        if st.session_state.current_gen < max_gen:
            st.session_state.current_gen += 1

    st.write(f"### Showing up to Generation: {st.session_state.current_gen}")

    # Compute infections
    infected = [1]
    for g in range(1, st.session_state.current_gen + 1):
        infected.append(infected[-1] * R0)

    df = pd.DataFrame({
        "Generation": list(range(st.session_state.current_gen + 1)),
        "Infected": infected
    })

    # Color gradient bar chart
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
    - Use lower or higher R₀ values to compare diseases.  
    """)

# -------------------------------------------------
# NODE TREE VISUALIZATION — FULL VERSION
# -------------------------------------------------
else:
    ###############################################
    # NODE TREE MODE — FULL IMPLEMENTATION
    ###############################################

    st.subheader("Node Tree Spread Visualization")

    st.markdown("""
    This visualization shows who infected whom using a **true branching transmission tree**.

    You may choose:
    - hierarchical layout (Ebola/SARS-style)  
    - radial layout (infection explosion)  
    - manual or auto animation  
    """)

    # ------------------------------------------------
    # TREE GENERATION LOGIC
    # ------------------------------------------------
    def generate_tree(R0, max_gen=6, max_nodes=1500):
        G = nx.DiGraph()
        G.add_node(0, generation=0, parent=None)  # patient zero

        node_id = 1
        current_gen = [0]

        for gen in range(1, max_gen + 1):
            next_gen = []
            for parent in current_gen:
                for _ in range(int(R0)):
                    if node_id > max_nodes:
                        return G
                    G.add_node(node_id, generation=gen, parent=parent)
                    G.add_edge(parent, node_id)
                    next_gen.append(node_id)
                    node_id += 1
            current_gen = next_gen

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
            radius = gen * 0.5 + 0.1
            angles = np.linspace(0, 2*np.pi, len(nodes), endpoint=False)
            for angle, node in zip(angles, nodes):
                pos[node] = (radius * np.cos(angle), radius * np.sin(angle))

        return pos

    # ------------------------------------------------
    # DRAWING FUNCTION
    # ------------------------------------------------
    def draw_tree(G, pos):
        # Edges
        edge_x, edge_y = [], []

        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(width=1, color="#999"),
            hoverinfo="none"
        )

        # Nodes
        node_x, node_y, colors, hover = [], [], [], []

        for n, data in G.nodes(data=True):
            x, y = pos[n]
            node_x.append(x)
            node_y.append(y)
            colors.append(data["generation"])

            parent = data["parent"]
            hover.append(
                f"<b>Node:</b> {n}<br>"
                f"<b>Generation:</b> {data['generation']}<br>"
                f"<b>Parent:</b> {parent}"
            )

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers",
            marker=dict(
                size=14,
                color=colors,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Generation"),
                line=dict(width=1, color="black")
            ),
            hovertext=hover,
            hoverinfo="text"
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(t=40, b=20, l=20, r=20)
        )
        return fig

    # ------------------------------------------------
    # USER OPTIONS
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

    # MANUAL ADVANCE
    if animation_mode == "Manual (Next Generation)":
        if st.button("Next Generation →"):
            if st.session_state.current_gen_tree < max_gen:
                st.session_state.current_gen_tree += 1

    # AUTO ANIMATION
    elif animation_mode == "Auto-Play":
        play = st.checkbox("Play", value=False)
        if play:
            for g in range(st.session_state.current_gen_tree, max_gen + 1):
                st.session_state.current_gen_tree = g
                time.sleep(0.8)
                st.experimental_rerun()

    # NO ANIMATION
    else:
        st.session_state.current_gen_tree = max_gen

    current_gen = st.session_state.current_gen_tree
    st.write(f"### Showing generations 0 → {current_gen}")

    # BUILD TREE
    G = generate_tree(R0, max_gen=current_gen)

    # LAYOUT
    pos = (
        layout_tree_hierarchical(G)
        if layout_mode.startswith("Hierarchical")
        else layout_tree_radial(G)
    )

    # DRAW FIGURE
    fig = draw_tree(G, pos)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    ### Teaching Notes
    - Hierarchical layout mirrors CDC outbreak diagrams.
    - Radial layout illustrates infection explosion speed.
    - Manual mode allows step-by-step classroom demonstration.
    - Auto-play helps show exponential acceleration visually.
    """)
