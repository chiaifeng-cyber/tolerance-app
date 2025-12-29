import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import base64

# 設定頁面資訊
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# --- CSS 優化間距 ---
st.markdown("""
    <style>
    .element-container { margin-bottom: -10px; }
    .stImage { margin-bottom: -20px; }
    h3 { margin-top: -20px; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 產生函數 ---
def create_pdf(proj_name, title, target, wc, rss, yield_pct, cpk, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Tolerance Stack-up Analysis Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Project: {proj_name}", ln=True)
    pdf.cell(200, 10, txt=f"Title: {title}", ln=True)
    pdf.cell(200, 10, txt=f"Target Spec: +/- {target:.3f} mm", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Analysis Results:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Worst Case: +/- {wc:.3f} mm", ln=True)
    pdf.cell(200, 10, txt=f"- RSS Total: +/- {rss:.3f} mm", ln=True)
    pdf.cell(200, 10, txt=f"- Estimated CPK: {cpk:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"- Estimated Yield: {yield_pct:.2f} %", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 初始化 Session State (用於清除資料) ---
default_data = [
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "a", "Description": "Panel mark to unit mark", "Upper Tol": 0.100, "Lower Tol": 0.100},
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "b", "Description": "Unit mark to soldering pad", "Upper Tol": 0.100, "Lower Tol": 0.100},
    {"Part": "SMT", "Req. CPK": 1.00, "No.": "c", "Description": "SMT tolerance", "Upper Tol": 0.150, "Lower Tol": 0.150},
    {"Part": "Connector", "Req. CPK": 1.33, "No.": "d", "Description": "Connector housing (0.25/2)", "Upper Tol": 0.125, "Lower Tol": 0.125},
]

if 'table_data' not in st.session_state:
    st.session_state.table_data = pd.DataFrame(default_data)

def clear_data():
    st.session_state.table_data = pd.DataFrame(columns=["Part", "Req. CPK", "No.", "Description", "Upper Tol", "Lower Tol"])
    st.rerun()

# 頁面標題
st.markdown("<h2 style='text-align: center;'>設計累計公差分析</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Design Tolerance Stack-up Analysis</h4>", unsafe_allow_html=True)

# 專案基本資訊
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        proj_name = st.text_input("專案名稱 (Project Name)", "TM-P4125-001")
        analysis_title = st.text_input("分析標題 (Title)", "Connector Y-Position Analysis")
    with c2:
        st.text_input("日期 (Date)", "2025/12/17")
        st.text_input("尺寸單位 (Unit)", "mm")

st.divider()

# --- 圖片上傳區域 ---
with st.container():
    st.subheader("累積公差圖示 (Tolerance Stack-up Diagram)")
    uploaded_image = st.file_uploader("匯入圖片檔 (Upload Image)", type=["png", "jpg", "jpeg"], key="diagram_uploader")
    if uploaded_image is not None:
        st.image(uploaded_image, use_container_width=True)

st.subheader("公差數據輸入 (Input Table)")

# 工具按鈕：一鍵清除
st.button("🗑️ 一鍵清除資料 (Clear All)", on_click=clear_data)

# 資料輸入表格
edited_df = st.data_editor(st.session_state.table_data, num_rows="dynamic", use_container_width=True, key="data_editor")
st.session_state.table_data = edited_df

# 計算區
target_spec = st.number_input("目前設計公差目標 (Target Spec ±)", value=0.200, format="%.3f")

# --- 核心邏輯計算 ---
if not edited_df.empty and "Upper Tol" in edited_df.columns:
    worst_case = edited_df["Upper Tol"].sum()
    rss_val = np.sqrt((edited_df["Upper Tol"]**2).sum())
    est_cpk = target_spec / rss_val if rss_val != 0 else 0
    z_score = 3 * est_cpk
    yield_val = (2 * norm.cdf(z_score) - 1) * 100
else:
    worst_case, rss_val, est_cpk, yield_val = 0, 0, 0, 0

st.divider()

# 顯示結果
st.subheader("公差疊加分析結果 (Results)")
r1, r2, r3 = st.columns(3)
r1.metric("Worst Case (最壞情況)", f"± {worst_case:.3f} mm")
r2.metric("RSS Total (均方根)", f"± {rss_val:.3f} mm")
r3.metric("預估良率 (Yield)", f"{yield_val:.2f} %")

st.info(f"結論：若採用 {target_spec:.3f} mm 為規格，預估良率約為 {yield_val:.2f}%，CPK 約為 {est_cpk:.2f}。")

# --- 匯出 PDF 功能 ---
pdf_content = create_pdf(proj_name, analysis_title, target_spec, worst_case, rss_val, yield_val, est_cpk, edited_df)
st.download_button(
    label="📥 匯出 PDF 報告 (Export PDF)",
    data=pdf_content,
    file_name="tolerance_report.pdf",
    mime="application/pdf"
)
