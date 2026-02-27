import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import networkx as nx
import time
import math
import json

# ============================================================
# DISEASE PRESET R0 VALUES
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
    "COVID-19 (Ancestral Wuhan)": 3,
    "COVID-19 Delta Variant": 6,
    "COVID-19 Omicron BA.1": 9,
    "COVID-19 Omicron BA.5": 12,
}

# ============================================================
# PAGE HEADER
# ============================================================
st.header("Spread Visualization (Animated, Node Tree, and SEIR Model)")

st.markdown("""
This tool allows you to explore:

### **1. Animated outbreak simulation**  
Shows exponential growth generation-by-generation.

### **2. Branching transmission tree**  
With:
- Superspreader paths  
- Vaccination pruning  
- Effective Rₑ  
- Curved edges  
- Radial or hierarchical layouts  
- Export options  

### **3. SEIR Compartmental Model**  
Clear S–E–I–R transitions with a full legend.
""")

# ============================================================
# CHOOSE MODE
# ============================================================
mode = st.selectbox(
    "Choose visualization mode:",
    ["Animated Spread (Click to Advance)",
     "Node Tree Spread",
     "SEIR Model"]
)

# ============================================================
# DISEASE SELECTION AND R0
# ============================================================
disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
R0_default = disease_r0[disease]

R0_base = st.slider("Baseline R₀", 1.0, 20.0, float(R0_default), 0.1)

max_gen = 8

# ============================================================
# CALCULATE EFFECTIVE Rₑ
# ============================================================
st.subheader("Rₑ (Effective Reproduction Number) Controls")

vacc_eff = st.slider("Vaccination effectiveness (%)", 0, 100, 50)
mask_eff = st.slider("Mask effectiveness (%)", 0, 100, 30)
dist_eff = st.slider("Distancing effectiveness (%)", 0, 100, 20)

Re = R0_base * (1 - vacc_eff/100) * (1 - mask_eff/100) * (1 - dist_eff/100)
Re = max(0.1, Re)  # safety floor

st.metric("Effective Rₑ", f"{Re:.2f}")

# ============================================================
# 1. ANIMATED MODE
# ============================================================
if mode == "Animated Spread (Click to Advance)":

    st.subheader("Animated Spread — Click to Advance")

    if "anim_gen" not in st.session_state:
        st.session_state.anim_gen = 0

    if st.button("Next Generation →"):
        if st.session_state.anim_gen < max_gen:
            st.session_state.anim_gen += 1

    gen = st.session_state.anim_gen
    st.write(f"### Showing Generation 0 → {gen}")

    infected = [1]
    for g in range(1, gen + 1):
        infected.append(infected[-1] * Re)

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
    st.metric("Total Infected", f"{int(infected[-1]):,}")

