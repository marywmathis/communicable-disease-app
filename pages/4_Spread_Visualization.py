import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import networkx as nx
import time
import math

# ====================================================
# DISEASE PRESET R0 VALUES
# ====================================================
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

# ====================================================
# PAGE TITLE
# ====================================================
st.header("Spread Visualization (Animated or Node Tree)")

st.markdown("""
Explore two different epidemic visualization tools:

### **1. Animated outbreak simulation**
Shows exponential growth generation-by-generation.

### **2. Node tree transmission map**
A realistic branching diagram showing:
- parental transmission
- superspreaders
- vaccination effects
- hierarchical (CDC-style) or radial layouts  
- curved edges  
""")

# ====================================================
# MODE SELECTOR
# ====================================================
mode = st.selectbox(
    "Choose visualization mode:",
    ["Animated Spread (Click to Advance)", "Node Tree Spread"]
)

# ====================================================
# SELECT DISEASE + R0
# ====================================================
disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
R0_default = disease_r0[disease]

R0 = st.slider("R₀ (Basic Reproduction Number)", 1.0, 20.0, float(R0_default), 0.1)

max_gen = 8  # consistent across modes

# ====================================================
# 1. ANIMATED GENERATION-BY-GENERATION MODE
# ====================================================
if mode == "Animated Spread (Click to Advance)":

    st.subheader("Animated Spread — Click to Advance")

    if "anim_gen" not in st.session_state:
        st.session_state.anim_gen = 0

    if st.button("Next Generation →"):
        if st.session_state.anim_gen < max_gen:
            st.session_state.anim_gen += 1

    gen = st.session_state.anim_gen
    st.write(f"### Showing up to Generation: {gen}")

    infected = [1]
    for g in range(1, gen + 1):
        infected.append(infected[-1] * R0)

    df = pd.DataFrame({"Generation": list(range(gen + 1)), "Infected": infected})

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="Generation:O",
            y="Infected:Q",
            color=alt.Color("Infected:Q", scale=alt.Scale(scheme="redyellowgreen"))
        )
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)
    st.metric("Total Infected So Far", f"{int(infected[-1]):,}")

    st.markdown("""
    ### Teaching Notes
    - Excellent for demonstrating exponential growth.
    - Measles and Omicron variants demonstrate rapid increases.
    """)

