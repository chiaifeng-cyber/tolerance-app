import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. Page Configuration
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# CSS 樣式清理，採用單行字串避免解析錯誤
css = '.stApp { background-color: #f0f2f6; } .main .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 98% !important; } h2 { line-height: 1; font-size: 22px; text-align: center; margin-top: -1.5rem; margin-bottom: 10px; color: #1e1e1e; } .section-label, [data-testid="stMetricLabel"], .stTextArea label p, .stNumberInput label p { font-size: 16px !important; font-weight: bold !important; color: #333; margin-bottom: 4px !important; } div[data-testid="stTextInput"] label p { font-size: 11px !important; color: #666 !important; margin-bottom: -5px !important; } .made-by-leo-Oliver { font-size: 10px; color: #aaa; text-align: right; margin-top: 5px; } .table-hint-container { display: flex; align-items: center; margin-top: -22px; margin-bottom: 8px; padding-left: 2px; } .red-check-box { width: 14px; height: 14px; background-color: #ff4b4b; border-radius: 3px; display: flex; align-items: center; justify-content: center; margin-right: 6px; flex-shrink: 0; } .white-checkmark { width: 8px; height: 5px; border-left: 2px solid white; border-bottom: 2px solid white; transform: rotate(-45deg); margin-top: -1px; } .hint-text { font-size: 11px; color: #666; font-weight: normal; } [data-testid="stImage"] img { max-height: 40vh !important; width: auto !important; margin-left: auto; margin-right: auto; display: block; } div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stTextArea"] textarea { background-color: #ffffff !important; border-radius: 8px !important; padding: 4px 8px !important; border: 1px solid #d1d5db !important; } [data-testid="stVerticalBlock"] > div { margin-bottom: 2px !important; gap: 0.4rem !important; } div[data-testid="stDataEditor"] { background-color: #ffffff !important; border-radius: 8px !important; } [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; color: #1f77b4 !important; } hr { display: none !important; } [data-testid="stElementToolbar"] { display: none !important; }'
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# 2. Data Initialization
COLS = ["Part", "Req. CPK (min. 1.33)", "No.", "Description", "Tol. (±)"]

def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "SMT", COLS[1]: "1.33", COLS[2]: "c", COLS[3]: "Assembly process", COLS[4]: 0.150},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.100},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.100},
        {COLS[0]: "Connector", COLS[1]: "1.33", COLS[2]: "d", COLS[3]: "Connector housing outline (0.25/2)", COLS[4]: 0.125}
    ])

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
    st.session_state.target_val = 0.241
    st.session_state.show_img = True

def action(mode):
    st.session_state.uploader_key += 1
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame([{COLS[0]: "", COLS[1]: "", COLS[2]: "", COLS[3]: "", COLS[4]: None} for _ in range(5)])
        st.session_state.target_val, st.session_state.show_img = 0.0, False
    elif mode == "reset":
        st.session_state.df_data, st.session_state.target_val, st.session_state.show_img = get_init_df(), 0.241, True
    st.rerun()

# 3. Main Interface Layout
st.markdown("<h2>Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.4, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input</p>', unsafe_allow_html=True)
    with st.container(border=True):
        up = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")
        if up:
            ext = up.name.split('.')[-1].lower()
            with open(f"temp.{ext}", "wb") as f: f.write(up.getbuffer())
            st.session_state.show_img = True
        if st.session_state.show_img:
            current_img = "temp.png" if os.path.exists("temp.png") else ("temp.jpg" if os.path.exists("temp.jpg") else ("temp.jpeg" if os.path.exists("temp.jpeg") else ("4125.jpg" if os.path.exists("4125.jpg") else None)))
            if current_img: st.image(current_img, use_container_width=True)

    ed_df = st.data_editor(
        st.session_state.df_data, num_rows="dynamic", use_container_width=True,
        column_config={
            COLS[0]: st.column_config.TextColumn(width="small"),
            COLS[1]: st.column_config.TextColumn(width="medium"),
            COLS[2]: st.column_config.TextColumn(width="small"),
            COLS[3]: st.column_config.TextColumn(width="large"),
            COLS[4]: st.column_config.NumberColumn(width="small", format="%.3f"),
        }
    )
    st.session_state.df_data = ed_df
    st.markdown(f'<div class="table-hint-container"><div class="red-check-box"><div class="white-checkmark"></div></div><span class="hint-text">Select the row index on the far left and press "Delete" to remove a row.</span></div>', unsafe_allow_html=True)

    tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    wc_v, rss_v = tols.sum(), np.sqrt((tols**2).sum())
    bc1, bc2 = st.columns(2)
    bc1.button("🗑️ Clear All", on_click=action, args=("clear",), use_container_width=True)
    bc2.button("⏪ Reset to Default", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Project Information</p>', unsafe_allow_html=True)
    with st.container(border=True):
        pn = st.text_input("Project Name", value="TM-P4125-001" if st.session_state.show_img else "")
        at = st.text_input("Analysis Title", value="Connector Analysis" if st.session_state.show_img else "")
        c1, c2 = st.columns(2)
        dt = st.text_input("Date", value="2025/12/30" if st.session_state.show_img else "")
        ut = st.text_input("Unit", value="mm" if st.session_state.show_img else "")
    
    st.markdown('<p class="section-label">⌨️ Target Spec (±)</p>', unsafe_allow_html=True)
    with st.container(border=True):
        ts = st.number_input("Target Spec", value=st.session_state.target_val, format="%.3f", label_visibility="collapsed")
        st.session_state.target_val = ts
        
        # --- 核心邏輯修正 ---
        # 1. 計算 CPK: 當 Target = RSS 時，值為 1.33
        cpk_v = (ts / rss_v * 1.33 if rss_v > 0 else 0)
        
        # 2. 定義良率顯示：只要 CPK 達標 (>=1.33)，良率強制顯示 99.99%
        if rss_v == 0:
            yld_text = ""
        elif cpk_v >= 1.329: # 防止浮點數運算微小誤差
            yld_text = "99.99 %"
        else:
            # 若 CPK 未達 1.33，則按比例換算良率
            # 以 1.33 對應 4-sigma (99.99%) 為計算基準
            yld_val = (2 * norm.cdf(3 * (cpk_v / 1.33) * 1.33) - 1) * 100
            yld_text = f"{min(yld_val, 99.99):.2f} %"

        res1, res2 = st.columns(2)
        res1.metric("Worst Case", f"± {wc_v:.3f}" if wc_v > 0 else "")
        res2.metric("RSS Total", f"± {rss_v:.3f}" if rss_v > 0 else "")
        res1.metric("Est. CPK", f"{cpk_v:.2f}" if rss_v > 0 else "")
        res2.metric("Est. Yield", yld_text)

    st.markdown('<p class="section-label">✍️ Conclusion</p>', unsafe_allow_html=True)
    with st.container(border=True):
        con_auto = (
            f"1. If the Target is +/-{ts:.3f} mm. The estimated CPK {cpk_v:.2f}. The estimated yield {yld_text}.\n"
            f"2. Use the RSS method for the spec. All calculated tolerances must meet a minimum CPK of 1.33."
        )
        st.text_area("Conclusion", value=con_auto if wc_v > 0 else "", height=100, label_visibility="collapsed")
        st.markdown('<div class="made-by-leo-Oliver">App Made by Leo & Oliver</div>', unsafe_allow_html=True)


