import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import datetime
import os

# 設定頁面
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# --- CSS 樣式：調整結果數值與標題字體 ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 24px !important;
        font-weight: bold !important;
    }
    .element-container { margin-bottom: -10px !important; }
    .stImage { margin-bottom: -20px !important; }
    h3 { margin-top: -10px !important; padding-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 產生函數 (模擬完整 App 畫面佈局) ---
def create_full_report_pdf(proj, title, date, unit, target, wc, rss, yield_val, cpk, df, img_path=None):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # 1. 頁面大標題
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 15, txt="Design Tolerance Stack-up Analysis Report", ln=True, align='C')
    pdf.ln(2)

    # 2. 專案基本資訊 (表格形式)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(45, 8, "Project Name", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, proj, 1)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 8, "Date", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, date, 1, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 8, "Analysis Title", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, title, 1)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 8, "Unit", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, unit, 1, 1)
    pdf.ln(5)

    # 3. 範例示意圖 (若檔案存在則嵌入)
    if img_path and os.path.exists(img_path):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, "Example Diagram:", ln=True)
        # 調整圖片大小以符合 A4 寬度，並保持比例
        pdf.image(img_path, x=10, y=pdf.get_y(), w=140)
        pdf.ln(70) # 預留圖片高度空間

    # 4. 公差數據表格
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Input Data Table:", ln=True)
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(20, 7, "Part", 1, 0, 'C', True)
    pdf.cell(10, 7, "No.", 1, 0, 'C', True)
    pdf.cell(90, 7, "Description", 1, 0, 'C', True)
    pdf.cell(35, 7, "Req. CPK", 1, 0, 'C', True)
    pdf.cell(35, 7, "Tol (+/-)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(20, 7, str(row['Part']), 1)
        pdf.cell(10, 7, str(row['No.']), 1)
        pdf.cell(90, 7, str(row['Description']), 1)
        pdf.cell(35, 7, f"{row['Req. CPK']:.2f}", 1)
        pdf.cell(35, 7, f"{row['Upper Tol']:.3f}", 1, 1)
    pdf.ln(5)

    # 5. 分析結果 (大字體加強)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "Summary Results:", ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(31, 119, 180) # 藍色字體
    pdf.cell(63, 10, f"Worst Case: +/- {wc:.3f}", 1, 0, 'C')
    pdf.cell(63, 10, f"RSS Total: +/- {rss:.3f}", 1, 0, 'C')
    pdf.cell(64, 10, f"Yield: {yield_val:.2f} %", 1, 1, 'C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'I', 10)
    pdf.ln(2)
    pdf.multi_cell(190, 8, txt=f"Conclusion: Based on the target spec of +/- {target:.3f} mm, the estimated assembly yield is {yield_val:.2f}% with a CPK of {cpk:.2f}.", border=0)

    # 頁尾
    pdf.set_y(-20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 10, txt=f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align='R')
    
    return pdf.output(dest="S").encode("latin-1")

# --- 資料初始化 ---
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

# --- 介面佈局 ---
st.markdown("<h2 style='text-align: center;'>設計累計公差分析</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Design Tolerance Stack-up Analysis</h4>", unsafe_allow_html=True)

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        proj_name = st.text_input("專案名稱 (Project Name)", "TM-P4125-001")
        title_text = st.text_input("分析標題 (Title)", "Connector Y-Position Analysis")
    with c2:
        date_text = st.text_input("日期 (Date)", "2025/12/29")
        unit_text = st.text_input("尺寸單位 (Unit)", "mm")

st.divider()

# --- 範例圖片 ---
st.subheader("範例示意圖 (Example Diagram)")
img_filename = "4125.jpg"
if os.path.exists(img_filename):
    st.image(img_filename, caption="分析參考圖示", use_container_width=True)
else:
    st.info("💡 請確保 GitHub 內有 4125.jpg 以便在 PDF 報告中顯示圖片。")

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
    yield_val = (2 * norm.cdf(3 * cpk) - 1) * 100
else:
    wc, rss, cpk, yield_val = 0, 0, 0, 0

st.divider()

# --- 結果顯示 ---
st.subheader("分析結果 (Results)")
r1, r2, r3 = st.columns(3)
r1.metric("Worst Case", f"± {wc:.3f} mm")
r2.metric("RSS Total", f"± {rss:.3f} mm")
r3.metric("預估良率 (Yield)", f"{yield_val:.2f} %")

st.info(f"結論：若採用 {target_spec:.3f} mm 為規格，預估良率為 {yield_val:.2f}%，CPK 為 {cpk:.2f}。")

# --- PDF 匯出 (全畫面整合版) ---
try:
    pdf_bytes = create_full_report_pdf(proj_name, title_text, date_text, unit_text, target_spec, wc, rss, yield_val, cpk, edited_df, img_filename)
    st.download_button(
        label="📥 匯出完整 A4 PDF 報告",
        data=pdf_bytes,
        file_name=f"Tolerance_Full_Report_{proj_name}.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"PDF 匯出失敗: {e}")
    st.warning("請注意：PDF 目前僅支援英文與數字內容顯示。")
