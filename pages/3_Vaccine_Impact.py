################################################################################
# TAB 1 — BASIC VACCINATION IMPACT (FULLY FIXED)
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
    # Initialize synced state variables
    # -------------------------------------------------------------------------
    if "coverage_value" not in st.session_state:
        st.session_state.coverage_value = 75

    if "preset_choice" not in st.session_state:
        st.session_state.preset_choice = "None"

    if "override_preset" not in st.session_state:
        st.session_state.override_preset = False

    # -------------------------------------------------------------------------
    # If slider previously changed → override preset now, BEFORE rendering widgets
    # -------------------------------------------------------------------------
    if st.session_state.override_preset:
        st.session_state.preset_choice = "None"
        st.session_state.override_preset = False

    st.markdown("### Vaccination Coverage Settings")
    colA, colB = st.columns([2, 3])

    # -------------------------------------------------------------------------
    # 1️⃣ PRESET radio → moves slider
    # -------------------------------------------------------------------------
    with colB:
        preset = st.radio(
            "Choose preset:",
            list(vacc_presets.keys()) + ["None"],
            horizontal=True,
            key="preset_choice",
        )

        # If a preset (not None) was chosen → update coverage value
        if preset != "None":
            st.session_state.coverage_value = vacc_presets[preset]
            st.success(f"Using preset: {preset} = {vacc_presets[preset]}%")

    # -------------------------------------------------------------------------
    # 2️⃣ SLIDER → if changed, mark override_preset for *next run*
    # -------------------------------------------------------------------------
    with colA:
        slider_val = st.slider(
            "Vaccination Coverage (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.coverage_value,
            key="coverage_slider"
        )

        # If user moved the slider → tell next run to deselect preset
        if slider_val != st.session_state.coverage_value:
            st.session_state.override_preset = True

        st.session_state.coverage_value = slider_val

    # FINAL unified coverage
    coverage = st.session_state.coverage_value

    # -------------------------------------------------------------------------
    # HERD IMMUNITY
    # -------------------------------------------------------------------------
    herd_threshold = (1 - 1 / R0) * 100
    st.metric("Herd Immunity Threshold", f"{herd_threshold:.1f}%")

    if coverage >= herd_threshold:
        st.success("Population exceeds herd immunity threshold.")
    else:
        st.warning("Population is below herd immunity threshold.")

    # -------------------------------------------------------------------------
    # EFFECTIVE Rₑ
    # -------------------------------------------------------------------------
    Re = R0 * (1 - coverage / 100)
    st.metric("Effective Rₑ", f"{Re:.2f}")

    # -------------------------------------------------------------------------
    # GENERATIONS
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
    # SCALE: linear vs log
    # -------------------------------------------------------------------------
    scale = st.radio("Chart Scale", ["Linear", "Log Scale"], horizontal=True)

    y_axis = alt.Y(
        "Infected:Q",
        scale=alt.Scale(type="log") if scale == "Log Scale" else alt.Scale(type="linear")
    )

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

    c1, c2 = st.columns(2)
    c1.altair_chart(chart_no, use_container_width=True)
    c2.altair_chart(chart_yes, use_container_width=True)

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    st.markdown("### Summary")
    st.write(f"""
    - **Final generation infections:**  
      - No vaccination: {infected_no[-1]:,}  
      - With vaccination: {infected_yes[-1]:,}  

    - **Cumulative infections:**  
      - No vaccination: {sum(infected_no):,}  
      - With vaccination: {sum(infected_yes):,}  
    """)