# ============================================================
# 2. NODE TREE MODE
# ============================================================
elif mode == "Node Tree Spread":

    st.subheader("Node Tree Spread Visualization")

    layout_mode = st.radio("Layout", ["Hierarchical (CDC-style)", "Radial"])
    animation_mode = st.radio("Animation", ["Manual", "Auto-Play", "None"])
    show_labels = st.checkbox("Show node labels")
    highlight_superspreader_paths = st.checkbox("Highlight superspreader paths", value=True)

    superspreader_pct = st.slider("Superspreader %", 0, 50, 10)
    vacc_pct = st.slider("Vaccination % (stops transmission)", 0, 80, 20)

    horiz = st.slider("Horizontal spacing", 0.2, 3.0, 1.0)
    vert = st.slider("Vertical spacing", 0.3, 2.0, 1.0)
    radial_scale = st.slider("Radial scale", 0.3, 2.0, 1.0)

    if "tree_gen" not in st.session_state:
        st.session_state.tree_gen = 0

    if animation_mode == "Manual":
        if st.button("Next Generation →"):
            st.session_state.tree_gen = min(max_gen, st.session_state.tree_gen + 1)

    elif animation_mode == "Auto-Play":
        play = st.checkbox("Play", value=False)
        if play:
            for g in range(st.session_state.tree_gen, max_gen + 1):
                st.session_state.tree_gen = g
                time.sleep(0.65)
                st.experimental_rerun()

    else:
        st.session_state.tree_gen = max_gen

    curr_gen = st.session_state.tree_gen
    st.write(f"### Showing generations 0 → {curr_gen}")

    # ============================================================
    # GENERATE TREE
    # ============================================================
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

                is_super = np.random.rand() < (superspreader_pct/100)
                new_R = int(Re * (3 if is_super else 1))
                if new_R < 1:
                    new_R = 1

                for _ in range(new_R):
                    if node_id > max_nodes:
                        return G

                    vacc_status = np.random.rand() < (vacc_pct/100)

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

    G = generate_tree(Re, curr_gen, superspreader_pct, vacc_pct)

    # ============================================================
    # LAYOUT FUNCTIONS
    # ============================================================
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
            angles = np.linspace(0, 2*np.pi, len(nodes), endpoint=False)
            for angle, n in zip(angles, nodes):
                pos[n] = (radius * math.cos(angle), radius * math.sin(angle))
        return pos

    # ============================================================
    # CURVED EDGE GENERATOR
    # ============================================================
    def curved_edge(x0, y0, x1, y1, steps=20):
        xm = (x0 + x1)/2
        ym = (y0 + y1)/2 - 0.15
        xs, ys = [], []
        for t in np.linspace(0, 1, steps):
            bx = (1-t)**2*x0 + 2*(1-t)*t*xm + t**2*x1
            by = (1-t)**2*y0 + 2*(1-t)*t*ym + t**2*y1
            xs.append(bx)
            ys.append(by)
        return xs + [None], ys + [None]

    # ============================================================
    # DRAW TREE
    # ============================================================
    def draw_tree(G, pos, show_labels, highlight):

        edge_x, edge_y = [], []
        edge_colors = []

        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]

            xs, ys = curved_edge(x0, y0, x1, y1)
            edge_x += xs
            edge_y += ys

            is_super_edge = G.nodes[u]["super"]
            edge_colors.append("#FF0000" if (highlight and is_super_edge) else "#BBBBBB")

        # Collapse edge color array into segments
        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1, color="#BBBBBB"),
            hoverinfo="none"
        )

        # Node properties
        node_x, node_y, color_vals, hovertext, size_vals = [], [], [], [], []

        for node, data in G.nodes(data=True):
            x, y = pos[node]
            node_x.append(x); node_y.append(y)
            size_vals.append(22 if data["super"] else 14)

            if data["vacc"]:
                color_vals.append(-1)
            else:
                color_vals.append(data["generation"])

            hovertext.append(
                f"<b>Node:</b> {node}<br>"
                f"Generation: {data['generation']}<br>"
                f"Superspreader: {data['super']}<br>"
                f"Vaccinated: {data['vacc']}<br>"
                f"Parent: {data['parent']}"
            )

        # CUSTOM EPIDEMIC COLOR SCALE
        colorscale = [
            [0.00, "#00AA00"],  # vaccinated
            [0.01, "#FFFF00"],  # gen0
            [0.25, "#FFB000"],
            [0.50, "#FF0000"],
            [0.75, "#8B00FF"],
            [1.00, "#002080"],
        ]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text" if show_labels else "markers",
            text=[str(n) for n in G.nodes()] if show_labels else None,
            textposition="top center",
            hovertext=hovertext,
            hoverinfo="text",
            marker=dict(
                size=size_vals,
                color=color_vals,
                colorscale=colorscale,
                cmin=-1,
                cmax=max(color_vals),
                showscale=True,
                colorbar=dict(
                    title="Legend",
                    tickvals=list(range(-1, max(color_vals)+1)),
                    ticktext=["Vaccinated"] + [f"Gen {i}" for i in range(max(color_vals)+1)]
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

    # ============================================================
    # BUILD FIGURE
    # ============================================================
    pos = layout_hierarchy(G, horiz, vert) if layout_mode.startswith("Hierarchical") else layout_radial(G, radial_scale)
    fig = draw_tree(G, pos, show_labels, highlight_superspreader_paths)

    st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # EXPORT OPTIONS
    # ============================================================
    st.subheader("Export Options")

    export_fmt = st.selectbox("Choose export format", ["PNG", "SVG", "JSON"])
    if st.button("Export"):
        if export_fmt == "JSON":
            s = json.dumps(nx.node_link_data(G))
            st.download_button("Download JSON", s, "tree.json")
        else:
            st.download_button("Download Image", fig.to_image(format=export_fmt.lower()),
                               f"tree.{export_fmt.lower()}")

# ============================================================
# 3. SEIR MODEL
# ============================================================
else:
    st.subheader("SEIR Model")

    st.markdown("""
### **SEIR Key**
- **S** = Susceptible  
- **E** = Exposed (infected but not infectious yet)  
- **I** = Infectious  
- **R** = Recovered / Removed  

This model shows epidemic dynamics over time.
""")

    incubation = st.slider("Incubation period (days)", 1, 10, 4)
    infectious_period = st.slider("Infectious period (days)", 1, 14, 6)
    days = st.slider("Simulation duration (days)", 30, 200, 100)

    N = 1000000
    I0 = 10
    E0 = 5
    S0 = N - I0 - E0
    R0_val = 0

    beta = Re / infectious_period
    sigma = 1/incubation
    gamma = 1/infectious_period

    S, E, I, R = [S0], [E0], [I0], [R0_val]

    for _ in range(days):
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
            y=alt.Y("value:Q"),
            color="variable:N"
        )
        .transform_fold(["S","E","I","R"])
        .properties(height=500)
    )
    st.altair_chart(chart, use_container_width=True)
