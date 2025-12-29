import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. 頁面配置與進階 CSS
st.set_page_config(page_title="Tolerance Tool", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #f0f2f6; }
    /* 縮小邊距以符合 Window 介面全覽 */
    .main .block-container { padding-top: 2.2rem !important; padding-bottom: 0rem !important; }
    h2 { line-height: 1.1; font-size: 22px; text-align: center; margin-top: -1.5rem; margin-bottom: 10px; color: #333; }
    
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p { 
        font-size: 18px !important; font-weight: bold !important; color: #333; 
    }
    
    /* 專案資訊標籤設定為非粗體 */
    .stTextInput label p { font-weight: normal !important; font-size: 14px !important; }
    
    /* Target Spec 標籤設定為黑色粗體 */
    [data-testid="stNumberInput"] label p { font-size: 16px !important; font-weight: bold !important; color: #000 !important; }
    
    /* 圓角反白輸入框樣式 */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        padding: 5px !important;
        border: 1px solid #d1d5db !important;
    }
    div[data-testid="stDataEditor"] { background-color: #ffffff !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; color: #1f77b4 !important; }
    [data-testid="stElementToolbar"] { display: none !important; }
</style>""", unsafe_allow_html=True)

# 2. 初始化數據管理
COLS = ["Part 零件", "Req. CPK 要求 (min. 1.0)", "No. 編號", "Description 描述", "Tol. 公差(±)"]
def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.1},
        {COLS[0]: "PCB", COLS[1]: 1.33, COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.1},
        {COLS[0]: "SMT", COLS[1]: 1.0, COLS[2]: "c", COLS[3]: "Assy Process", COLS[4]: 0.15},
        {COLS[0]: "Connector", COLS[1]: 1.33, COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
    ])

if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
    st.session_state.target_val, st.session_state.show_img = 0.2, True
    st.session_state.results = {"wc": "± 0.475", "rss": "± 0.241", "cpk": "0.83", "yld": "98.72 %"}
    st.session_state.is_cleared = False

def action(mode):
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame([{c: "" for c in COLS} for _ in range(6)])
        st.session_state.target_val, st.session_state.results = 0.0, {"wc":"", "rss":"", "cpk":"", "yld":""}
        st.session_state.show_img, st.session_state.is_cleared = False, True
        if os.path.exists("temp.png"): os.remove("temp.png")
    elif mode == "reset":
        st.session_state.df_data, st.session_state.target_val = get_init_df(), 0.2
        st.session_state.results = {"wc": "± 0.475", "rss": "± 0.241", "cpk": "0.83", "yld": "98.72 %"}
        st.session_state.show_img, st.session_state.is_cleared = False, False
    st.rerun()

# 3. 主介面
st.markdown("<h2>設計累計公差分析工具 / Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.3, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input / 示意圖與數據輸入</p>', unsafe_allow_html=True)
    up = st.file_uploader("Upload Image", type=["jpg", "png"], label_visibility="collapsed")
    if up:
        with open("temp.png", "wb") as f: f.write(up.getbuffer())
        st.session_state.show_img = True
    if st.session_state.show_img:
        current_img = "temp.png" if os.path.exists("temp.png") else ("4125.jpg" if os.path.exists("4125.jpg") else None)
        if current_img: st.image(current_img, use_container_width=True)

    # 數據編輯器：根據圖片比例設定欄位寬度比例
    ed_df = st.data_editor(
        st.session_state.df_data, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            COLS[0]: st.column_config.TextColumn(width="small"),      # Part 約 15%
            COLS[1]: st.column_config.TextColumn(width="small"),      # Req. CPK 約 15%
            COLS[2]: st.column_config.TextColumn(width="small"),      # No. 約 10%
            COLS[3]: st.column_config.TextColumn(width="large"),      # Description 約 45%
            COLS[4]: st.column_config.NumberColumn(width="small"),    # Tol. 約 15%
        }
    )
    st.session_state.df_data = ed_df
    
    # 即時計算 Worst Case
    current_tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    real_wc = current_tols.sum()
    if not st.session_state.is_cleared:
        st.session_state.results["wc"] = f"± {real_wc:.3f}"

    bc1, bc2, bc3 = st.columns(3)
    bc1.button("🗑️ Clear / 全部清除", on_click=action, args=("clear",), use_container_width=True)
    
    if bc2.button("🔄 Recalculate / 重新計算", use_container_width=True):
        rss_v = np.sqrt((current_tols**2).sum())
        ts_v = st.session_state.target_val
        cpk_v = ts_v / rss_v if rss_v != 0 else 0
        st.session_state.results = {
            "wc": f"± {real_wc:.3f}", 
            "rss": f"± {rss_v:.3f}", 
            "cpk": f"{cpk_v:.2f}", 
            "yld": f"{(2 * norm.cdf(3 * cpk_v) - 1) * 100:.2f} %"
        }
        st.session_state.is_cleared = False
        st.rerun()
        
    bc3.button("⏪ Reset / 還原範例", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Project information / 專案資訊</p>', unsafe_allow_html=True)
    with st.container(border=True):
        st.session_state.proj_name = st.text_input("Project Name", value="TM-P4125-001" if not st.session_state.is_cleared else "")
        st.session_state.analysis_title = st.text_input("Analysis Title", value="Connector Analysis" if not st.session_state.is_cleared else "")
        c1, c2 = st.columns(2)
        st.session_state.date = c1.text_input("Date", value="2025/12/30" if not st.session_state.is_cleared else "")
        st.session_state.unit = c2.text_input("Unit", value="mm" if not st.session_state.is_cleared else "")
    
    st.session_state.target_val = st.number_input(
        "Target Spec 公差目標 (±)", 
        value=st.session_state.target_val, 
        format="%.3f", 
        on_change=lambda: st.session_state.results.update({"rss":"","cpk":"","yld":""})
    )

    res = st.session_state.results
    res1, res2 = st.columns(2)
    res1.metric("Worst Case", res["wc"])
    res2.metric("RSS Total", res["rss"])
    res1.metric("Est. CPK", res["cpk"])
    res2.metric("Est. Yield", res["yld"])

    

    st.divider()
    con_auto = (
        f"1. Target +/-{st.session_state.target_val:.3f}, CPK {res['cpk']}, Yield {res['yld']}.\n"
        f"2. In RSS calculation, all tolerances must be controlled with CPK ≥ 1.0.\n"
        f"3. \n"
        f"4. "
    )
    st.text_area("✍️ Conclusion 結論", value=con_auto if not st.session_state.is_cleared else "", height=130)
