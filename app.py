import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import datetime
import os

# 設定寬螢幕模式
st.set_page_config(page_title="Tolerance Tool", layout="wide")

# --- CSS: 修正標題顯示、放大字體、壓縮佈局 ---
st.markdown("""
    <style>
    /* 修正頂部空白，確保標題不被切掉 */
    .block-container { 
        padding-top: 3rem !important; 
        padding-bottom: 0rem !important; 
    }
    
    /* 標題與結果標籤字體放大 1.5 倍 */
    h2, [data-testid="stMetricLabel"] {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #333333 !important;
        line-height: 1.5 !important;
    }

    /* 數值字體放大至 30px */
    [data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
    }
    
    /* 壓縮元件間距符合 16:9 比例 */
    .element-container { margin-bottom: -5px !important; }
    .stImage { margin-bottom: -10px !important; }
    div[data-testid="stDataEditor"] > div { max-height: 320px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 報告函數: 修正括號閉合錯誤 ---
def create_report_pdf(proj, title, date, unit, target, wc, rss, yield_val, cpk, df, img_path):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 15, txt="Design Tolerance Analysis Report", ln=True, align='C')
    pdf.ln(5)

    # 基本資訊
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(230, 230, 230)
    pdf.cell(45, 8, "Project", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(145, 8, proj, 1, 1)
    pdf.set_font("Arial", 'B', 10); pdf.cell(45, 8, "Title", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(145, 8, title, 1, 1)
    pdf.ln(5)

    # 嵌入示意圖
    if img_path and os.path.exists(img_path):
        pdf.image(img_path, x=10, w=140)
        pdf.ln(75)

    # 數據明細表格 (已修正語法錯誤)
    pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data Details:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(245, 245, 245)
    pdf.cell(30, 7, "Part", 1, 0, 'C', True)
    pdf.cell(20, 7, "No.", 1, 0, 'C', True)
    pdf.cell(100, 7, "Description", 1, 0, 'C', True)
    pdf.cell(40, 7, "Tol (+/-)", 1, 1, 'C', True) # 確保結尾括號正確閉合

    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(30, 7, str(row['Part']), 1)
        pdf.cell(20, 7, str(row['No.']), 1)
        pdf.cell(100, 7, str(row['Description']), 1)
        pdf.cell(40, 7, f"{row['Upper Tol']:.3f}", 1, 1)
    
    # 分析結果
    pdf.ln(5); pdf.set_font("Arial", 'B', 13)
    pdf.cell(190, 8, "Analysis Summary:", ln=True)
    pdf.set_font("Arial", 'B', 11); pdf.set_text_color(31, 119, 180)
    pdf.cell(63, 10, f"Worst Case: +/- {wc:.3f}", 1, 0, 'C')
    pdf.cell(63, 10, f"RSS Total: +/- {rss:.3f}", 1, 0, 'C')
    pdf.cell(64, 10, f"Yield: {yield_val:.2f}%", 1, 1, 'C')
    
    return pdf.output(dest="S").encode("latin-1")

# --- 資料邏輯 ---
DEFAULT_DATA = [
    {"Part": "PCB", "No.": "a", "Description": "Panel mark to unit mark", "Upper Tol": 0.100},
    {"Part": "PCB", "No.": "b", "Description": "Unit mark to soldering pad", "Upper Tol": 0.100},
    {"Part": "SMT", "No.": "c", "Description": "SMT tolerance", "Upper Tol": 0.150},
    {"Part": "Connector", "No.": "d", "Description": "Connector housing", "Upper Tol": 0.125},
]
if 'df_data' not in st.session_state: st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

def clear_all(): st.session_state.df
