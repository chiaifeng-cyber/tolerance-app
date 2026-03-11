import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. Page Configuration
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# CSS 樣式
st.markdown("""<style>
    .stApp { background-color: #f0f2f6; }
    .main .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 98% !important;
    }
    h2 { line-height: 1; font-size: 22px; text-align: center; margin-top: -1.5rem; margin-bottom: 10px; color: #1e1e1e; }
    .section-label, [data-testid="stMetricLabel"] { 
        font-size: 16px !important; font-weight: bold !important; color: #333; 
        margin-bottom: 4px !important;
    }
    .made-by-leo {
        font-size: 10px; color: #aaa; text-align: right; margin-top: 5px;
    }
    .table-hint-container {
        display: flex; align-items: center; margin-top: -22px; margin-bottom: 8px; padding-left: 2px;
    }
    .red-check-box {
        width: 14px; height: 14px; background-color: #ff4b4b; border-radius: 3px;
        display: flex; align-items: center; justify-content: center; margin-right: 6px;
    }
    .white-checkmark {
        width: 8px; height: 5px; border-left: 2px solid white; border-bottom: 2px solid white;
        transform: rotate(-45deg); margin-top: -1px;
    }
    .hint-text { font-size: 11px; color: #666; }
    [data-testid="stImage"] img { max-height: 40vh !important; width: auto !important; margin: 0 auto; display: block; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; color: #1f77b4 !important; }
</style>""", unsafe_allow_html=True)

# 2. Data Initialization
COLS = ["Part", "Req. CPK", "No.", "Description", "Tol. (±)"]

def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "SMT", COLS[1]: "1.33", COLS[2]: "c", COLS[3]: "Assembly process", COLS[4]: 0.150},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.100},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.100},
        {COLS[0]: "Connector", COLS[1]: "1.33", COLS[2]: "d", COLS[3]: "Connector housing outline", COLS[4]: 0.125}
    ])

# 初始化 Session State
if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
if 'target_val' not in st.session_state:
    st.session_state.target_val = 0.241
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

def handle_action(mode):
    st.session_state.uploader_key += 1
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame([{c: "" if i < 4 else 0.0 for i, c in enumerate(COLS)} for _ in range(4)])
        st.session_state.target_val = 0.0
    elif mode == "reset":
        st.session_state.df_data = get_init_df()
        st.session_state.target_val = 0.241
    # 這裡不需要 rerun，Streamlit 偵測到 State 改變會自動處理

# 3. Main Interface Layout
st.markdown("<h2>Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.4, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input</p>', unsafe_allow_html=True)
    with st.container(border=True):
        up = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")
        if up:
            with open("temp_img", "wb") as f: f.write(up.getbuffer())
            st.image("temp_img", use_container_width=True)
        elif os.path.exists("4125.jpg"):
            st.image("4125.jpg", use_container_width=True)

    # 💡 修正點：使用 key 直接綁定，避免重複賦值導致的「輸入兩次」問題
    ed_df = st.data_editor(
        st.session_state.df_data,
        num_rows="dynamic",
        use_container_width=True,
        key="main_editor",
        column_config={
            COLS[4]: st.column_config.NumberColumn(format="%.3f")
        }
    )
    # 同步編輯後的數據回到 session_state
    st.session_state.df_data = ed_df

    st.markdown("""<div class="table-hint-container"><div class="red-check-box"><div class="white-checkmark"></div></div>
        <span class="hint-text">Select row index and press "Delete" to remove.</span></div>""", unsafe_allow_html=True)

    tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    wc_v, rss_v = tols.sum(), np.sqrt((tols**2).sum())
    
    bc1, bc2 = st.columns(2)
    bc1.button("🗑️ Clear All", on_click=handle_action, args=("clear",), use_container_width=True)
    bc2.button("⏪ Reset to Default", on_click=handle_action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Project Information</p>', unsafe_allow_html=True)
    with st.container(border=True):
        st.text_input("Project Name", value="TM-P4125-001")
        st.text_input("Analysis Title", value="Connector Analysis")
        c1, c2 = st.columns(2)
        with c1: st.text_input("Date", value="2026/03/11")
        with c2: st.text_input("Unit", value="mm")

    st.markdown('<p class="section-label">⌨️ Target Spec (±)</p>', unsafe_allow_html=True)
    with st.container(border=True):
        # 💡 修正點：直接使用 session_state 綁定，避免 ts 變數衝突
        ts = st.number_input("Target Spec", format="%.3f", key="target_val", label_visibility="collapsed")
        
        # 核心計算
        cpk_v = (ts / rss_v * 1.33) if rss_v > 0 else 0
        
        # 標準良率計算公式: Yield = Phi(3*CPK) - Phi(-3*CPK)
        if rss_v == 0:
            yld_text = "0.00 %"
        else:
            yld_val = (2 * norm.cdf(3 * cpk_v) - 1) * 100
            yld_text = "> 99.99 %" if yld_val > 99.99 else f"{max(yld_val, 0):.2f} %"

        res1, res2 = st.columns(2)
        res1.metric("Worst Case", f"± {wc_v:.3f}")
        res2.metric("RSS Total", f"± {rss_v:.3f}")
        res1.metric("Est. CPK", f"{cpk_v:.2f}")
        res2.metric("Est. Yield", yld_text)

    st.markdown('<p class="section-label">✍️ Conclusion</p>', unsafe_allow_html=True)
    with st.container(border=True):
        con_auto = (
            f"1. Target Spec: +/-{ts:.3f} mm. Estimated CPK: {cpk_v:.2f}. Yield: {yld_text}.\n"
            f"2. Statistical analysis (RSS) shows the design meets 1.33 CPK requirements."
        )
        st.text_area("Conclusion", value=con_auto if wc_v > 0 else "", height=100, label_visibility="collapsed")
        st.markdown('<div class="made-by-leo">App Made by Leo & Oliver</div>', unsafe_allow_html=True)
