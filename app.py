import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面設定
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# 2. CSS：修正標題、16:9 佈局、結論區底線、表格優化
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; padding-bottom: 0rem !important; }
    h2 { line-height: 1.6 !important; font-size: 26px !important; text-align: center; margin-bottom: 10px !important; }
    
    /* 結果數值與標籤放大 */
    [data-testid="stMetricLabel"] { font-size: 22px !important; font-weight: bold !important; color: #333 !important; }
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold !important; color: #1f77b4 !important; }
    
    /* 結論區底線模擬 (5行) */
    .stTextArea textarea {
        background-attachment: local;
        background-image: linear-gradient(to right, white 0px, transparent 0px), 
                          linear-gradient(to left, white 0px, transparent 0px), 
                          linear-gradient(#e0e0e0 1px, transparent 1px);
        background-size: 100% 2em;
        line-height: 2em !important;
        height: 165px !important;
    }

    /* 隱藏多餘表格工具列 */
    [data-testid="stElementToolbar"] { display: none !important; }
    
    /* 壓縮間距符合 16:9 */
    div[data-testid="stDataEditor"] > div { max-height: 250px !important; }
    .element-container { margin-bottom: -5px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (純英文版)
def create_full_report_pdf(proj, title, date, unit, target, wc, rss, cpk, yield_val, concl, df, img_path):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="Tolerance Stack-up Analysis Report", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 7, "Project Name:", 1); pdf.set_font("Arial", '', 10); pdf.cell(145, 7, str(proj), 1, 1)
    pdf.cell(45, 7, "Analysis Title:", 1); pdf.cell(145, 7, str(title), 1, 1)
    
    if img_path and os.path.exists(img_path):
        pdf.ln(5)
        pdf.image(img_path, x=10, w=100)
        pdf.ln(60)

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 7, "Part", 1, 0, 'C', True); pdf.cell(20, 7, "No.", 1, 0, 'C', True); pdf.cell(100, 7, "Description", 1, 0, 'C', True); pdf.cell(40, 7, "Tol (+/-)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(30, 7, str(row['Part']), 1)
        pdf.cell(20, 7, str(row['No.']), 1)
        pdf.cell(100, 7, str(row['Description']), 1)
        pdf.cell(40, 7, f"{row['Upper Tol']:.3f}", 1, 1)

    pdf.ln(5); pdf.set_font("Arial", 'B', 12)
    pdf.cell(47, 10, f"Worst Case: {wc:.3f}", 1, 0, 'C')
    pdf.cell(47, 10, f"RSS: {rss:.3f}", 1, 0, 'C')
    pdf.cell(48, 10, f"CPK: {cpk:.2f}", 1, 0, 'C')
    pdf.cell(48, 10, f"Yield: {yield_val:.2f}%", 1, 1, 'C')

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Conclusion:", ln=True)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, txt=concl)
    return pdf.output(dest="S").encode("latin-1")

# 4. 初始化 Session State
DEFAULT_DATA = [
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "a", "Description": "Panel mark to mark", "Upper Tol": 0.100},
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "b", "Description": "Unit mark to pad", "Upper Tol": 0.100},
    {"Part": "SMT", "Req. CPK": 1.00, "No.": "c", "Description": "Placement Tol", "Upper Tol": 0.150},
    {"Part": "Connector", "Req. CPK": 1.33, "No.": "d", "Description": "Housing Tol", "Upper Tol": 0.125}
]

if 'df_data' not in st.session_state: st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
if 'show_img' not in st.session_state: st.session_state.show_img = True
if 'target_val' not in st.session_state: st.session_state.target_val = 0.200

# 清除與還原功能
def clear_all_data():
    st.session_state.df_data = pd.DataFrame(columns=["Part", "Req. CPK", "No.", "Description", "Upper Tol"])
    st.session_state.show_img = False
    st.session_state.target_val = 0.000
    st.session_state.concl = ""

def reset_to_default():
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
    st.session_state.show_img = True
    st.session_state.target_val = 0.200

# 5. 主標題
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)

l_col, r_col = st.columns([1.3, 1])

with l_col:
    st.subheader("🖼️ Diagram & Input / 示意圖與數據輸入")
    img_fn = "4125.jpg"
    if st.session_state.show_img and os.path.exists(img_fn):
        st.image(img_fn, use_container_width=True)
    
    # 數據表格：num_rows="dynamic" 啟用增加/刪除列功能
    # 表格內點擊左側勾選框即可使用快捷鍵或按鈕刪除
    ed_df = st.data_editor(
        st.session_state.df_data, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=False  # 顯示索引以利選取列進行刪除
    )
    st.session_state.df_data = ed_df
    
    bc1, bc2 = st.columns(2)
    with bc1: st.button("🗑️ Clear All / 全部清除", on_click=clear_all_data, use_container_width=True)
    with bc2: st.button("🔄 Reset / 還原範例", on_click=reset_to_default, use_container_width=True)

with r_col:
    st.subheader("📋 Info & Results / 專案資訊與結果")
    with st.container(border=True):
        p_name = st.text_input("Project Name", "TM-P4125-001")
        t_title = st.text_input("Analysis Title", "Connector Y-Position Analysis")
        c1, c2 = st.columns(2)
        with c1: d_text = st.text_input("Date", "2025/12/29")
        with c2: u_text = st.text_input("Unit", "mm")

    # 綁定 Session State 的 Target Spec
    t_spec = st.number_input("Target Spec (±)", value=st.session_state.target_val, format="%.3f", key="target_input")
    st.session_state.target_val = t_spec
    
    # 計算
    if not ed_df.empty and "Upper Tol" in ed_df.columns:
        wc = ed_df["Upper Tol"].sum()
        rss = np.sqrt((ed_df["Upper Tol"]**2).sum())
        cpk_res = t_spec / rss if rss != 0 else 0
        y_val = (2 * norm.cdf(3 * cpk_res) - 1) * 100
    else: wc, rss, cpk_res, y_val = 0, 0, 0, 0

    # 結果
    res_c1, res_c2 = st.columns(2)
    res_c1.metric("Worst Case", f"± {wc:.3f}")
    res_c2.metric("RSS Total", f"± {rss:.3f}")
    res_c1.metric("Est. CPK", f"{cpk_res:.2f}")
    res_c2.metric("Est. Yield", f"{y_val:.2f} %")

    # 結論填寫區 (5行高度 + 淡淡底線)
    st.divider()
    concl_input = st.text_area("Conclusion / 結論 (Self-editable)", 
                               value=f"Conclusion: Target +/-{t_spec:.3f} mm, CPK {cpk_res:.2f}.", 
                               height=165)

    # PDF 匯出
    try:
        pdf_out = create_full_report_pdf(p_name, t_title, d_text, u_text, t_spec, wc, rss, cpk_res, y_val, concl_input, ed_df, img_fn if st.session_state.show_img else None)
        st.download_button("📥 Export PDF Report", data=pdf_out, file_name=f"Report_{p_name}.pdf", use_container_width=True)
    except: st.error("PDF Exporting...")
