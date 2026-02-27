# Communicable Disease Spread Simulator

This interactive Streamlit app demonstrates how infectious diseases spread and how vaccination changes outbreak dynamics.  
Designed for epidemiology teaching — especially for undergraduate public health students.

---

## 🔬 Features

### **1. Herd Immunity Calculator**
- Auto-filled R₀ values for major vaccine-preventable diseases  
- Calculates herd immunity threshold  
- Computes effective reproduction number (Rₑ)  
- Clear indicators showing whether an outbreak can be controlled  

### **2. Exponential Disease Spread**
- Visual bar chart of generation growth  
- Color gradient from green → yellow → red  
- Adjustable R₀ and number of generations  

### **3. Vaccine Impact**
- Side-by-side comparison:  
  **no vaccination vs. real-world coverage**  
- Rₑ automatically computed  
- Dual-line chart for clear teaching use  

### **4. Spread Visualization (Animated or Node Tree)**
- **Animated spread (click to advance)** up to 8 generations  
- **Node Tree network** showing branching transmission  
- Colorful, intuitive graphics ideal for classroom demonstration  

---

## 📚 Diseases Included (with R₀ presets)

- Measles (MMR)  
- Pertussis (DTaP)  
- Polio (IPV)  
- Varicella (Chickenpox)  
- Hepatitis B (HepB)  
- HPV  
- Hib  
- Pneumococcal (PCV)  

---

## 🖥️ Running the App Locally

### **1. Install Python**
Download Python 3.10 or later from:  
https://www.python.org/downloads/

Be sure to check **"Add Python to PATH"** during installation.

---

### **2. Install required packages**

Open Command Prompt and run:

```bash
pip install -r requirements.txt