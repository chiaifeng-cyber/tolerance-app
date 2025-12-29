import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import os

# 1. 頁面配置與精簡 CSS：解決標題遮擋與樣式需求
st.set_page_config(page_title="Tolerance Tool", layout="wide")
st.markdown("""<style>
    /* 增加頂部間距確保標題完全顯示 */
    .main .block-container { padding-top: 3.5rem !important; }
    h2 { line-height: 1.2; font-size: 24px; text-align: center; display: block !important; margin-top: -1.5rem; margin-bottom: 15px; }
    
    /* 區域標籤樣式 (20px) */
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p { font-size: 20px !important; font-weight: bold; color: #333; }
    
    /* Target Spec：字小一點點且改為黑色 */
    [data-testid="stNumberInput"] label p { font-size: 18px !important; font-weight: bold; color: #000 !important; }
    
    /* Metric 數值大小 */
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: bold; color: #1f77b4 !important; }
    
    /* 結論區底線 */
    .stTextArea textarea { background-attachment: local; background-size: 100% 2.2em; line-height: 2.2em !important; height: 120px !important;
        background-image: linear-gradient(to right, white 0px, transparent 0px), linear-gradient(#e0e0e0 1px, transparent 1px); }
    
    /* 隱藏冗餘工具列 */
    [data-testid="stElementToolbar"] { display: none !important; }
</style>""", unsafe_allow_html=True)

# 2. PDF 產生函數：強化資料轉換容錯
def create_pdf(proj, title, date, unit, target, wc, rss, cpk, yld, concl, df, img):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(190, 10, "Tolerance Stack-up Analysis Report", ln=True, align='C'); pdf.ln(5)
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
    for l, v in [("Project:", proj), ("Title:", title), ("Date:", date), ("Unit:", unit), ("Target Spec:", f"+/- {target:.3f}")]:
        pdf.cell(40, 7, l, 1, 0, 'L', True); pdf.set_font("Arial", '', 10); pdf.cell(150 if "Title" in l else 55, 7, str(v), 1, 1 if "Title" in l or "Unit" in l else 0)
    
    if img and os.path.exists(img): pdf.ln(5); pdf.image(img, x=10, w=100); pdf.ln(5)
    
    pdf.ln(2); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Input Data Details:", ln=True)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(230, 230, 230)
    for h, w in [("Part", 30), ("No.", 20), ("Description", 100), ("Tol (+/-)", 40)]: pdf.cell(w, 7, h, 1, 0, 'C', True)
    pdf.ln(7); pdf.set_font("Arial", '', 9)
    
    # 💡 核心修復：精確轉換數值，自動排除空行或非法文字
    for _, r in df.iterrows():
        try:
            val = float(r.iloc[4])
            pdf.cell(30, 7, str(r.iloc[0]), 1); pdf.cell(20, 7, str(r.iloc[2]), 1); pdf.cell(100, 7, str(r.iloc[3]), 1); pdf.cell(40, 7, f"{val:.3f}", 1, 1)
        except: continue

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(190, 8, "Analysis Summary:", ln=True)
    pdf.cell(190, 10, f"Worst Case: {wc:.3f} | RSS Total: {rss:.3f} | CPK: {cpk:.2f} | Yield: {yld:.2f}%", 1, 1, 'C')
    pdf.ln(5); pdf.cell(190, 8, "Final Conclusion:", ln=True); pdf.set_font("Arial", 'I', 10); pdf.multi_cell(190, 6, concl)
    return pdf.output(dest="S").encode("latin-1")

# 3. 初始化數據管理
COLS = ["Part 零件", "Req. CPK 要求", "No. 編號", "Description 描述", "Tol. 公差(±)"]
def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.1},
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "b", COLS[3]: "Unit mark to pad", COLS[4]: 0.1},
        {COLS[0]: "SMT", COLS[1]: 1.0, COLS[2]: "c", COLS[3]: "Assy Process", COLS[4]: 0.15},
        {COLS[0]: "Connector", COLS[1]: 1.33, COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
    ])

# 確保 Session State 穩定
if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
    st.session_state.target_val = 0.2
    st.session_state.concl_text = ""

def action(mode):
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame([{c: "" for c in COLS} for _ in range(6)])
        st.session_state.target_val = 0.0
    elif mode == "reset":
        st.session_state.df_data = get_init_df()
        st.session_state.target_val = 0.2
    st.rerun()

# 4. 主介面繪製
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.3, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input / 示意圖與數據輸入</p>', unsafe_allow_html=True)
    up = st.file_uploader("Upload Image", type=["jpg", "png"], label_visibility="collapsed")
    img_path = None
    if up:
        with open("temp.png", "wb") as f: f.write(up.getbuffer())
        img_path = "temp.png"; st.image(img_path, use_container_width=True)
    elif os.path.exists("4125.jpg"):
        img_path = "4125.jpg"; st.image(img_path, use_container_width=True)

    # 💡 極速輸入優化：移除 key 綁定，避免回寫造成的 5 秒延遲
    ed_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
    st.session_state.df_data = ed_df
    
    bc1, bc2, bc3 = st.columns(3)
    bc1.button("🗑️ Clear / 全部清除", on_click=action, args=("clear",), use_container_width=True)
    if bc2.button("🔄 Recalculate / 重新計算", use_container_width=True): st.rerun()
    bc3.button("⏪ Reset / 還原範例", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Info & Results / 專案資訊與結果</p>', unsafe_allow_html=True)
    with st.container(border=True):
        pn = st.text_input("Project Name", value="TM-P4125-001")
        at = st.text_input("Analysis Title", value="Connector Analysis")
        c1, c2 = st.columns(2)
        dt, ut = c1.text_input("Date", value="2025/12/29"), c2.text_input("Unit", value="mm")
    
    # 🎨 Target Spec 樣式優化
    ts = st.number_input("Target Spec 公差目標 (±)", value=st.session_state.target_val, format="%.3f")
    st.session_state.target_val = ts

    # 💡 即時計算邏輯
    tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    wc, rss = tols.sum(), np.sqrt((tols**2).sum())
    cpk = ts / rss if rss != 0 else 0
    yld = (2 * norm.cdf(3 * cpk) - 1) * 100
    
    res1, res2 = st.columns(2)
    res1.metric("Worst Case", f"± {wc:.3f}"); res2.metric("RSS Total", f"± {rss:.3f}")
    res1.metric("Est. CPK", f"{cpk:.2f}"); res2.metric("Est. Yield", f"{yld:.2f} %")

    

    st.divider()
    auto_con = f"1. Target +/-{ts:.3f}, CPK {cpk:.2f}, Yield {yld:.2f}%.\n2. \n3. "
    con_in = st.text_area("✍️ Conclusion 結論", value=st.session_state.concl_text or auto_con, height=120)
    st.session_state.concl_text = con_in
    
    # 📥 PDF 導出 (強化穩定性)
    pdf_data = create_pdf(pn, at, dt, ut, ts, wc, rss, cpk, yld, con_in, ed_df, img_path)
    st.download_button("📥 Export PDF Report", data=pdf_data, file_name=f"Report_{pn}.pdf", use_container_width=True)
