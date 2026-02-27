import streamlit as st

# -------------------------------------------------
# DISEASE PRESETS (R₀ VALUES)
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
st.header("Herd Immunity Calculator")

st.markdown("""
Use this tool to explore how vaccination impacts community-level protection.
""")

# -------------------------------------------------
# SELECT DISEASE WITH PRE-FILLED R₀
# -------------------------------------------------
disease = st.selectbox(
    "Choose a disease:",
    list(disease_r0.keys())
)

R0_default = disease_r0[disease]

R0 = st.slider(
    "R₀ (Basic Reproduction Number)",
    min_value=1.0,
    max_value=20.0,
    value=float(R0_default),
    step=0.1
)

# -------------------------------------------------
# HERD IMMUNITY FORMULA
# HIT = 1 - (1 / R0)
# -------------------------------------------------
HIT = 1 - (1 / R0)
HIT_percent = HIT * 100

st.metric("Herd Immunity Threshold", f"{HIT_percent:.1f} %")

# -------------------------------------------------
# VACCINATION COVERAGE
# -------------------------------------------------
coverage = st.slider(
    "Current Vaccination Coverage (%)",
    min_value=0,
    max_value=100,
    value=70
)

# -------------------------------------------------
# EFFECTIVE REPRODUCTION NUMBER
# Rₑ = R₀(1 - v)
# -------------------------------------------------
Re = R0 * (1 - coverage / 100)

st.metric("Effective Reproduction Number (Rₑ)", f"{Re:.2f}")

# -------------------------------------------------
# INTERPRETATION
# -------------------------------------------------
st.markdown("---")

if Re < 1:
    st.success("""
### 🎉 Outbreak Control Achieved
The effective reproduction number is **below 1**, meaning infections will decline over time.
""")
else:
    st.error("""
### ⚠️ Insufficient Immunity
Rₑ is **above 1**, meaning the disease can continue spreading in the population.
""")

# -------------------------------------------------
# EXTRA CONTEXT
# -------------------------------------------------
st.markdown("""
### Formula Notes
- **R₀** = number of new infections caused by one infected person  
- **Herd immunity threshold** = level of immunity needed to stop sustained spread  
- **Rₑ** = actual transmission under real-world immunity levels  
""")
