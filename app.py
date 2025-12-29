import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置與進階 CSS 樣式
st.set_page_config(page_title="Tolerance Tool", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #f0f2f6; }
    .main .block-container { padding-top: 2rem !important; padding-bottom: 0rem !important; }
    h2 { line-height: 1.1; font-size: 22px; text-align: center; margin-top: -1rem; margin-bottom: 10px; color: #333; }
    
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p { 
        font-size: 18px !important; font-weight: bold !important; color: #333; 
    }
    
    /* 專案資訊標籤非粗體 */
    .stTextInput label p { font-weight: normal !important; font-size: 14px !important; }
    
    /* Target Spec 標籤粗體 */
    [data-testid="stNumberInput"] label p { font-size: 16px !important; font-weight: bold !important; color: #000 !important; }
    
    /* 圓角反白輸入框 */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        padding: 5px !important;
    }
    div[data-testid="stDataEditor"] { background-color: #ffffff !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; color: #1f77b4 !important; }
    [data-testid="stElementToolbar"] { display: none !important; }
</style>""", unsafe_allow_html=True)

# 2. PDF 產生函數
def create_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "Tolerance Stack-up Analysis Report", ln=True, align='C'); pdf.ln(5)
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
    for l, v in [("Project:", proj), ("Title:", title), ("Date:", date), ("Unit:", unit), ("Target Spec:", f"+/- {target:.3f}")]:
        pdf.cell(40, 7, l, 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(145 if "Title" in l else 50, 7, str(v), 1, 1 if "Title" in l or "Unit" in l else 0)
    
    if img and isinstance(img, str) and os.path.exists(img):
        try: pdf.ln(5); pdf.image(img, x=10, w=100); pdf.ln(5)
        except: pass
        
    pdf.ln(2); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data Details:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(230, 230, 230)
    for h, w in [("Part", 30), ("No.", 20), ("Description", 100), ("Tol (+/-)", 40)]: pdf.cell(w, 7, h, 1, 0, 'C', True)
    pdf.ln(7); pdf.set_font("Arial", '', 9)
    for _, r in df.iterrows():
        try:
            val = float(r.iloc[4])
            pdf.cell(30, 7, str(r.iloc[0]), 1); pdf.cell(20, 7, str(r.iloc[2]), 1); pdf.cell(100, 7, str(r.iloc[3]), 1); pdf.cell(40, 7, f"{val:.3f}", 1, 1)
        except: continue
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Analysis Summary:", ln=True)
    pdf.cell(190, 10, f"Worst Case: {wc} | RSS Total: {rss} | CPK: {cpk} | Yield: {yld}", 1, 1, 'C')
    pdf.ln(5); pdf.cell(190, 8, "Final Conclusion:", ln=True); pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, concl)
    return pdf.output(dest="S").encode("latin-1")

# 3. 初始化數據管理 (更新標題名稱)
COLS = ["Part 零件", "Req. CPK 要求 (min. 1.0)", "No. 編號", "Description 描述", "Tol. 公差(±)"]
def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.1},
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "b", COLS[3]: "Unit mark to pad", COLS[4]: 0.1},
        {COLS[0]: "SMT", COLS[1]: 1.0, COLS[2]: "c", COLS[3]: "Assy Process", COLS[4]: 0.15},
        {COLS[0]: "Connector", COLS[1]: 1.33, COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
    ])

if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
    st.session_state.proj_name, st.session_state.analysis_title = "TM-P4125-001", "Connector Analysis"
    st.session_state.date, st.session_state.unit = "2025/12/30", "mm"
    st.session_state.target_val = 0.2
    st.session_state.results = {"wc": "± 0.475", "rss": "± 0.241", "cpk": "0.83", "yld": "98.72 %"}
    st.session_state.show_img, st.session_state.is_cleared = True, False

def action(mode):
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame([{c: "" for c in COLS} for _ in range(6)])
        st.session_state.proj_name, st.session_state.analysis_title, st.session_state.date, st.session_state.unit = "", "", "", ""
        st.session_state.target_val, st.session_state.results = 0.0, {"wc": "", "rss": "", "cpk": "", "yld": ""}
        st.session_state.show_img = False
        if os.path.exists("temp.png"): os.remove("temp.png")
        st.session_state.is_cleared = True
    elif mode == "reset":
        st.session_state.df_data = get_init_df()
        st.session_state.proj_name, st.session_state.analysis_title, st.session_state.date, st.session_state.unit = "TM-P4125-001", "Connector Analysis", "2025/12/30", "mm"
        st.session_state.target_val, st.session_state.results = 0.2, {"wc": "± 0.475", "rss": "± 0.241", "cpk": "0.83", "yld": "98.72 %"}
        st.session_state.show_img, st.session_state.is_cleared = True, False
    st.rerun()

# 4. 主介面
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.3, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input / 示意圖與數據輸入</p>', unsafe_allow_html=True)
    up = st.file_uploader("Upload Image", type=["jpg", "png"], label_visibility="collapsed")
    current_img = None
    if up:
        with open("temp.png", "wb") as f: f.write(up.getbuffer())
        st.session_state.show_img = True
    
    if st.session_state.show_img:
        current_img = "temp.png" if os.path.exists("temp.png") else ("4125.jpg" if os.path.exists("4125.jpg") else None)
        if current_img: st.image(current_img, use_container_width=True)

    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
    st.session_state.df_data = ed_df
    
    bc1, bc2, bc3 = st.columns(3)
    bc1.button("🗑️ Clear / 全部清除", on_click=action, args=("clear",), use_container_width=True)
    if bc2.button("🔄 Recalculate / 重新計算", use_container_width=True):
        # 💡 使用更新後的列標題抓取數據
        tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
        wc_v, rss_v = tols.sum(), np.sqrt((tols**2).sum())
        ts_v = st.session_state.target_val
        cpk_v = ts_v / rss_v if rss_v != 0 else 0
        st.session_state.results = {"wc": f"± {wc_v:.3f}", "rss": f"± {rss_v:.3f}", "cpk": f"{cpk_v:.2f}", "yld": f"{(2 * norm.cdf(3 * cpk_v) - 1) * 100:.2f} %"}
        st.session_state.is_cleared = False
        st.rerun()
    bc3.button("⏪ Reset / 還原範例", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Project information / 專案資訊</p>', unsafe_allow_html=True)
    with st.container(border=True):
        st.session_state.proj_name = st.text_input("Project Name", value=st.session_state.proj_name)
        st.session_state.analysis_title = st.text_input("Analysis Title", value=st.session_state.analysis_title)
        c1, c2 = st.columns(2)
        st.session_state.date = c1.text_input("Date", value=st.session_state.date)
        st.session_state.unit = c2.text_input("Unit", value=st.session_state.unit)
    
    st.session_state.target_val = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f")

    res1, res2 = st.columns(2)
    res1.metric("Worst Case", st.session_state.results["wc"])
    res2.metric("RSS Total", st.session_state.results["rss"])
    res1.metric("Est. CPK", st.session_state.results["cpk"])
    res2.metric("Est. Yield", st.session_state.results["yld"])

    st.divider()
    con_auto = f"1. Target +/-{st.session_state.target_val:.3f}, CPK {st.session_state.results['cpk']}, Yield {st.session_state.results['yld']}."
    con_in = st.text_area("✍️ Conclusion 結論", value=con_auto if not st.session_state.is_cleared else "", height=100)
    
    res = st.session_state.results
    pdf_b = create_pdf(st.session_state.proj_name, st.session_state.analysis_title, st.session_state.date, st.session_state.unit, st.session_state.target_val, res["wc"], res["rss"], res["cpk"], res["yld"], con_in, ed_df, current_img if st.session_state.show_img else None)
    st.download_button("📥 Export PDF Report", data=pdf_b, file_name=f"Report_{st.session_state.proj_name}.pdf", use_container_width=True)
