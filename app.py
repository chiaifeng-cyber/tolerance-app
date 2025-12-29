import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置與 CSS 樣式 (徹底解決標題遮擋與字體加大)
st.set_page_config(page_title="Tolerance Tool", layout="wide")
st.markdown("""<style>
    /* 增加頂部間距，確保標題上半部不被遮擋 */
    .main .block-container { padding-top: 4rem !important; }
    
    /* 大型字標題強制顯示 */
    h2 { line-height: 1.5; font-size: 26px; text-align: center; margin-top: -2rem; margin-bottom: 20px; display: block !important; }
    
    /* 中型字標籤 (22px) */
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p { font-size: 22px !important; font-weight: bold; color: #333; }
    
    /* Target Spec 標籤與數值加大 */
    [data-testid="stNumberInput"] label p { font-size: 24px !important; font-weight: bold; color: #d32f2f !important; }
    [data-testid="stNumberInput"] input { font-size: 22px !important; font-weight: bold; }
    
    /* 結果數值 (28px) */
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: bold; color: #1f77b4 !important; }
    
    /* 結論區底線間距 */
    .stTextArea textarea { background-attachment: local; background-size: 100% 2.2em; line-height: 2.2em !important; height: 140px !important;
        background-image: linear-gradient(to right, white 0px, transparent 0px), linear-gradient(#e0e0e0 1px, transparent 1px); }
    
    /* 佈局壓縮與工具列隱藏 */
    div[data-testid="stDataEditor"] > div { max-height: 260px !important; }
    [data-testid="stElementToolbar"] { display: none !important; }
    .element-container { margin-bottom: -10px !important; }
</style>""", unsafe_allow_html=True)

# 2. PDF 產生函數 (解決新數據行導出異常)
def create_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "Tolerance Stack-up Analysis Report", ln=True, align='C'); pdf.ln(2)
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
    infos = [("Project Name:", proj), ("Analysis Title:", title), ("Date:", date), ("Unit:", unit), ("Target Spec:", f"+/- {target:.3f}")]
    for l, v in infos:
        pdf.cell(45, 7, l, 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(145 if "Title" in l else 50, 7, str(v), 1, 1 if "Title" in l or "Unit" in l else 0)
    if img and os.path.exists(img): pdf.ln(2); pdf.image(img, x=10, w=110); pdf.ln(2)
    pdf.ln(2); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data Details:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(230, 230, 230)
    for h, w in [("Part", 30), ("No.", 20), ("Description", 100), ("Tol (+/-)", 40)]: pdf.cell(w, 7, h, 1, 0, 'C', True)
    pdf.ln(7); pdf.set_font("Arial", '', 9)
    # 過濾手動輸入的無效數據列
    for _, r in df.iterrows():
        try:
            val = float(r.iloc[4])
            pdf.cell(30, 7, str(r.iloc[0]), 1); pdf.cell(20, 7, str(r.iloc[2]), 1); pdf.cell(100, 7, str(r.iloc[3]), 1); pdf.cell(40, 7, f"{val:.3f}", 1, 1)
        except: continue
    pdf.ln(4); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Analysis Summary (RSS 3-Sigma):", ln=True)
    pdf.cell(190, 10, f"Worst Case: {wc:.3f} | RSS Total: {rss:.3f} | CPK: {cpk:.2f} | Yield: {yld:.2f}%", 1, 1, 'C')
    pdf.ln(4); pdf.cell(190, 8, "Final Conclusion:", ln=True); pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, concl)
    return pdf.output(dest="S").encode("latin-1")

# 3. 初始化數據 (刪除 Other 行)
COLS = ["Part 零件", "Req. CPK 要求", "No. 編號", "Description 描述", "Tol. 公差(±)"]
def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.1},
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.1},
        {COLS[0]: "SMT", COLS[1]: 1.0, COLS[2]: "c", COLS[3]: "Assy Process", COLS[4]: 0.15},
        {COLS[0]: "Connector", COLS[1]: 1.33, COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
    ])

