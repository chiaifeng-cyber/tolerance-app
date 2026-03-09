import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. Page Configuration & Professional Compact CSS
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #f0f2f6; }
    .main .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 98% !important;
    }
    h2 { line-height: 1; font-size: 22px; text-align: center; margin-top: -1.5rem; margin-bottom: 10px; color: #1e1e1e; }
    
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p, .stNumberInput label p { 
        font-size: 16px !important; font-weight: bold !important; color: #333; 
        margin-bottom: 4px !important;
    }

    div[data-testid="stTextInput"] label p {
        font-size: 11px !important;
        color: #666 !important;
        margin-bottom: -5px !important;
    }

    .made-by-leo-Oliver {
        font-size: 10px;
        color: #aaa;
        text-align: right;
        margin-top: 5px;
    }

    .table-hint-container {
        display: flex;
        align-items: center;
        margin-top: -22px; 
        margin-bottom: 8px;
        padding-left: 2px;
    }
    .red-check-box {
        width: 14px; height: 14px; background-color: #ff4b4b; border-radius: 3px;
        display: flex; align-items: center; justify-content: center; margin-right: 6px; flex-shrink: 0;
    }
    .white-checkmark {
        width: 8px; height: 5px; border-left: 2px solid white; border-bottom: 2px solid white;
        transform: rotate(-45deg); margin-top: -1px;
    }
    .hint-text { font-size: 11px; color: #666; font-weight: normal; }

    [data-testid="stImage"] img {
        max-height: 40vh !important;
        width: auto !important;
        margin-left: auto; margin-right: auto; display: block;
    }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important; border-radius: 8px !important;
        padding: 4px 8px !important; border: 1px solid #d1d5db !important;
    }
    [data-testid="stVerticalBlock"] > div { margin-bottom: 2px !important; gap: 0.4rem !important; }
    div[data-testid="stDataEditor"] { background-color: #ffffff !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; color: #1f77b4 !important; }
    
    hr { display
