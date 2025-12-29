import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置 (Page Config)
st.set_page_config(page_title="Tolerance Tool", layout="wide")

# 2. CSS 樣式：優化 16:9 佈局、字體層次與底線間距
st.markdown("""
    <style>
    .block-container { padding-top: 2.5rem !important; padding-bottom: 0rem !important; }
    h2 { line-height: 1.4 !important; font-size: 26px !important; text-align: center; margin-bottom: 10px !important; }
    
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p, .stSubheader h3 { 
        font-size: 22px !important; font-weight: bold !important; color: #333 !important; margin-bottom: 5px !important;
    }
    
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold !important; color: #1f77b4 !important; }
    
    .stTextArea textarea {
        background-attachment: local;
        background-image: linear-gradient(to right, white 0px, transparent 0px), 
                          linear-gradient(to left, white 0px, transparent 0px), 
                          linear-gradient(#e0e0e0 1px, transparent 1px);
        background-size: 100% 2.2em; line-height: 2.2em !important; height: 180px !important; padding-top: 8px !important;
    }

    [data-testid="stElementToolbar"] { display: none !important; }
    div[data-testid="stDataEditor"] > div { max-height: 280px !important; }
    .element-container { margin-bottom: -10px !important; }
    hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (彙整全畫面 + 純英文標籤)
def create_full_page_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="Tolerance Stack-up Analysis Report", ln=True, align='C')
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 7, "Project Name:", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(150, 7, str(proj), 1, 1)
    pdf.cell(40, 7, "Analysis Title:", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(150, 7, str(title), 1, 1)
    pdf.cell(40, 7, "Date:", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(55, 7, str(date), 1, 0); 
    pdf.cell(40, 7, "Unit:", 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(55, 7, str(unit), 1, 1)
    
    if img and os.path.exists(img):
        pdf.ln(4)
        pdf.image(img, x=10, w=110)
        pdf.ln(2)
    
    pdf.ln(2); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data Details:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 7, "Part", 1, 0, 'C', True); pdf.cell(20, 7, "No.", 1, 0, 'C', True); 
    pdf.cell(100, 7, "Description", 1, 0, 'C', True); pdf.cell(40, 7, "Tol (+/-)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        pdf.cell(30, 7, str(row.iloc[0]), 1)
        pdf.cell(20, 7, str(row.iloc[2]), 1)
        pdf.cell(100, 7, str(row.iloc[3]), 1)
        pdf.cell(40, 7, f"{row.iloc[4]:.3f}", 1, 1)
        
    pdf.ln(4); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Analysis Summary (RSS 3-Sigma):", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(47, 10, f"Worst Case: {wc:.3f}", 1, 0, 'C'); pdf.cell(47, 10, f"RSS Total: {rss:.3f}", 1, 0, 'C')
    pdf.cell(48, 10, f"Est. CPK: {cpk:.2f}", 1, 0, 'C'); pdf.cell(48, 10, f"Est. Yield: {yld:.2f}%", 1, 1, 'C')

    pdf.ln(4); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Final Conclusion:", ln=True)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, txt=concl)
    return pdf.output(dest="S").encode("latin-1")

# 4. 初始化與 Session State
COLS = ["Part 零件", "Req. CPK 要求", "No. 編號", "Description 描述", "Tol. 公差(±)"]
DEFAULT_DATA = [
    {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.1},
    {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "b", COLS[3]: "Unit mark to pad", COLS[4]: 0.1},
    {COLS[0]: "SMT", COLS[1]: 1.0, COLS[2]: "c", COLS[3]: "SMT tolerance", COLS[4]: 0.15},
    {COLS[0]: "Connector", COLS[1]: 1.33, COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
]
# 結論縮減為 3 行模板
DEFAULT_CONCL_TEMPLATE = "1. {}\n2. \n3. "

def init_state(reset_all=False):
    if 'df_data' not in st.session_state or reset_all: st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
    if 'target_val' not in st.session_state or reset_all: st.session_state.target_val = 0.2
    if 'proj_name' not in st.session_state or reset_all: st.session_state.proj_name = "TM-P4125-001"
    if 'analysis_title' not in st.session_state or reset_all: st.session_state.analysis_title = "Connector Analysis"
    if 'date' not in st.session_state or reset_all: st.session_state.date = "2025/12/29"
    if 'unit' not in st.session_state or reset_all: st.session_state.unit = "mm"
    if 'show_img' not in st.session_state or reset_all: st.session_state.show_img = True
    st.session_state.concl_text = ""

init_state()

def action_all(mode):
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame(columns=COLS); st.session_state.target_val = 0.0
        st.session_state.show_img = False; st.session_state.concl_text = ""
        for k in ["proj_name", "analysis_title", "date", "unit"]: st.session_state[k] = ""
    else: init_state(reset_all=True)

# 5. 主介面繪製
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l_col, r_col = st.columns([1.3, 1])

with l_col:
    st.markdown('<p class="section-label">🖼️ Diagram & Input / 示意圖與數據輸入</p>', unsafe_allow_html=True)
    img_pdf = "4125.jpg" if st.session_state.show_img and os.path.exists("4125.jpg") else None
    if img_pdf: st.image(img_pdf, use_container_width=True)
    else:
        up = st.file_uploader("Upload New Diagram", type=["jpg", "png"])
        if up: 
            st.image(up, use_container_width=True)
            with open("temp.png", "wb") as f: f.write(up.getbuffer())
            img_pdf = "temp.png"

    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True, hide_index=False, key="main_editor")
    st.session_state.df_data = ed_df
    st.caption("💡 點擊左側序號選取該列，按 Delete 鍵即可刪除。")
    bc1, bc2 = st.columns(2)
    bc1.button("🗑️ Clear All / 全部清除", on_click=action_all, args=("clear",), use_container_width=True)
    bc2.button("🔄 Reset / 還原範例", on_click=action_all, args=("reset",), use_container_width=True)

with r_col:
    st.markdown('<p class="section-label">📋 Info & Results / 專案資訊與結果</p>', unsafe_allow_html=True)
    with st.container(border=True):
        p_n = st.text_input("Project Name 專案名稱", key="proj_name")
        a_t = st.text_input("Analysis Title 分析標題", key="analysis_title")
        c1, c2 = st.columns(2)
        d_t, u_t = c1.text_input("Date 日期", key="date"), c2.text_input("Unit 單位", key="unit")

    t_s = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f", key="target_input")
    st.session_state.target_val = t_s
    
    # 計算邏輯
    wc = ed_df[COLS[4]].sum() if not ed_df.empty else 0
    rss = np.sqrt((ed_df[COLS[4]]**2).sum()) if not ed_df.empty else 0
    cpk = t_s / rss if rss != 0 else 0
    yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    
    res_c1, res_c2 = st.columns(2)
    res_c1.metric("Worst Case (最壞情況)", f"± {wc:.3f}"); res_c2.metric("RSS Total (均方根)", f"± {rss:.3f}")
    res_c1.metric("Est. CPK (預估 CPK)", f"{cpk:.2f}"); res_c2.metric("Est. Yield (預估良率)", f"{yld:.2f} %")

    st.divider()
    con_auto = f"Target +/-{t_s:.3f}, CPK {cpk:.2f}, Yield {yld:.2f}%."
    if not st.session_state.concl_text: st.session_state.concl_text = DEFAULT_CONCL_TEMPLATE.format(con_auto)

    # 結論區固定顯示三行
    con_in = st.text_area("✍️ Conclusion 結論 (Editable)", value=st.session_state.concl_text, height=180, key="concl_area")
    st.session_state.concl_text = con_in

    try:
        # PDF 匯出優化：緊湊間距並移除中文字元
        pdf_b = create_full_page_pdf(p_n, a_t, d_t, u_t, t_s, wc, rss, cpk, yld, con_in, ed_df, img_pdf)
        st.download_button("📥 Export PDF Report / 匯出報告", data=pdf_b, file_name=f"Report_{p_n}.pdf", use_container_width=True)
    except: st.error("PDF Exporting Error...")