if 'df_data' not in st.session_state:
    for k, v in {"df_data": get_init_df(), "target_val": 0.2, "proj_name": "TM-P4125-001", "analysis_title": "Connector Analysis", "date": "2025/12/29", "unit": "mm", "show_img": True, "concl_text": "", "uploaded_img": None}.items():
        st.session_state[k] = v

def action(mode):
    if mode == "clear":
        for k in ["proj_name", "analysis_title", "date", "unit", "concl_text"]: st.session_state[k] = ""
        st.session_state.df_data, st.session_state.target_val, st.session_state.show_img, st.session_state.uploaded_img = pd.DataFrame([{c: "" for c in COLS} for _ in range(6)]), 0.0, False, None
    elif mode == "reset":
        for k, v in {"df_data": get_init_df(), "target_val": 0.2, "proj_name": "TM-P4125-001", "analysis_title": "Connector Analysis", "date": "2025/12/29", "unit": "mm", "show_img": True, "concl_text": "", "uploaded_img": None}.items():
            st.session_state[k] = v
    st.rerun()

# 4. 主介面繪製
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.3, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input / 示意圖與數據輸入</p>', unsafe_allow_html=True)
    display_img = st.session_state.uploaded_img if st.session_state.uploaded_img else ("4125.jpg" if st.session_state.show_img and os.path.exists("4125.jpg") else None)
    if display_img:
        st.image(display_img, use_container_width=True)
        if st.button("🗑️ Remove Diagram / 移除圖片"):
            st.session_state.uploaded_img, st.session_state.show_img = None, False
            st.rerun()
    else:
        up = st.file_uploader("Upload New Diagram", type=["jpg", "png"])
        if up:
            with open("uploaded_temp.png", "wb") as f: f.write(up.getbuffer())
            st.session_state.uploaded_img = "uploaded_temp.png"; st.rerun()

    # 💡 數據編輯器：優化輸入流暢度
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
    st.session_state.df_data = ed_df
    
    st.caption("💡 點擊左側序號選取並按 Delete 刪除。")
    bc1, bc2, bc3 = st.columns(3)
    bc1.button("🗑️ Clear / 全部清除", on_click=action, args=("clear",), use_container_width=True)
    if bc2.button("🔄 Recalculate / 重新計算", use_container_width=True): st.rerun()
    bc3.button("⏪ Reset / 還原範例", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Info & Results / 專案資訊與結果</p>', unsafe_allow_html=True)
    with st.container(border=True):
        pn, at = st.text_input("Project Name", key="proj_name"), st.text_input("Analysis Title", key="analysis_title")
        c1, c2 = st.columns(2)
        dt, ut = c1.text_input("Date", key="date"), c2.text_input("Unit", key="unit")
    
    # Target Spec 字體加大與顏色標註
    ts = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f", key="target_input")
    st.session_state.target_val = ts

    # 💡 強制數據即時同步
    tol_vals = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    wc, rss = tol_vals.sum(), np.sqrt((tol_vals**2).sum())
    cpk = ts / rss if rss != 0 else 0
    yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    
    res1, res2 = st.columns(2)
    res1.metric("Worst Case (最壞情況)", f"± {wc:.3f}"); res2.metric("RSS Total (均方根)", f"± {rss:.3f}")
    res1.metric("Est. CPK (預估 CPK)", f"{cpk:.2f}"); res2.metric("Est. Yield (預估良率)", f"{yld:.2f} %")

    st.divider()
    auto_con = f"1. Target +/-{ts:.3f}, CPK {cpk:.2f}, Yield {yld:.2f}%.\n2. \n3. "
    con_in = st.text_area("✍️ Conclusion 結論 (Editable)", value=st.session_state.concl_text or auto_con, height=140, key="concl_area")
    st.session_state.concl_text = con_in
    
    try:
        pdf_img = st.session_state.uploaded_img if st.session_state.uploaded_img else (display_img if (display_img and os.path.exists(display_img)) else None)
        pdf_b = create_pdf(pn, at, dt, ut, ts, wc, rss, cpk, yld, con_in, ed_df, pdf_img)
        st.download_button("📥 Export PDF Report / 匯出報告", data=pdf_b, file_name=f"Report_{pn}.pdf", use_container_width=True)
    except: st.error("PDF Syncing Error... Please click 'Recalculate' button above.")
