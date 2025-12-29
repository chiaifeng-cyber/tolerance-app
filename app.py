import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置 (Page Config)
st.set_page_config(page_title="Tolerance Tool", layout="wide")

# 2. CSS 樣式：精確控制字體層次與佈局
st.markdown("""
    <style>
    /* 修正頂部邊距，確保 16:9 一畫面全覽 */
    .block-container { padding-top: 2.5rem !important; padding-bottom: 0rem !important; }
    
    /* 大型字 (Title Layer): 26px 加粗 */
    h2 { line-height: 1.4 !important; font-size: 26px !important; text-align: center; margin-bottom: 10px !important; }
    
    /* 中型字 (Section Labels): 22px 加粗 */
    .section-label, [data-testid="stMetricLabel"], .stTextArea label, .stSubheader h3 { 
        font-size: 22px !important; 
        font-weight: bold !important; 
        color: #333 !important; 
    }
    
    /* 結果數值字體: 30px 加粗藍色 */
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold !important; color: #1f77b4 !important; }
    
    /* 結論區底線間距優化：拉開文字與線的距離 */
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

    /* 隱藏表格工具列並壓縮間距 */
    [data-testid="stElementToolbar"] { display: none !important; }
    div[data-testid="stDataEditor"] > div { max-height: 280px !important; }
    .element-container { margin-bottom: -10px !important; }
    hr { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (純英文報告輸出)
def create_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="Tolerance Stack-up Analysis Report", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    data_map = {"Project": proj, "Title": title, "Date": date, "Unit": unit, "Target": f"+/- {target:.3f}"}
    for k, v in data_map.items():
        pdf.cell(45, 7, f"{k}:", 1); pdf.cell(145, 7, str(v), 1, 1)
    if img and os.path.exists(img):
        pdf.ln(5)
        pdf.image(img, x=10, w=100)
        pdf.ln(60)
    pdf.set_font("Arial", 'B', 12)
    pdf.ln(5)
    pdf.cell(190, 10, f"Results: WC={wc:.3f}, RSS={rss:.3f}, CPK={cpk:.2f}, Yield={yld:.2f}%", ln=True)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(190, 6, txt=f"Conclusion: {concl}")
    return pdf.output(dest="S").encode("latin-1")

# 4. 初始化 Session State
COLS = ["Part 零件", "Req. CPK 要求", "No. 編號", "Description 描述", "Tol. 公差"]
DEFAULT_DATA = [
    {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.1},
    {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.1},
    {COLS[0]: "SMT", COLS[1]: 1.0, COLS[2]: "c", COLS[3]: "SMT tolerance", COLS[4]: 0.15},
    {COLS[0]: "Connector", COLS[1]: 1.33, COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
]
# 結論區預設格式
DEFAULT_CONCL = "1. \n2. \n3. \n4. \n5. "

def init_state(reset_all=False):
    if 'df_data' not in st.session_state or reset_all:
        st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
    if 'target_val' not in st.session_state or reset_all:
        st.session_state.target_val = 0.2
    if 'proj_name' not in st.session_state or reset_all:
        st.session_state.proj_name = "TM-P4125-001"
    if 'analysis_title' not in st.session_state or reset_all:
        st.session_state.analysis_title = "Connector Analysis"
    if 'date' not in st.session_state or reset_all:
        st.session_state.date = "2025/12/29"
    if 'unit' not in st.session_state or reset_all:
        st.session_state.unit = "mm"
    if 'show_img' not in st.session_state or reset_all:
        st.session_state.show_img = True
    if 'concl_text' not in st.session_state or reset_all:
        st.session_state.concl_text = DEFAULT_CONCL

init_state()

def action_all(mode):
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame(columns=COLS)
        st.session_state.target_val = 0.0
        st.session_state.show_img = False
        st.session_state.proj_name, st.session_state.analysis_title = "", ""
        st.session_state.date, st.session_state.unit = "", ""
        st.session_state.concl_text = DEFAULT_CONCL
    else: init_state(reset_all=True)

# 5. 主介面繪製
# 大型字標題
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)

l_col, r_col = st.columns([1.3, 1])

with l_col:
    # 中型字區域標籤
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
    # 中型字區域標籤
    st.markdown('<p class="section-label">📋 Info & Results / 專案資訊與結果</p>', unsafe_allow_html=True)
    with st.container(border=True):
        p_n = st.text_input("Project Name 專案名稱", key="proj_name")
        a_t = st.text_input("Analysis Title 分析標題", key="analysis_title")
        c1, c2 = st.columns(2)
        d_t = c1.text_input("Date 日期", key="date")
        u_t = c2.text_input("Unit 單位", key="unit")

    t_s = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f", key="target_input")
    st.session_state.target_val = t_s
    
    # 計算邏輯
    wc = ed_df[COLS[4]].sum() if not ed_df.empty else 0
    rss = np.sqrt((ed_df[COLS[4]]**2).sum()) if not ed_df.empty else 0
    cpk = t_s / rss if rss != 0 else 0
    yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    
    res_c1, res_c2 = st.columns(2)
    # 中型字分析標籤
    res_c1.metric("Worst Case (最壞情況)", f"± {wc:.3f}")
    res_c2.metric("RSS Total (均方根)", f"± {rss:.3f}")
    res_c1.metric("Est. CPK (預估 CPK)", f"{cpk:.2f}")
    res_c2.metric("Est. Yield (預估良率)", f"{yld:.2f} %")

    st.divider()
    # ✍️ 結論區標籤 (22px 中型字)
    con_in = st.text_area("✍️ Conclusion 結論 (Editable)", value=st.session_state.concl_text, height=180, key="concl_area")
    st.session_state.concl_text = con_in

    try:
        pdf_b = create_pdf(p_n, a_t, d_t, u_t, t_s, wc, rss, cpk, yld, con_in, ed_df, img_pdf)
        st.download_button("📥 Export PDF Report / 匯出報告", data=pdf_b, file_name=f"Report_{p_n}.pdf", use_container_width=True)
    except: st.error("PDF Exporting Error...")