# ====================================================
# 2. NODE TREE MODE
# ====================================================
else:
    st.subheader("Node Tree Spread Visualization")

    # ----------------------------
    # USER OPTIONS
    # ----------------------------

    layout_mode = st.radio(
        "Choose layout:",
        ["Hierarchical (CDC-style)", "Radial"]
    )

    animation_mode = st.radio(
        "Animation mode:",
        ["Manual (Next Generation)", "Auto-Play", "None"]
    )

    show_labels = st.checkbox("Show node labels", value=False)

    superspreader_pct = st.slider("Superspreader %", 0, 50, 10)
    vacc_pct = st.slider("Vaccination % (stops transmission)", 0, 80, 20)

    horiz = st.slider("Horizontal spacing (hierarchical)", 0.2, 3.0, 1.0)
    vert = st.slider("Vertical spacing (hierarchical)", 0.3, 2.0, 1.0)
    radial_scale = st.slider("Radial scale (radial layout)", 0.3, 2.0, 1.0)

    # ----------------------------
    # SESSION STATE FOR GENERATIONS
    # ----------------------------
    if "tree_gen" not in st.session_state:
        st.session_state.tree_gen = 0

    if animation_mode == "Manual (Next Generation)":
        if st.button("Next Generation →"):
            if st.session_state.tree_gen < max_gen:
                st.session_state.tree_gen += 1

    elif animation_mode == "Auto-Play":
        play = st.checkbox("Play", value=False)
        if play:
            for g in range(st.session_state.tree_gen, max_gen + 1):
                st.session_state.tree_gen = g
                time.sleep(0.7)
                st.experimental_rerun()

    else:
        st.session_state.tree_gen = max_gen

    curr_gen = st.session_state.tree_gen
    st.write(f"### Showing generations 0 → {curr_gen}")

    # ====================================================
    # GENERATE TREE WITH SUPERSPREADERS & VACCINATION
    # ====================================================
    def generate_tree(R0, max_gen, superspreader_pct, vacc_pct, max_nodes=1800):
        """Creates a branching transmission tree."""
        G = nx.DiGraph()
        G.add_node(0, generation=0, parent=None, vacc=False, super=False)

        node_id = 1
        current = [0]

        for gen in range(1, max_gen + 1):
            next_gen = []

            for parent in current:

                parent_is_vacc = G.nodes[parent]["vacc"]
                if parent_is_vacc:
                    continue  # vaccinated → no children

                # Assign superspreader status
                is_super = np.random.rand() < (superspreader_pct / 100)
                new_R0 = int(R0 * (3 if is_super else 1))

                for _ in range(new_R0):
                    if node_id > max_nodes:
                        return G

                    vacc_status = np.random.rand() < (vacc_pct / 100)

                    G.add_node(
                        node_id,
                        generation=gen,
                        parent=parent,
                        vacc=vacc_status,
                        super=is_super
                    )
                    G.add_edge(parent, node_id)

                    if not vacc_status:
                        next_gen.append(node_id)

                    node_id += 1

            current = next_gen

        return G

    # ====================================================
    # LAYOUT FUNCTIONS
    # ====================================================

    def layout_hierarchy(G, horiz, vert):
        pos = {}
        gens = {}

        for n, d in G.nodes(data=True):
            gens.setdefault(d["generation"], []).append(n)

        for gen, nodes in gens.items():
            xs = np.linspace(-horiz, horiz, len(nodes))
            for i, n in enumerate(nodes):
                pos[n] = (xs[i], -gen * vert)

        return pos

    def layout_radial(G, radial_scale):
        pos = {}
        gens = {}

        for n, d in G.nodes(data=True):
            gens.setdefault(d["generation"], []).append(n)

        for gen, nodes in gens.items():
            radius = (gen + 0.5) * radial_scale
            angles = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
            for angle, n in zip(angles, nodes):
                pos[n] = (radius * math.cos(angle), radius * math.sin(angle))

        return pos

    # ====================================================
    # CURVED EDGE GENERATOR
    # ====================================================
    def curved_edge(x0, y0, x1, y1, steps=20):
        """Generate curved Bezier-like arc."""
        xm = (x0 + x1) / 2
        ym = (y0 + y1) / 2 - 0.2  # upward bow
        xs, ys = [], []
        for t in np.linspace(0, 1, steps):
            bx = (1 - t)**2 * x0 + 2 * (1 - t) * t * xm + t**2 * x1
            by = (1 - t)**2 * y0 + 2 * (1 - t) * t * ym + t**2 * y1
            xs.append(bx); ys.append(by)
        return xs + [None], ys + [None]

    # ====================================================
    # DRAW TREE
    # ====================================================
    def draw_tree(G, pos, show_labels):

        edge_x, edge_y = [], []

        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            xs, ys = curved_edge(x0, y0, x1, y1)
            edge_x += xs
            edge_y += ys

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(width=1, color="#cccccc"),
            hoverinfo="none"
        )

        node_x, node_y, color_vals, hovertext, size_vals = [], [], [], [], []

        for node, data in G.nodes(data=True):
            x, y = pos[node]
            node_x.append(x); node_y.append(y)

            # Vaccinated nodes = green
            if data["vacc"]:
                color_vals.append(-1)
            else:
                color_vals.append(data["generation"])

            size_vals.append(22 if data["super"] else 14)

            hovertext.append(
                f"<b>Node:</b> {node}<br>"
                f"Generation: {data['generation']}<br>"
                f"Vaccinated: {data['vacc']}<br>"
                f"Superspreader: {data['super']}<br>"
                f"Parent: {data['parent']}"
            )

        # CUSTOM COLOR SCALE (vaccinated = green)
        full_colorscale = [
            [0.00, "#00AA00"],   # VACCINATED overridden separately
            [0.01, "#FFFF00"],   # Gen 0 = yellow
            [0.25, "#FFB000"],
            [0.50, "#FF0000"],
            [0.75, "#8B00FF"],
            [1.00, "#002080"],
        ]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text" if show_labels else "markers",
            hovertext=hovertext,
            hoverinfo="text",
            text=[str(n) for n in G.nodes()] if show_labels else None,
            textposition="top center",
            marker=dict(
                size=size_vals,
                color=color_vals,
                colorscale=full_colorscale,
                cmin=-1,
                cmax=max(color_vals),
                showscale=True,
                colorbar=dict(
                    title="Generation",
                    tickvals=list(range(-1, max(color_vals) + 1)),
                    ticktext=["Vaccinated"] + [str(i) for i in range(max(color_vals) + 1)],
                ),
                line=dict(width=1, color="black")
            ),
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

    # ====================================================
    # BUILD TREE
    # ====================================================
    G = generate_tree(R0, curr_gen, superspreader_pct, vacc_pct)

    if layout_mode == "Hierarchical (CDC-style)":
        pos = layout_hierarchy(G, horiz, vert)
    else:
        pos = layout_radial(G, radial_scale)

    fig = draw_tree(G, pos, show_labels)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    ### Teaching Notes
    - **Yellow index case** is visually distinct and meaningful.
    - **Superspreaders** (large glowing nodes) show real-world patterns.
    - **Vaccinated nodes** stop chains of transmission.
    - **Curved links** improve readability.
    - **Radial mode** shows outbreak explosions; **hierarchical mode** shows lineage.
    """)
