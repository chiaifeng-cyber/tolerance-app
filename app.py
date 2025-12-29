import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import datetime
import os

# 1. 頁面設定：寬螢幕模式
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# 2. CSS：16:9 佈局壓縮與字體放大
st.markdown("""
    <style>
    /* 壓縮邊距確保 16:9 單屏全覽 */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; }
    
    /* 標題與標籤字體 */
    h2 { line-height: 1.2 !important; font-size: 26px !important; text-align: center; margin-bottom: 5px !important; }
    h3 { font-size: 18px !important; margin-bottom: 5px !important; }
    
    /* 結果標題 (Metric Label) 放大 1.5 倍 */
    [data-testid="stMetricLabel"] { font-size: 22px !important; font-weight: bold !important; color: #333 !important; }
    
    /* 結果數值 (Metric Value) 放大至 30px */
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold !important; color: #1f77b4 !important; }
    
    /* 縮小間距與限制表格高度 */
    .element-container { margin-bottom: -8px !important; }
    div[data-testid="stDataEditor"] > div { max-height: 280px !important; }
    .stTextInput > div { margin-bottom: -10px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (雙語報告)
def create_report_pdf(proj, title, date, unit, target, wc, rss, yield_val, cpk, concl, df, img_path):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="Tolerance Stack-up Analysis Report / 公差疊加分析報告", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(40, 7, "Project Name / 專案名稱:", 1); pdf.cell(150, 7, str(proj), 1, 1)
    pdf.cell(40, 7, "Analysis Title / 分析標題:", 1); pdf.cell(150, 7, str(title), 1, 1)
    if img_path and os.path.exists(img_path):
        pdf.image(img_path, x=10, w=120); pdf.ln(65)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(63, 10, f"Worst Case: {wc:.3f}", 1); pdf.cell(63, 10, f"RSS: {rss:.3f}", 1); pdf.cell(64, 10, f"Yield: {yield_val:.2f}%", 1, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(190, 7, txt=f"Conclusion / 結論: {concl}")
    return pdf.output(dest="S").encode("latin-1")

# 4. 資料初始化
DEFAULT_DATA = [
    {"Part 零件": "PCB", "No. 編號": "a", "Description 描述": "Panel mark to unit mark", "Upper Tol 上限公差": 0.100},
    {"Part 零件": "PCB", "No. 編號": "b", "Description 描述": "Unit mark to soldering pad", "Upper Tol 上限公差": 0.100},
    {"Part 零件": "SMT", "No. 編號": "c", "Description 描述": "SMT tolerance", "Upper Tol": 0.150},
    {"Part 零件": "Connector", "No. 編號": "d", "Description 描述": "Connector housing", "Upper Tol 上限公差": 0.125}
]
if 'df_data' not in st.session_state: st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

# 5. 主標題 (雙語)
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)

# 6. 左右分欄 (左側放圖與表，右側放資訊、結果與結論)
l_col, r_col = st.columns([1.2, 1])

with l_col:
    st.subheader("🖼️ Diagram & Input / 示意圖與數據輸入")
    img_fn = "4125.jpg"
    if os.path.exists(img_fn): st.image(img_fn, use_container_width=True)
    
    # 數據編輯區
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
    st.session_state.df_data = ed_df
    
    # 清除與還原按鈕
    bc1, bc2 = st.columns(2)
    with bc1: 
        if st.button("🗑️ Clear / 清除", use_container_width=True):
            st.session_state.df_data = pd.DataFrame(columns=DEFAULT_DATA[0].keys())
            st.rerun()
    with bc2: 
        if st.button("🔄 Reset / 還原範例", use_container_width=True):
            st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
            st.rerun()

with r_col:
    st.subheader("📋 Info & Results / 專案資訊與結果")
    with st.container(border=True):
        p_name = st.text_input("Project Name 專案名稱", "TM-P4125-001")
        t_title = st.text_input("Analysis Title 分析標題", "Connector Y-Position Analysis")
        c1, c2 = st.columns(2)
        with c1: d_text = st.text_input("Date 日期", "2025/12/29")
        with c2: u_text = st.text_input("Unit 單位", "mm")

    t_spec = st.number_input("Target Spec 公差目標 (±)", value=0.200, format="%.3f")
    
    # 計算邏輯
    col_name = "Upper Tol 上限公差" if "Upper Tol 上限公差" in ed_df.columns else ed_df.columns[-1]
    if not ed_df.empty and col_name in ed_df.columns:
        wc = ed_df[col_name].sum()
        rss = np.sqrt((ed_df[col_name]**2).sum())
        cpk = t_spec / rss if rss != 0 else 0
        y_val = (2 * norm.cdf(3 * cpk) - 1) * 100
    else: wc, rss, cpk, y_val = 0, 0, 0, 0

    # 分析結果區 (四格 Metric)
    res_c1, res_c2 = st.columns(2)
    res_c1.metric("Worst Case (最壞情況)", f"± {wc:.3f}")
    res_c2.metric("RSS Total (均方根)", f"± {rss:.3f}")
    res_c1.metric("Est. CPK (預估 CPK)", f"{cpk:.2f}")
    res_c2.metric("Est. Yield (預估良率)", f"{y_val:.2f} %")

    # 結論填寫區
    st.divider()
    concl_input = st.text_area("Conclusion 結論 (可自行編輯)", 
                               value=f"若採用 {t_spec:.3f} mm 為規格，預估良率約為 {y_val:.2f}%，CPK 約為 {cpk:.2f}。")

    # PDF 下載
    try:
        pdf_out = create_report_pdf(p_name, t_title, d_text, u_text, t_spec, wc, rss, y_val, cpk, concl_input, ed_df, img_fn)
        st.download_button("📥 Export PDF / 匯出報告", data=pdf_out, file_name=f"Report_{p_name}.pdf", use_container_width=True)
    except: st.warning("PDF export supports English characters / PDF 匯出暫不支援中文標題輸入。")
