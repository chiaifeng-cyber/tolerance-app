import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置 (Page Config)
st.set_page_config(page_title="Tolerance Tool", layout="wide")

# 2. CSS：修正標題切頂、放大雙語標籤、優化結論底線間距、隱藏索引
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
        background-size: 100% 2.2em; /* 拉開行間距 (Increase line spacing) */
        line-height: 2.2em !important; /* 文字浮在線上 (Float text on lines) */
        height: 180px !important;
        padding-top: 8px !important;
    }

    /* 隱藏表格工具列 (Hide table toolbar) */
    [data-testid="stElementToolbar"] { display: none !important; }
    
    /* 壓縮間距符合 16:9 (16:9 optimization) */
    div[data-testid="stDataEditor"] > div { max-height: 280px !important; }
    .element-container { margin-bottom: -5px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. PDF 產生函數 (純英文報告 / English Report Only)
def create_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Tolerance Analysis Report", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    data_map = {"Project": proj, "Title": title, "Date": date, "Unit": unit, "Target": f"+/- {target:.3f}"}
    for k, v in data_map.items():
        pdf.cell(45, 7, f"{k}:", 1); pdf.cell(145, 7, str(v), 1, 1)
    if img: pdf.image(img, x=10, w=100); pdf.ln(60)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Results: WC={wc:.3f}, RSS={rss:.3f}, CPK={cpk:.2f}, Yield={yld:.2f}%", ln=True)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, f"Conclusion: {concl}")
    return pdf.output(dest="S").encode("latin-1")

# 4. 初始化 Session State
COLS = ["Part 零件", "Req. CPK 要求", "No. 編號", "Description 描述", "Tol. 公差"]
DEFAULT_DATA = [
    {"Part 零件": "PCB", "Req. CPK 要求": 1.33, "No. 編號": "a", "Description 描述": "Panel mark to unit mark", "Tol. 公差": 0.1},
    {"Part 零件": "PCB", "Req. CPK 要求": 1.33, "No. 編號": "b", "Description 描述": "Unit mark to soldering pad", "Tol. 公差": 0.1},
    {"Part 零件": "SMT", "Req. CPK 要求": 1.0, "No. 編號": "c", "Description 描述": "SMT tolerance", "Tol. 公差": 0.15},
    {"Part 零件": "Connector", "Req. CPK 要求": 1.33, "No. 編號": "d", "Description 描述": "Connector housing", "Tol. 公差": 0.125}
]

for key, val in {"df_data": pd.DataFrame(DEFAULT_DATA), "target_val": 0.2, "proj_name": "TM-P4125-001", 
                 "analysis_title": "Connector Y-Position Analysis", "date": "2025/12/17", "unit": "mm", 
                 "show_img": True, "concl_text": ""}.items():
    if key not in st.session_state: st.session_state[key] = val

def action_all(mode):
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame(columns=COLS)
        st.session_state.target_val, st.session_state.show_img = 0.0, False
        for k in ["proj_name", "analysis_title", "date", "unit", "concl_text"]: st.session_state[k] = ""
    else: # reset
        st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)
        st.session_state.target_val, st.session_state.show_img = 0.2, True
        st.session_state.proj_name, st.session_state.analysis_title = "TM-P4125-001", "Connector Y-Position Analysis"
        st.session_state.date, st.session_state.unit = "2025/12/17", "mm"

# 5. 主介面繪製 (Header)
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l_col, r_col = st.columns([1.3, 1])

with l_col:
    st.subheader("🖼️ Diagram & Input / 示意圖與數據輸入")
    img_path = "4125.jpg" if st.session_state.show_img and os.path.exists("4125.jpg") else None
    if img_path: st.image(img_path, use_container_width=True)
    else: 
        up = st.file_uploader("Upload New Diagram / 上傳新示意圖", type=["jpg", "png"])
        if up: 
            st.image(up, use_container_width=True)
            with open("temp.png", "wb") as f: f.write(up.getbuffer())
            img_path = "temp.png"
    
    # 數據編輯器：啟用 num_rows="dynamic" 即可刪除列 (Select row and press Delete)
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True, hide_index=False)
    st.session_state.df_data = ed_df
    
    c1, c2 = st.columns(2)
    c1.button("🗑️ Clear All / 全部清除", on_click=action_all, args=("clear",), use_container_width=True)
    c2.button("🔄 Reset / 還原範例", on_click=action_all, args=("reset",), use_container_width=True)

with r_col:
    st.subheader("📋 Info & Results / 專案資訊與結果")
    with st.container(border=True):
        p_n = st.text_input("Project Name 專案名稱", key="proj_name")
        a_t = st.text_input("Analysis Title 分析標題", key="analysis_title")
        c1, c2 = st.columns(2)
        d_t, u_t = c1.text_input("Date 日期", key="date"), c2.text_input("Unit 單位", key="unit")

    t_s = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f", key="target_input")
    st.session_state.target_val = t_s
    
    # 計算邏輯 (Calculation)
    wc = ed_df[COLS[4]].sum() if not ed_df.empty else 0
    rss = np.sqrt((ed_df[COLS[4]]**2).sum()) if not ed_df.empty else 0
    cpk = t_s / rss if rss != 0 else 0
    yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    
    res = st.columns(2)
    res[0].metric("Worst Case (最壞情況)", f"± {wc:.3f}")
    res[1].metric("RSS Total (均方根)", f"± {rss:.3f}")
    res[0].metric("Est. CPK (預估 CPK)", f"{cpk:.2f}")
    res[1].metric("Est. Yield (預估良率)", f"{yld:.2f} %")

    st.divider()
    def_con = f"Target +/-{t_s:.3f}, CPK {cpk:.2f}, Yield {yld:.2f}%."
    con_in = st.text_area("Conclusion 結論", value=st.session_state.concl_text or def_con, height=180)
    st.session_state.concl_text = con_in

    try:
        pdf_b = create_pdf(p_n, a_t, d_t, u_t, t_s, wc, rss, cpk, yld, con_in, ed_df, img_path)
        st.download_button("📥 Export PDF Report / 匯出報告", data=pdf_b, file_name=f"Report_{p_n}.pdf", use_container_width=True)
    except: st.error("PDF Exporting...")
