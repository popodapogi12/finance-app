import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json

# --- SETUP & SECURITY ---
# This block handles the connection to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 1. Try to load from Cloud Secrets (Streamlit Cloud)
try:
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # If secrets exist but 'gcp_service_account' is missing
        raise FileNotFoundError
except FileNotFoundError:
    # 2. If Cloud Secrets fail, load from Local File (Your Computer)
    # Make sure 'credentials.json' is in the SAME folder as this app.py file
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)

# --- APP INTERFACE ---
st.title("Financial Decision Engine")

# 1. Input Data
st.subheader("1. Monthly Actuals")
revenue = st.number_input("Revenue Actuals", value=0)
target = st.number_input("Revenue Target", value=0)

if st.button("Analyze"):
    # Calculate Variance
    if target > 0:
        variance = (revenue - target) / target
        st.write(f"Variance: {variance:.1%}")
        
        # 2. Simple Logic Rule
        if abs(variance) > 0.05:
            st.error("Variance > 5%. Please explain.")
            explanation = st.text_input("Reason for variance:")
            
            if explanation:
                # 3. Save to Google Sheet
                try:
                    sheet = client.open("Financial_Data").sheet1  # Make sure your Sheet is named "Financial_Data"
                    sheet.append_row([revenue, target, variance, explanation])
                    st.success("Saved to Google Sheets!")
                except Exception as e:
                    st.error(f"Could not connect to Sheet: {e}")