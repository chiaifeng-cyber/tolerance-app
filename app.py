import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import datetime
import os

# 設定頁面為寬螢幕模式
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# --- CSS 樣式優化：修正標題切頂、放大字體、一覽式佈局 ---
st.markdown("""
    <style>
    /* 修正頂部空白確保標題完整 */
    .block-container { 
        padding-top: 2.5rem !important; 
        padding-bottom: 0rem !important; 
    }
    
    /* 標題行高修正 */
    h2 { line-height: 1.4 !important; }

    /* 結果數值：30px 加粗藍色 */
    [data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
    }
    
    /* 結果標題：24px 加粗 (1.5倍) */
    [data-testid="stMetricLabel"] {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #333333 !important;
    }
    
    /* 壓縮元件間距以符合 16:9 一覽 */
    .element-container { margin-bottom: -5px !important; }
    .stImage { margin-bottom: -10px !important; }
    
    /* 限制資料編輯器高度 */
    div[data-testid="stDataEditor"] > div {
        max-height: 320px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 產生函數 (模擬完整 App 畫面彙整至 A4) ---
def create_full_report_pdf(proj, title, date, unit, target, wc, rss, yield_val, cpk, df, img_path=None):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 15, txt="Design Tolerance Analysis Report", ln=True, align='C')
    pdf.ln(2)

    # 專案資訊
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(45, 8, "Project", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(50, 8, proj, 1)
    pdf.set_font("Arial", 'B', 10); pdf.cell(45, 8, "Date", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(50, 8, date, 1, 1)
    pdf.set_font("Arial", 'B', 10); pdf.cell(45, 8, "Title", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(50, 8, title, 1)
    pdf.set_font("Arial", 'B', 10); pdf.cell(45, 8, "Unit", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(50, 8, unit, 1, 1)
    pdf.ln(5)

    # 示意圖
    if img_path and os.path.exists(img_path):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, "Example Diagram:", ln=True)
        pdf.image(img_path, x=10, w=130)
        pdf.ln(70)

    # 數據表格
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, "Input Data:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(245, 245, 245)
    pdf.cell(30, 7, "Part", 1, 0, 'C', True); pdf.cell(20, 7, "No.", 1, 0, 'C', True); pdf.cell(100, 7, "Description", 1, 0, 'C', True); pdf.cell(40, 7, "Tol (+/-)", 1, 1
