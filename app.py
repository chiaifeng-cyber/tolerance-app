import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面設定 (Page Config)
st.set_page_config(page_title="Tolerance Tool", layout="wide")

# 2. CSS：修正標題切頂、放大雙語字體、優化結論底線間距
st.markdown("""
    <style>
    /* 修正頂部邊距 (Fix top margin) */
    .block-container { padding-top: 3.5rem !important; padding-bottom: 0rem !important; }
    
    /* 標題與標籤雙語字體放大 (En/Ch Label scaling) */
    h2 { line-height: 1.6 !important; font-size: 26px !important; text-align: center; margin-bottom: 10px !important; }
    [data-testid="stMetricLabel"] { font-size: 20px !important; font-weight: bold !important; color: #333 !important; }
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold !important; color: #1f77b4 !important; }
    
    /* 結論區底線間距優化 (Conclusion underlines spacing) */
    .stTextArea textarea {
        background-attachment: local;
        background-image: linear-gradient(to right, white 0px, transparent 0px), 
                          linear-gradient(to left, white 0px, transparent 0px), 
                          linear-gradient(#e0e0e0 1px, transparent 1px);
        background-size: 100% 2.2em;
        line-height: 2.2em !important;
        height: 180px !important;
        padding-top: 8px !important;
    }

    /* 隱藏表格工具列與功能選單 (Hide table toolbar) */
    [data-testid="stElementToolbar"] { display: none !important; }
    
    /* 壓縮間距符合 16:9 (16:9 optimization) */
    div[data-testid="stDataEditor"] > div { max-height: 280px !important; }
    .element-container { margin-bottom: -5px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (純英文報告 / English Report Only)
def create_full_report_pdf(proj, title, date, unit, target, wc, rss, cpk, yield_val, concl, df, img_path):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="Tolerance Stack-up Analysis Report", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 7, "Project Name:", 1); pdf.set_font("Arial", '', 10); pdf.cell(145, 7, str(proj), 1, 1)
    pdf.cell(45, 7, "Analysis Title:", 1); pdf.set_font("Arial", '', 10); pdf.cell(145, 7, str(title), 1, 1)
    
    if img_path:
        pdf.ln(5)
        pdf.image(img_path, x=10, w=100)
        pdf.ln(60)

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 7, "Part", 1, 0, 'C', True); pdf.cell(20, 7, "No.", 1, 0, 'C', True); pdf.cell(100, 7, "Description", 1, 0, 'C', True); pdf.cell(40, 7, "Tol (+/-)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(30, 7, str(row.iloc[0]), 1)
        pdf.cell(20, 7, str(row.iloc[2]), 1)
        pdf.cell(100, 7, str(row.iloc[3]), 1)
        pdf.cell(40, 7, f"{row.iloc[4]:.3f}", 1, 1)
    
    pdf.ln(5); pdf.set_font("Arial", 'B', 12)
    pdf.cell(47, 10, f"Worst Case: {wc:.3f}", 1, 0, 'C'); pdf.cell(47, 10, f"RSS: {rss:.3f}", 1, 0, 'C')
    pdf.cell(48, 10, f"CPK: {cpk:.2f}", 1, 0, 'C'); pdf.cell(48, 10, f"Yield: {yield_val:.2f}%", 1, 1, 'C')

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Conclusion:", ln=True)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, txt=concl)
    return pdf.output(dest="S").encode("latin-1")

# 4. 初始化與清除邏輯 (State Management)
DEFAULT_DATA = [
    {"Part 零件": "PCB", "Req. CPK 要求": 1.33, "No. 編號": "a", "Description 描述": "Panel mark to mark", "Upper Tol 上限公差": 0.100},
    {"Part 零件": "PCB", "Req. CPK 要求": 1.33, "No. 編號": "b", "Description 描述": "Unit mark to pad", "Upper Tol 上限公差": 0.100},
    {"Part 零件": "SMT", "Req. CPK 要求": 1.00, "No. 編號": "c", "Description 描述": "Placement Tol", "Upper Tol 上限公差": 0.150},
    {"Part 零件": "Connector", "Req. CPK 要求": 1.33, "No. 編號": "d", "Description 描述": "Housing Tol", "Upper Tol 上限公差": 0.125}
]

if 'df_data' not in st.session_state: st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
if 'target_val' not in st.session_state: st.session_state.target_val = 0.200
if 'proj_name' not in st.session_state: st.session_state.proj_name = "TM-P4125-001"
if 'analysis_title' not in st.session_state: st.session_state.analysis_title = "Connector Y-Position Analysis"
if 'date' not in st.session_state: st.session_state.date = "2025/12/29"
if 'unit' not in st.session_state: st.session_state.unit = "mm"
if 'show_example_img' not in st.session_state: st.session_state.show_example_img = True
if 'concl_text' not in st.session_state: st.session_state.concl_text = ""

def clear_all():
    st.session_state.df_data = pd.DataFrame(columns=DEFAULT_DATA[0].keys())
    st.session_state.target_val = 0.000
    st.session_state.proj_name = ""
    st.session_state.analysis_title = ""
    st.session_state.date = ""
    st.session_state.unit = ""
    st.session_state.show_example_img = False
    st.session_state.concl_text = ""

def reset_all():
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
    st.session_state.target_val = 0.200
    st.session_state.proj_name = "TM-P4125-001"
    st.session_state.analysis_title = "Connector Y-Position Analysis"
    st.session_state.date = "2025/12/29"
    st.session_state.unit = "mm"
    st.session_state.show_example_img = True

# 5. 主標題 (Bilingual Header)
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)

l_col, r_col = st.columns([1.3, 1])

with l_col:
    st.subheader("🖼️ Diagram & Input / 示意圖與數據輸入")
    img_pdf = None
    if st.session_state.show_example_img and os.path.exists("4125.jpg"):
        st.image("4125.jpg", use_container_width=True)
        img_pdf = "4125.jpg"
    else:
        up_file = st.file_uploader("Upload New Diagram / 上傳新示意圖", type=["jpg", "png", "jpeg"])
        if up_file:
            st.image(up_file, use_container_width=True)
            with open("temp.png", "wb") as f: f.write(up_file.getbuffer())
            img_pdf = "temp.png"

    # 數據表格 (Bilingual Columns, No Index)
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True, hide_index=True)
    st.session_state.df_data = ed_df
    
    bc1, bc2 = st.columns(2)
    with bc1: st.button("🗑️ Clear All / 全部清除", on_click=clear_all, use_container_width=True)
    with bc2: st.button("🔄 Reset / 還原範例", on_click=reset_all, use_container_width=True)

with r_col:
    st.subheader("📋 Info & Results / 專案資訊與結果")
    with st.container(border=True):
        p_n = st.text_input("Project Name 專案名稱", key="proj_name")
        a_t = st.text_input("Analysis Title 分析標題", key="analysis_title")
        c1, c2 = st.columns(2)
        with c1: d_t = st.text_input("Date 日期", key="date")
        with c2: u_t = st.text_input("Unit 單位", key="unit")

    t_s = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f", key="target_val_input")
    st.session_state.target_val = t_s
    
    # 計算 (Calculation)
    tol_col = "Upper Tol 上限公差"
    if not ed_df.empty and tol_col in ed_df.columns:
        wc = ed_df[tol_col].sum()
        rss = np.sqrt((ed_df[tol_col]**2).sum())
        cpk = t_s / rss if rss != 0 else 0
        yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    else: wc, rss, cpk, yld = 0, 0, 0, 0

    # 分析結果 (Bilingual Metric Labels)
    res1, res2 = st.columns(2)
    res1.metric("Worst Case (最壞情況)", f"± {wc:.3f}")
    res2.metric("RSS Total (均方根)", f"± {rss:.3f}")
    res1.metric("Est. CPK (預估 CPK)", f"{cpk:.2f}")
    res2.metric("Est. Yield (預估良率)", f"{yld:.2f} %")

    # 結論填寫區 (Bilingual, Bottom-lined)
    st.divider()
    con_def = f"Conclusion: Target +/-{t_s:.3f}, CPK {cpk:.2f}, Yield {yld:.2f}%."
    con_in = st.text_area("Conclusion 結論 (Editable)", value=st.session_state.concl_text if st.session_state.concl_text else con_def, height=180)
    st.session_state.concl_text = con_in

    # PDF 匯出 (Export)
    try:
        pdf_bytes = create_full_report_pdf(p_n, a_t, d_t, u_t, t_s, wc, rss, cpk, yld, con_in, ed_df, img_pdf)
        st.download_button("📥 Export PDF Report / 匯出報告", data=pdf_bytes, file_name=f"Report_{p_n}.pdf", use_container_width=True)
    except: st.error("PDF Exporting...")
