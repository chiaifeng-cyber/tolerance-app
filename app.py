import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. Page Configuration & Professional Compact CSS
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# 清理過的 CSS，確保無特殊字元
st.markdown("""
<style>
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
        width: 8px; height: 5px; border-left: 2px solid white; border-bottom: 2px solid
