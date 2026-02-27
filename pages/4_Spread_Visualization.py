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
or a **full branching network view**.
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
disease = st.selectbox(
    "Choose a disease:",
    list(disease_r0.keys())
)

R0 = float(disease_r0[disease])

R0 = st.slider(
    "R₀ (Basic Reproduction Number)",
    min_value=1.0, max_value=20.0,
    value=R0, step=0.1
)

# -------------------------------------------------
# ANIMATION MODE (CLICK-TO-ADVANCE)
# -------------------------------------------------
if mode == "Animated Spread (Click to Advance)":
    
    st.subheader("Animated Spread — Click to Advance")

    max_gen = 8  # Your requested maximum number of generations

    # A button that increments session state each click
    if "current_gen" not in st.session_state:
        st.session_state.current_gen = 0

    if st.button("Next Generation →"):
        if st.session_state.current_gen < max_gen:
            st.session_state.current_gen += 1

    st.write(f"### Showing up to Generation: {st.session_state.current_gen}")

    # Compute infections for displayed generations
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

    st.metric(
        "Total Infected So Far",
        f"{int(infected[-1]):,}"
    )

    st.markdown("""
    ### Teaching Notes
    - Click *Next Generation* to show exponential growth visually.  
    - Works extremely well in the classroom when demonstrating outbreaks.  
    """)

# -------------------------------------------------
# NODE TREE MODE
# -------------------------------------------------
else:
    st.subheader("Node Tree Spread Visualization")

    st.markdown("""
    Each circle represents an infected person.  
    Each generation branches outward from the previous one.
    """)

    max_gen = 8

    # Calculate number of infected per generation
    infected = [1]
    for g in range(1, max_gen + 1):
        infected.append(infected[-1] * R0)

    # Create dataset for node positions
    nodes = []
    for gen in range(max_gen + 1):
        count = int(infected[gen])
        # Spread nodes horizontally across the chart
        x_positions = np.linspace(0, 100, count)
        y_position = gen * 12  # vertical spacing between generations
        for x in x_positions:
            nodes.append([gen, x, y_position])

    node_df = pd.DataFrame(nodes, columns=["Generation", "x", "y"])

    # Circles represent infected individuals
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
    - This view helps students understand **branching transmission**.  
    - Higher R₀ = **denser and wider branching**.  
    - Lower R₀ = more compact networks.  
    """)
