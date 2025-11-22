import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import matplotlib.pyplot as plt

# --- 1. SETUP & SECURITY ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Connect to Google Sheets
try:
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Financial_Data").sheet1
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# Connect to AI (Gemini)
if "google_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["google_api_key"])
else:
    st.warning("⚠️ AI Key missing. Please add 'google_api_key' to Secrets.")

# --- 2. AI & MATH FUNCTIONS ---

def get_macro_risk(industry):
    """Asks AI to analyze macro conditions and return a risk score (0.0 to 0.3)"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        Act as a CFO. For the {industry} industry, analyze current macroeconomic factors (inflation, supply chain, interest rates).
        Based on this, output a single 'Volatility Score' between 0.05 (Stable) and 0.30 (Highly Volatile).
        
        Also provide a 1-sentence summary of the biggest threat.
        
        Output format:
        SCORE: [number]
        THREAT: [text]
        """
        response = model.generate_content(prompt)
        text = response.text
        
        # Parse the AI's "Text" answer into data
        score = 0.10 # Default fallback
        reason = "AI analysis pending"
        
        for line in text.split('\n'):
            if "SCORE:" in line:
                score = float(line.split(":")[1].strip())
            if "THREAT:" in line:
                reason = line.split(":")[1].strip()
                
        return score, reason
    except:
        return 0.15, "AI could not reach server. Using default volatility."

def run_monte_carlo(current_rev, volatility, years=5, simulations=1000):
    """Runs 1,000 stochastic simulations of future revenue."""
    mu = 0.05  # Assume 5% average organic growth
    dt = 1     # 1 year steps
    
    simulation_df = pd.DataFrame()
    
    for i in range(simulations):
        # Geometric Brownian Motion Formula
        prices = [current_rev]
        for y in range(years):
            shock = np.random.normal(0, 1) # The "Stochastic" random part
            
            # The Formula: S_t = S_{t-1} * exp(...)
            next_price = prices[-1] * np.exp((mu - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * shock)
            prices.append(next_price)
        
        simulation_df[f"Sim_{i}"] = prices
        
    return simulation_df

# --- 3. THE APP INTERFACE ---

st.title("🤖 AI Financial Core")

# TAB SYSTEM
tab1, tab2 = st.tabs(["🔮 Future Modeling", "📉 Variance Tracker"])

# === TAB 1: PREDICT THE FUTURE ===
with tab1:
    st.header("Stochastic Forecasting")
    
    col1, col2 = st.columns(2)
    with col1:
        industry = st.text_input("Industry / Sector", value="Retail Fashion")
        current_revenue = st.number_input("Starting Revenue ($)", value=100000)
    
    if st.button("Run AI Simulation"):
        with st.spinner("AI is analyzing macroeconomic trends..."):
            # 1. Ask AI for Risk Score
            risk_score, threat = get_macro_risk(industry)
            st.info(f"AI Detected Volatility: {risk_score*100:.1f}% | Major Threat: {threat}")
            
            # 2. Run Math
            sim_data = run_monte_carlo(current_revenue, risk_score)
            
            # 3. Visualize
            st.subheader("5-Year Probability Cone")
            
            # Calculate P10, P50, P90 (Confidence Intervals)
            sim_data["P90"] = sim_data.apply(lambda x: np.percentile(x, 90), axis=1)
            sim_data["P50"] = sim_data.apply(lambda x: np.percentile(x, 50), axis=1) # Median
            sim_data["P10"] = sim_data.apply(lambda x: np.percentile(x, 10), axis=1)
            
            # Simple Chart
            st.line_chart(sim_data[["P90", "P50", "P10"]])
            
            st.caption("Top Line: Best Case (90%) | Middle: Likely | Bottom: Worst Case (10%)")

# === TAB 2: TRACK THE PAST ===
with tab2:
    st.header("Monthly Actuals vs Targets")
    
    ac_col, ta_col = st.columns(2)
    with ac_col:
        actual = st.number_input("Actual Revenue", value=0.0)
    with ta_col:
        target = st.number_input("Target Revenue", value=0.0)
        
    if st.button("Log Actuals"):
        if target == 0:
            st.error("Target cannot be 0")
        else:
            variance = (actual - target) / target
            
            # Smart Logic: Check if variance is huge
            if abs(variance) > 0.05:
                st.warning(f"⚠️ High Variance detected: {variance:.1%}")
                explanation = st.text_area("Admin Explanation Required:")
                
                if explanation:
                     # Save to Google Sheets
                    row = [str(pd.Timestamp.now()), industry, actual, target, variance, explanation]
                    sheet.append_row(row)
                    st.success("Data + Explanation logged to Knowledge Base.")
            else:
                # Save without explanation
                row = [str(pd.Timestamp.now()), industry, actual, target, variance, "Normal Operation"]
                sheet.append_row(row)
                st.success("Data logged successfully.")