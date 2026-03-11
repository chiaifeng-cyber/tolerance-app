import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. Page Configuration
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# CSS 保持不變 (省略部分重複樣式以節省空間)
st.markdown("""<style>
    .stApp { background-color: #f0f2f6; }
    h2 { font-size: 22px; text-align: center; margin-top: -1.5rem; color: #1e1e1e; }
    .section-label { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #1f77b4 !important; }
</style>""", unsafe_allow_html=True)

# 2. Data Initialization
COLS = ["Part", "Req. CPK", "No.", "Description", "Tol. (±)"]

def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "SMT", COLS[1]: "1.33", COLS[2]: "c", COLS[3]: "Assembly process", COLS[4]: 0.150},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.100},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.100},
        {COLS[0]: "Connector", COLS[1]: "1.33", COLS[2]: "d", COLS[3]: "Connector housing", COLS[4]: 0.125}
    ])

# 初始化 session_state
if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# 按鈕處理邏輯
def action_trigger(mode):
    st.session_state.uploader_key += 1 # 強制刷新上傳組件
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame(columns=COLS) # 清空
    elif mode == "reset":
        st.session_state.df_data = get_init_df()

# 3. Layout
st.markdown("<h2>Design Tolerance Stack-up Analysis</h2>", unsafe_allow_html=True)
l, r = st.columns([1.4, 1])

with l:
    st.markdown('<p class="section-label">🖼️ Diagram & Input</p>', unsafe_allow_html=True)
    
    # 圖片上傳區
    with st.container(border=True):
        up = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")
        if up: st.image(up)
        elif os.path.exists("4125.jpg"): st.image("4125.jpg")

    # 🔥 關鍵修正：
    # 使用一個獨立的變數 ed_df 接收結果，value 給予初始 dataframe
    # 不要使用 key="df_data" 或在後續手動回填 session_state
    ed_df = st.data_editor(
        st.session_state.df_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={COLS[4]: st.column_config.NumberColumn(format="%.3f", min_value=0.0)}
    )

    tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    wc_v, rss_v = tols.sum(), np.sqrt((tols**2).sum())
    
    bc1, bc2 = st.columns(2)
    bc1.button("🗑️ Clear All", on_click=action_trigger, args=("clear",), use_container_width=True)
    bc2.button("⏪ Reset to Default", on_click=action_trigger, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Project Info</p>', unsafe_allow_html=True)
    with st.container(border=True):
        st.text_input("Project Name", value="TM-P4125-001")
        st.text_input("Analysis Title", value="Connector Analysis")
    
    st.markdown('<p class="section-label">⌨️ Target Spec (±)</p>', unsafe_allow_html=True)
    with st.container(border=True):
        # 這裡不使用 session_state 綁定，直接用變數接收
        ts = st.number_input("Target", value=0.241, format="%.3f", label_visibility="collapsed")
        
        cpk_v = (ts / rss_v * 1.33) if rss_v > 0 else 0
        yld_val = (2 * norm.cdf(3 * cpk_v) - 1) * 100 if rss_v > 0 else 0
        yld_text = f"{min(yld_val, 99.99):.2f} %" if yld_val < 99.995 else "99.99 %"

        res1, res2 = st.columns(2)
        res1.metric("Worst Case", f"± {wc_v:.3f}")
        res2.metric("RSS Total", f"± {rss_v:.3f}")
        res1.metric("Est. CPK", f"{cpk_v:.2f}")
        res2.metric("Est. Yield", yld_text)

    st.markdown('<p class="section-label">✍️ Conclusion</p>', unsafe_allow_html=True)
    with st.container(border=True):
        con_auto = f"1. Target Spec: +/-{ts:.3f} mm.\n2. Est. CPK: {cpk_v:.2f}, Yield: {yld_text}."
        st.text_area("Conclusion", value=con_auto if wc_v > 0 else "", height=100, label_visibility="collapsed")
        st.markdown('<div style="text-align:right; font-size:10px; color:#aaa;">App Made by Leo & Oliver</div>', unsafe_allow_html=True)
