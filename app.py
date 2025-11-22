import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials # <--- NEW LIBRARY
import google.generativeai as genai
import matplotlib.pyplot as plt

# --- 1. SETUP & SECURITY ---
# Define the correct permissions (scopes)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Connect to Google Sheets
try:
    if "gcp_service_account" in st.secrets:
        # Cloud Mode (Streamlit Server)
        creds_dict = dict(st.secrets["gcp_service_account"]) # Convert to standard dict
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        # Local Mode (Your Computer)
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        
    client = gspread.authorize(creds)
    
    # CRITICAL CHECK: Ensure the Sheet exists
    sheet = client.open("Financial_Data").sheet1
    
except Exception as e:
    st.error(f"Database Error: {e}")
    st.info("Troubleshooting: 1. Did you create a Google Sheet named 'Financial_Data'? 2. Did you click 'Share' on that sheet and paste the bot's email address?")
    st.stop()

# Connect to AI (Gemini)
# ... (The rest of your code stays exactly the same) ...
