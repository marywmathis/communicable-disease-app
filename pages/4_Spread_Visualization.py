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
st.header("Epidemic Spread Visualization Suite")

mode = st.selectbox(
    "Choose visualization mode:",
    ["Animated Spread", "Node Tree Spread", "SEIR Model"]
)

# ============================================================
# DISEASE + R0
# ============================================================
disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
R0_default = disease_r0[disease]
R0_base = st.slider("Baseline R₀", 1.0, 20.0, float(R0_default), 0.1)

# ============================================================
# EFFECTIVE Rₑ CONTROLS
# ============================================================
st.subheader("Rₑ Controls")

vacc_eff = st.slider("Vaccination effectiveness (%)", 0, 100, 50)
mask_eff = st.slider("Mask effectiveness (%)", 0, 100, 30)
dist_eff = st.slider("Distancing effectiveness (%)", 0, 100, 20)

Re = R0_base * (1 - vacc_eff/100) * (1 - mask_eff/100) * (1 - dist_eff/100)
Re = max(0.1, Re)

st.metric("Effective Rₑ", f"{Re:.2f}")

# ============================================================
# ADVANCED EPIDEMIOLOGIC TIMING PANEL
# ============================================================
with st.expander("Advanced Epidemiologic Timing"):

    incubation_days = st.slider("Incubation Period (days)", 1, 14, 4)
    infectious_days = st.slider("Infectious Period (days)", 1, 20, 6)

    generation_interval = incubation_days + (infectious_days / 2)
    doubling_time = math.log(2) / math.log(Re) if Re > 1 else None

    st.write(f"**Estimated Generation Interval:** {generation_interval:.1f} days")

    if doubling_time:
        st.write(f"**Approximate Doubling Time:** {doubling_time * generation_interval:.1f} days")
    else:
        st.write("**Doubling Time:** Not applicable (Rₑ ≤ 1)")

# ============================================================
# 1. ANIMATED SPREAD
# ============================================================
if mode == "Animated Spread":

    st.subheader("Generation-by-Generation Spread")

    max_gen = 8

    if "anim_gen" not in st.session_state:
        st.session_state.anim_gen = 0

    if st.button("Next Generation →"):
        st.session_state.anim_gen = min(max_gen, st.session_state.anim_gen + 1)

    gen = st.session_state.anim_gen
    st.write(f"Showing Generation 0 → {gen}")

    infected = [1]
    for g in range(1, gen + 1):
        infected.append(infected[-1] * Re)

    df = pd.DataFrame({
        "Generation": list(range(gen + 1)),
        "Infected": infected
    })

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

    timing_df = pd.DataFrame({
        "Generation": list(range(gen + 1)),
        "Approx Days": [round(g * generation_interval, 1) for g in range(gen + 1)]
    })

    st.dataframe(timing_df, use_container_width=True)

# ============================================================
# 2. NODE TREE SPREAD
# ============================================================
elif mode == "Node Tree Spread":

    st.subheader("Transmission Tree")

    superspreader_pct = st.slider("Superspreader %", 0, 50, 10)
    vacc_pct = st.slider("Vaccination % (blocks transmission)", 0, 80, 20)
    max_gen = 8

    def generate_tree(Re, max_gen, superspreader_pct, vacc_pct, max_nodes=2000):

        G = nx.DiGraph()
        G.add_node(0, generation=0)
        node_id = 1
        current = [0]

        for gen in range(1, max_gen + 1):
            next_gen = []
            for parent in current:

                is_super = np.random.rand() < superspreader_pct / 100
                newR = int(Re * (3 if is_super else 1))
                newR = max(1, newR)

                for _ in range(newR):
                    if node_id > max_nodes:
                        return G

                    vaccinated = np.random.rand() < vacc_pct / 100
                    G.add_node(node_id, generation=gen, vacc=vaccinated)
                    G.add_edge(parent, node_id)

                    if not vaccinated:
                        next_gen.append(node_id)

                    node_id += 1

            current = next_gen

        return G

    G = generate_tree(Re, max_gen, superspreader_pct, vacc_pct)

    # SIMPLE HIERARCHICAL LAYOUT (NO SCIPY REQUIRED)
    pos = {}
    gens = {}
    for n, d in G.nodes(data=True):
        gens.setdefault(d["generation"], []).append(n)

    for gen, nodes in gens.items():
        xs = np.linspace(-1, 1, len(nodes))
        for i, n in enumerate(nodes):
            pos[n] = (xs[i], -gen)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_gen = [G.nodes[n]["generation"] for n in G.nodes()]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1, color="gray"),
        hoverinfo="none"
    ))

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        marker=dict(
            size=12,
            color=node_gen,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Generation")
        )
    ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # GENERATION TIMING TABLE
    timing_df = pd.DataFrame({
        "Generation": list(range(max_gen + 1)),
        "Approx Days Since Index Case":
            [round(g * generation_interval, 1) for g in range(max_gen + 1)]
    })

    st.subheader("Generation Timing")
    st.dataframe(timing_df, use_container_width=True)

# ============================================================
# 3. SEIR MODEL
# ============================================================
else:

    st.subheader("SEIR Model")

    days = st.slider("Simulation Duration (days)", 30, 200, 100)

    N = 1_000_000
    I0, E0 = 10, 5
    S0 = N - I0 - E0

    beta = Re / infectious_days
    sigma = 1 / incubation_days
    gamma = 1 / infectious_days

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
        .transform_fold(["S", "E", "I", "R"])
        .mark_line()
        .encode(
            x="index:Q",
            y="value:Q",
            color="key:N"
        )
        .properties(height=500)
    )

    st.altair_chart(chart, use_container_width=True)
