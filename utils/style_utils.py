# utils/style_utils.py
import streamlit as st

def inject_global_styles():
    st.markdown("""
    <style>
        :root {
            --primary: #ff9ff3;
            --secondary: #f368e0;
            --accent: #ff6b6b;
            --background: #fff9ff;
            --text: #5f27cd;
        }

        .stApp {
            background-color: var(--background);
        }

        h1, h2, h3 {
            color: var(--text) !important;
            font-family: 'Arial Rounded MT Bold', sans-serif;
        }

        .stButton>button {
            background-color: var(--primary) !important;
            color: white !important;
            border-radius: 20px !important;
            font-weight: bold !important;
            border: none !important;
        }

        .stButton>button:hover {
            background-color: var(--secondary) !important;
        }

        .stMetric {
            background-color: #fef6ff !important;
            border-radius: 10px !important;
            padding: 10px !important;
            border-left: 3px solid var(--accent) !important;
        }

        .metric-card {
            background-color: #fef6ff !important;
            border-radius: 15px !important;
            padding: 15px !important;
            border-left: 4px solid var(--accent) !important;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .plot-container {
            background-color: white;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
