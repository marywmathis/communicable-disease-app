# ============================================================
# TAB 1 — BASIC VACCINATION IMPACT  (FULLY FIXED VERSION)
# ============================================================
with tab1:

    st.subheader("Basic Vaccination Impact")

    # ---------------------------------------------
    # Disease selection
    # ---------------------------------------------
    disease = st.selectbox("Choose a disease:", list(disease_r0.keys()))
    R0 = disease_r0[disease]

    st.write(f"**Baseline R₀ for {disease}: {R0}**")

    # ---------------------------------------------
    # Vaccination coverage slider with session state
    # ---------------------------------------------
    if "coverage_slider" not in st.session_state:
        st.session_state.coverage_slider = 75  # default

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

    # ---------------------------------------------
    # Vaccination presets that override slider
    # ---------------------------------------------
    with colB:
        st.write("Preset Coverage Values:")

        preset_selection = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True
        )

        if preset_selection != "None":
            preset_value = vacc_presets[preset_selection]

            # Update slider AND internal value
            st.session_state.coverage_slider = preset_value
            coverage = preset_value

            st.success(f"Using preset: {preset_selection} = {preset_value}%")

    # ---------------------------------------------
    # Herd immunity threshold
    # ---------------------------------------------
    herd_threshold = (1 - 1 / R0) * 100
    st.metric("Herd Immunity Threshold", f"{herd_threshold:.1f}%")

    if coverage >= herd_threshold:
        st.success("Population exceeds herd immunity threshold.")
    else:
        st.warning("Population is below herd immunity threshold.")

    # ---------------------------------------------
    # Effective reproductive number
    # ---------------------------------------------
    Re = R0 * (1 - coverage / 100)
    st.metric("Effective Rₑ", f"{Re:.2f}")

    # ---------------------------------------------
    # Generations slider
    # ---------------------------------------------
    generations = st.slider(
        "Number of generations",
        min_value=1,
        max_value=12,
        value=6
    )

    # ---------------------------------------------
    # Infection calculations
    # ---------------------------------------------
    infected_no_vax = [1]
    infected_vax = [1]

    for g in range(1, generations + 1):
        infected_no_vax.append(infected_no_vax[-1] * R0)
        infected_vax.append(infected_vax[-1] * Re)

    cumulative_no_vax = sum(infected_no_vax)
    cumulative_vax = sum(infected_vax)

    # Build dataframes
    df_no = pd.DataFrame({
        "Generation": list(range(generations + 1)),
        "Infected": infected_no_vax
    })

    df_yes = pd.DataFrame({
        "Generation": list(range(generations + 1)),
        "Infected": infected_vax
    })

    # ---------------------------------------------
    # Linear vs Log scale toggle
    # ---------------------------------------------
    scale_type = st.radio(
        "Chart Scale",
        ["Linear", "Log Scale (base 10)"],
        horizontal=True
    )

    y_axis = alt.Y(
        "Infected:Q",
        scale=alt.Scale(type="log") if scale_type == "Log Scale (base 10)" else alt.Scale(type="linear"),
        title="Infected"
    )

    # ---------------------------------------------
    # Charts
    # ---------------------------------------------
    chart_no = (
        alt.Chart(df_no)
        .mark_line(point=True, color="#E53935", strokeWidth=3)
        .encode(
            x="Generation:O",
            y=y_axis,
            tooltip=["Generation", "Infected"]
        )
        .properties(
            width=350,
            height=350,
            title="No Vaccination (R₀)"
        )
    )

    chart_yes = (
        alt.Chart(df_yes)
        .mark_line(point=True, color="#43A047", strokeWidth=3)
        .encode(
            x="Generation:O",
            y=y_axis,
            tooltip=["Generation", "Infected"]
        )
        .properties(
            width=350,
            height=350,
            title=f"With Vaccination (Rₑ = {Re:.2f})"
        )
    )

    # ---------------------------------------------
    # Display side-by-side charts
    # ---------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_no, use_container_width=True)
    with col2:
        st.altair_chart(chart_yes, use_container_width=True)

    # ---------------------------------------------
    # Summary Interpretation
    # ---------------------------------------------
    st.markdown("---")
    st.markdown(f"""
    ### Summary
    - **No vaccination:** {int(infected_no_vax[-1]):,} infections by generation {generations}.  
    - **With {coverage}% vaccination:** {int(infected_vax[-1]):,} infections.  
    - **Cumulative infections reduced** from {cumulative_no_vax:,} → {cumulative_vax:,}.  
    - Herd Immunity Threshold = **{herd_threshold:.1f}%**, Coverage = **{coverage}%**.  
    """)
