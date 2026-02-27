import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

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
Use the dropdown below to switch between an **animated generation-by-generation outbreak**,  
or a **full branching network-style node tree**.
""")

# -------------------------------------------------
# MODE SELECTOR
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
# ANIMATION MODE (CLICK-TO-ADVANCE)
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
# NODE TREE VISUALIZATION MODE
# -------------------------------------------------
else:
    st.subheader("Node Tree Spread Visualization")

    st.markdown("""
Each circle represents an infected person.  
Generations expand outward vertically.
Node counts are capped to keep the browser responsive.
""")

    # Compute infections per generation
    infected = [1]
    for g in range(1, max_gen + 1):
        infected.append(infected[-1] * R0)

    # Cap total nodes to prevent crashing Streamlit Cloud
    MAX_NODES = 5000

    # Build dataset
    nodes = []
    for gen in range(max_gen + 1):
        count = min(int(infected[gen]), MAX_NODES)
        x_positions = np.linspace(0, 100, count)
        y_position = gen * 12

        for x in x_positions:
            nodes.append([gen, x, y_position])

    node_df = pd.DataFrame(nodes, columns=["Generation", "x", "y"])

    # Altair scatterplot
    node_chart = (
        alt.Chart(node_df)
        .mark_circle(size=60, opacity=0.8)
        .encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            color=alt.Color(
                "Generation:Q",
                scale=alt.Scale(scheme="purplebluegreen")
            )
        )
        .properties(height=600)
    )

    st.altair_chart(node_chart, use_container_width=True)

    st.markdown("""
### Teaching Notes
- This view shows branching transmission visually.  
- Higher R₀ produces wider, denser networks.  
- Lower R₀ produces narrow, constrained networks.  
- Node count is capped for smooth performance.  
""")
