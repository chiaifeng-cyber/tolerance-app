import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import datetime
import os

# 1. 頁面基本設定
st.set_page_config(page_title="Tolerance Tool", layout="wide")

# 2. CSS 樣式：解決標題切頂與字體放大需求
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    h2 { line-height: 1.6 !important; font-size: 28px !important; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold !important; color: #1f77b4 !important; }
    [data-testid="stMetricLabel"] { font-size: 24px !important; font-weight: bold !important; color: #333333 !important; }
    div[data-testid="stDataEditor"] > div { max-height: 320px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (嚴格檢查括號閉合)
def create_report_pdf(proj, title, date, unit, target, wc, rss, yield_val, cpk, df, img_path):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="Design Tolerance Analysis Report", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, "Project:", 1); pdf.cell(150, 8, str(proj), 1, 1)
    pdf.cell(40, 8, "Title:", 1); pdf.cell(150, 8, str(title), 1, 1)
    if img_path and os.path.exists(img_path):
        pdf.ln(5)
        pdf.image(img_path, x=10, w=130)
        pdf.ln(70)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, "Results:", ln=True)
    pdf.cell(63, 10, f"Worst Case: {wc:.3f}", 1); pdf.cell(63, 10, f"RSS: {rss:.3f}", 1); pdf.cell(64, 10, f"Yield: {yield_val:.2f}%", 1, 1)
    return pdf.output(dest="S").encode("latin-1")

# 4. 資料初始化與 Session State 管理
DEFAULT_DATA = [
    {"Part": "PCB", "No.": "a", "Description": "Panel mark to unit mark", "Upper Tol": 0.100},
    {"Part": "PCB", "No.": "b", "Description": "Unit mark to soldering pad", "Upper Tol": 0.100},
    {"Part": "SMT", "No.": "c", "Description": "SMT tolerance", "Upper Tol": 0.150},
    {"Part": "Connector", "No.": "d", "Description": "Connector housing", "Upper Tol": 0.125}
]

if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

def clear_all():
    st.session_state.df_data = pd.DataFrame(columns=["Part", "No.", "Description", "Upper Tol"])

def reset_default():
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

# 5. 主畫面標題
st.markdown("<h2>設計累計公差分析工具</h2>", unsafe_allow_html=True)

# 6. 左右分欄佈局 (16:9 優化)
l_col, r_col = st.columns([1.3, 1])

with l_col:
    st.subheader("🖼️ 示意圖與數據輸入")
    img_fn = "4125.jpg"
    if os.path.exists(img_fn):
        st.image(img_fn, use_container_width=True)
    
    # 按鈕列
    b1, b2, _ = st.columns([1, 1, 2])
    with b1: st.button("🗑️ 清除資料", on_click=clear_all, use_container_width=True)
    with b2: st.button("🔄 還原範例", on_click=reset_default, use_container_width=True)
    
    # 數據編輯
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
    st.session_state.df_data = ed_df

with r_col:
    st.subheader("📋 專案資訊與結果")
    with st.container(border=True):
        p_name = st.text_input("專案名稱", "TM-P4125-001")
        t_text = st.text_input("分析標題", "Connector Y-Analysis")
        d_text = st.text_input("日期", "2025/12/29")
        u_text = st.text_input("單位", "mm")

    st.divider()
    t_spec = st.number_input("設計公差目標 (Target Spec ±)", value=0.200, format="%.3f")
    
    # 核心計算邏輯
    if not ed_df.empty and "Upper Tol" in ed_df.columns:
        wc = ed_df["Upper Tol"].sum()
        rss = np.sqrt((ed_df["Upper Tol"]**2).sum())
        cpk = t_spec / rss if rss != 0 else 0
        y_val = (2 * norm.cdf(3 * cpk) - 1) * 100
    else:
        wc, rss, cpk, y_val = 0, 0, 0, 0

    # 顯示結果 (字體已放大)
    st.metric("Worst Case (最壞情況)", f"± {wc:.3f} {u_text}")
    st.metric("RSS Total (均方根)", f"± {rss:.3f} {u_text}")
    st.metric("預估良率 (Estimated Yield)", f"{y_val:.2f} %")
    st.info(f"結論：CPK 為 {cpk:.2f}。")

    # PDF 匯出按鈕
    try:
        pdf_out = create_report_pdf(p_name, t_text, d_text, u_text, t_spec, wc, rss, y_val, cpk, ed_df, img_fn)
        st.download_button("📥 匯出 A4 PDF 報告", data=pdf_out, file_name=f"Report_{p_name}.pdf", use_container_width=True)
    except Exception:
        st.warning("PDF 下載暫不支援中文字元輸入。")
