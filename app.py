import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF

# 設定頁面
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# --- CSS 樣式：字體加大與間距優化 ---
st.markdown("""
    <style>
    /* 加大結果數值的字體 */
    [data-testid="stMetricValue"] {
        font-size: 40px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
    }
    /* 縮小間距 */
    .element-container { margin-bottom: -10px !important; }
    .stImage { margin-bottom: -20px !important; }
    h3 { margin-top: -10px !important; padding-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 產生函數 ---
def create_pdf(proj, title, target, wc, rss, yield_val, cpk):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Tolerance Analysis Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Project: {proj}", ln=True)
    pdf.cell(200, 10, txt=f"Title: {title}", ln=True)
    pdf.cell(200, 10, txt=f"Target: +/- {target:.3f} mm", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Results:", ln=True)
    pdf.cell(200, 10, txt=f"- Worst Case: +/- {wc:.3f} mm", ln=True)
    pdf.cell(200, 10, txt=f"- RSS Total: +/- {rss:.3f} mm", ln=True)
    pdf.cell(200, 10, txt=f"- Yield: {yield_val:.2f} % / CPK: {cpk:.2f}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 資料初始化與還原功能 ---
DEFAULT_DATA = [
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "a", "Description": "Panel mark to unit mark", "Upper Tol": 0.100, "Lower Tol": 0.100},
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "b", "Description": "Unit mark to soldering pad", "Upper Tol": 0.100, "Lower Tol": 0.100},
    {"Part": "SMT", "Req. CPK": 1.00, "No.": "c", "Description": "SMT tolerance", "Upper Tol": 0.150, "Lower Tol": 0.150},
    {"Part": "Connector", "Req. CPK": 1.33, "No.": "d", "Description": "Connector housing (0.25/2)", "Upper Tol": 0.125, "Lower Tol": 0.125},
]

if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

def clear_all():
    st.session_state.df_data = pd.DataFrame(columns=["Part", "Req. CPK", "No.", "Description", "Upper Tol", "Lower Tol"])

def reset_default():
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

# --- 介面開始 ---
st.markdown("<h2 style='text-align: center;'>設計累計公差分析</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Design Tolerance Stack-up Analysis</h4>", unsafe_allow_html=True)

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        proj_name = st.text_input("專案名稱 (Project Name)", "TM-P4125-001")
        title_text = st.text_input("分析標題 (Title)", "Connector Y-Position Analysis")
    with c2:
        st.text_input("日期 (Date)", "2025/12/29")
        st.text_input("尺寸單位 (Unit)", "mm")

st.divider()

# --- 範例圖片顯示區域 ---
st.subheader("範例示意圖 (Example Diagram)")
# 直接顯示您上傳過的圖片 (請確保 GitHub 儲存庫內有 4125.jpg 檔案，或使用下方 Uploader)
try:
    st.image("4125.jpg", caption="公差標註範例", use_container_width=True)
except:
    st.info("💡 提示：若要顯示預設圖片，請將圖片命名為 4125.jpg 並上傳至 GitHub 儲存庫。")
    uploaded_image = st.file_uploader("或手動匯入圖片檔", type=["png", "jpg", "jpeg"], key="uploader")
    if uploaded_image:
        st.image(uploaded_image, use_container_width=True)

st.divider()

# --- 數據輸入 ---
st.subheader("公差數據輸入 (Input Table)")
col_btn1, col_btn2, _ = st.columns([1, 1, 4])
with col_btn1:
    st.button("🗑️ 一鍵清除", on_click=clear_all, use_container_width=True)
with col_btn2:
    st.button("🔄 一鍵還原範例", on_click=reset_default, use_container_width=True)

edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
st.session_state.df_data = edited_df

target_spec = st.number_input("目前設計公差目標 (Target Spec ±)", value=0.200, format="%.3f")

# --- 核心邏輯計算 ---
if not edited_df.empty and "Upper Tol" in edited_df.columns:
    wc = edited_df["Upper Tol"].sum()
    rss = np.sqrt((edited_df["Upper Tol"]**2).sum())
    cpk = target_spec / rss if rss != 0 else 0
    z_score = 3 * cpk
    yield_val = (2 * norm.cdf(z_score) - 1) * 100
else:
    wc, rss, cpk, yield_val = 0, 0, 0, 0

st.divider()

# --- 結果顯示 (字體已加大) ---
st.subheader("分析結果 (Results)")
r1, r2, r3 = st.columns(3)
r1.metric("Worst Case", f"± {wc:.3f} mm")
r2.metric("RSS Total", f"± {rss:.3f} mm")
r3.metric("預估良率 (Yield)", f"{yield_val:.2f} %")

st.info(f"結論：若採用 {target_spec:.3f} mm 為規格，預估良率為 {yield_val:.2f}%，CPK 為 {cpk:.2f}。")

# PDF 下載
try:
    pdf_bytes = create_pdf(proj_name, title_text, target_spec, wc, rss, yield_val, cpk)
    st.download_button("📥 匯出 PDF 報告", data=pdf_bytes, file_name="Tolerance_Report.pdf", mime="application/pdf")
except:
    st.warning("PDF 僅支援英文字元產生。")
