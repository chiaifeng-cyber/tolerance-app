import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置與 CSS 樣式 (保留 16:9 與底線設定)
st.set_page_config(page_title="Tolerance Tool", layout="wide")
st.markdown("""<style>
    .block-container { padding-top: 2.5rem !important; }
    h2 { line-height: 1.4; font-size: 26px; text-align: center; }
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p { font-size: 22px !important; font-weight: bold; color: #333; }
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: bold; color: #1f77b4; }
    .stTextArea textarea { background-attachment: local; background-size: 100% 2.2em; line-height: 2.2em !important; height: 160px !important;
        background-image: linear-gradient(to right, white 0px, transparent 0px), linear-gradient(#e0e0e0 1px, transparent 1px); }
    div[data-testid="stDataEditor"] > div { max-height: 280px !important; }
    [data-testid="stElementToolbar"] { display: none !important; }
    .element-container { margin-bottom: -10px !important; }
</style>""", unsafe_allow_html=True)

# 2. PDF 產生函數 (純英文 A4 彙整)
def create_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "Tolerance Stack-up Analysis Report", ln=True, align='C'); pdf.ln(2)
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
    infos = [("Project Name:", proj), ("Analysis Title:", title), ("Date:", date), ("Unit:", unit), ("Target:", f"+/- {target:.3f}")]
    for label, val in infos:
        pdf.cell(40, 7, label, 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(150 if "Title" in label else 55, 7, str(val), 1, 1 if "Title" in label or "Unit" in label else 0)
    if img and os.path.exists(img): pdf.ln(2); pdf.image(img, x=10, w=110); pdf.ln(2)
    pdf.ln(2); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data Details:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(230, 230, 230)
    headers = [("Part", 30), ("No.", 20), ("Description", 100), ("Tol (+/-)", 40)]
    for h, w in headers: pdf.cell(w, 7, h, 1, 0, 'C', True)
    pdf.ln(7); pdf.set_font("Arial", '', 9)
    for _, r in df.iterrows():
        pdf.cell(30, 7, str(r.iloc[0]), 1); pdf.cell(20, 7, str(r.iloc[2]), 1); pdf.cell(100, 7, str(r.iloc[3]), 1); pdf.cell(40, 7, f"{r.iloc[4]:.3f}", 1, 1)
    pdf.ln(4); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Analysis Summary (RSS 3-Sigma):", ln=True)
    res_line = f"Worst Case: {wc:.3f} | RSS Total: {rss:.3f} | CPK: {cpk:.2f} | Yield: {yld:.2f}%"
    pdf.cell(190, 10, res_line, 1, 1, 'C'); pdf.ln(4); pdf.cell(190, 8, "Final Conclusion:", ln=True)
    pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, concl)
    return pdf.output(dest="S").encode("latin-1")

# 3. 初始化數據與邏輯
COLS = ["Part 零件", "Req. CPK 要求", "No. 編號", "Description 描述", "Tol. 公差(±)"]
DEFAULTS = {
    "df_data": pd.DataFrame([{"Part 零件": "PCB", "Req. CPK 要求": 1.33, "No. 編號": "a", "Description 描述": "Panel mark", "Tol. 公差(±)": 0.1},
                             {"Part 零件": "Connector", "Req. CPK 要求": 1.33, "No. 編號": "d", "Description 描述": "Housing", "Tol. 公差(±)": 0.125}]),
    "target_val": 0.2, "proj_name": "TM-P4125-001", "analysis_title": "Connector Analysis", "date": "2025/12/29", "unit": "mm", "show_img": True, "concl_text": ""
}

def init_state(reset=False):
    for k, v in DEFAULTS.items():
        if k not in st.session_state or reset: st.session_state[k] = v

init_state()

def action(mode):
    if mode == "clear":
        for k in ["proj_name", "analysis_title", "date", "unit", "concl_text"]: st.session_state[k] = ""
        st.session_state.df_data, st.session_state.target_val, st.session_state.show_img = pd.DataFrame(columns=COLS), 0.0, False
    else: init_state(True)

# 4. 主介面
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.3, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input / 示意圖與數據輸入</p>', unsafe_allow_html=True)
    img = "4125.jpg" if st.session_state.show_img and os.path.exists("4125.jpg") else None
    if img: st.image(img, use_container_width=True)
    else:
        up = st.file_uploader("Upload New Diagram", type=["jpg", "png"])
        if up: 
            with open("temp.png", "wb") as f: f.write(up.getbuffer())
            img = "temp.png"; st.image(img, use_container_width=True)
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True, key="main_editor")
    st.caption("💡 點擊左側序號選取並按 Delete 刪除。")
    c1, c2 = st.columns(2)
    c1.button("🗑️ Clear All / 全部清除", on_click=action, args=("clear",), use_container_width=True)
    c2.button("🔄 Reset / 還原範例", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Info & Results / 專案資訊與結果</p>', unsafe_allow_html=True)
    with st.container(border=True):
        pn = st.text_input("Project Name", key="proj_name")
        at = st.text_input("Analysis Title", key="analysis_title")
        c1, c2 = st.columns(2)
        dt, ut = c1.text_input("Date", key="date"), c2.text_input("Unit", key="unit")
    ts = st.number_input("Target Spec (±)", value=st.session_state.target_val, format="%.3f", key="target_input")
    
    wc = ed_df[COLS[4]].sum() if not ed_df.empty else 0
    rss = np.sqrt((ed_df[COLS[4]]**2).sum()) if not ed_df.empty else 0
    cpk = ts / rss if rss != 0 else 0
    yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    
    res1, res2 = st.columns(2)
    res1.metric("Worst Case", f"± {wc:.3f}"); res2.metric("RSS Total", f"± {rss:.3f}")
    res1.metric("Est. CPK", f"{cpk:.2f}"); res2.metric("Est. Yield", f"{yld:.2f} %")

    

    st.divider()
    auto_con = f"1. Target +/-{ts:.3f}, CPK {cpk:.2f}, Yield {yld:.2f}%.\n2. \n3. "
    con_in = st.text_area("✍️ Conclusion 結論", value=st.session_state.concl_text or auto_con, height=160, key="concl_area")
    st.session_state.concl_text = con_in
    try:
        pdf_b = create_pdf(pn, at, dt, ut, ts, wc, rss, cpk, yld, con_in, ed_df, img)
        st.download_button("📥 Export PDF Report", data=pdf_b, file_name=f"Report_{pn}.pdf", use_container_width=True)
    except: st.error("PDF Error")
