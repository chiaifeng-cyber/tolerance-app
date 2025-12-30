import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import os

# 1. Page Configuration & Professional Compact CSS
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #f0f2f6; }
    .main .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 98% !important;
    }
    h2 { line-height: 1; font-size: 22px; text-align: center; margin-top: -1.5rem; margin-bottom: 10px; color: #1e1e1e; }
    
    .section-label, [data-testid="stMetricLabel"], .stTextArea label p, .stNumberInput label p { 
        font-size: 16px !important; font-weight: bold !important; color: #333; 
        margin-bottom: 4px !important;
    }

    /* 💡 修正提示標籤：紅底白勾圖示與極窄間距 */
    .table-hint-container {
        display: flex;
        align-items: center;
        margin-top: -22px; 
        margin-bottom: 8px;
        padding-left: 2px;
    }
    .red-check-box {
        width: 14px;
        height: 14px;
        background-color: #ff4b4b; /* 紅底 */
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 6px;
        flex-shrink: 0;
    }
    .white-checkmark {
        width: 8px;
        height: 5px;
        border-left: 2px solid white; /* 白勾 */
        border-bottom: 2px solid white;
        transform: rotate(-45deg);
        margin-top: -1px;
    }
    .hint-text {
        font-size: 11.5px;
        color: #666;
        font-weight: normal;
    }

    [data-testid="stImage"] img {
        max-height: 40vh !important;
        width: auto !important;
        margin-left: auto;
        margin-right: auto;
        display: block;
    }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        border: 1px solid #d1d5db !important;
    }
    [data-testid="stVerticalBlock"] > div { margin-bottom: 2px !important; gap: 0.4rem !important; }
    div[data-testid="stDataEditor"] { background-color: #ffffff !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: bold; color: #1f77b4 !important; }
    
    hr { display: none !important; }
    [data-testid="stElementToolbar"] { display: none !important; }
</style>""", unsafe_allow_html=True)

# 2. Data Initialization
COLS = ["Part", "Req. CPK (min. 1.0)", "No.", "Description", "Tol. (±)"]

def get_init_df():
    return pd.DataFrame([
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "a", COLS[3]: "Panel mark to unit mark", COLS[4]: 0.100},
        {COLS[0]: "PCB", COLS[1]: "1.33", COLS[2]: "b", COLS[3]: "Unit mark to soldering pad", COLS[4]: 0.100},
        {COLS[0]: "SMT", COLS[1]: "1.0", COLS[2]: "c", COLS[3]: "SMT tolerance", COLS[4]: 0.150},
        {COLS[0]: "Connector", COLS[1]: "1.33", COLS[2]: "d", COLS[3]: "Connector housing (0.25/2)", COLS[4]: 0.125}
    ])

if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'df_data' not in st.session_state:
    st.session_state.df_data = get_init_df()
    st.session_state.target_val = 0.2
    st.session_state.show_img = True

def action(mode):
    st.session_state.uploader_key += 1
    if mode == "clear":
        st.session_state.df_data = pd.DataFrame([{COLS[0]: "", COLS[1]: "", COLS[2]: "", COLS[3]: "", COLS[4]: None} for _ in range(5)])
        st.session_state.target_val, st.session_state.show_img = 0.0, False
    elif mode == "reset":
        st.session_state.df_data, st.session_state.target_val, st.session_state.show_img = get_init_df(), 0.2, True
    for ext in ["png", "jpg", "jpeg"]:
        f = f"temp.{ext}"
        if os.path.exists(f):
            try: os.remove(f)
            except: pass
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

    # Data Editor
    ed_df = st.data_editor(
        st.session_state.df_data, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            COLS[0]: st.column_config.TextColumn(width="small"),
            COLS[1]: st.column_config.TextColumn(width="medium"),
            COLS[2]: st.column_config.TextColumn(width="small"),
            COLS[3]: st.column_config.TextColumn(width="large"),
            COLS[4]: st.column_config.NumberColumn(width="small", format="%.3f"),
        }
    )
    st.session_state.df_data = ed_df

    # 💡 紅底白勾提示標籤
    st.markdown("""
        <div class="table-hint-container">
            <div class="red-check-box"><div class="white-checkmark"></div></div>
            <span class="hint-text">Select the row index on the far left and press "Delete" to remove a row.</span>
        </div>
    """, unsafe_allow_html=True)

    tols = pd.to_numeric(ed_df[COLS[4]], errors='coerce').fillna(0)
    wc_v, rss_v = tols.sum(), np.sqrt((tols**2).sum())

    bc1, bc2 = st.columns(2)
    bc1.button("🗑️ Clear All", on_click=action, args=("clear",), use_container_width=True)
    bc2.button("⏪ Reset to Default", on_click=action, args=("reset",), use_container_width=True)

with r:
    st.markdown('<p class="section-label">📋 Project Information</p>', unsafe_allow_html=True)
    with st.container(border=True):
        pn = st.text_input("Project Name", value="TM-P4125-001" if st.session_state.show_img else "", label_visibility="collapsed")
        at = st.text_input("Analysis Title", value="Connector Analysis" if st.session_state.show_img else "", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        dt = c1.text_input("Date", value="2025/12/30" if st.session_state.show_img else "", label_visibility="collapsed")
        ut = c2.text_input("Unit", value="mm" if st.session_state.show_img else "", label_visibility="collapsed")
    
    st.markdown('<p class="section-label">⌨️ Target Spec (±)</p>', unsafe_allow_html=True)
    with st.container(border=True):
        ts = st.number_input("Target Spec", value=st.session_state.target_val, format="%.3f", label_visibility="collapsed")
        st.session_state.target_val = ts
        cpk_v, yld_v = (ts / rss_v if rss_v > 0 else 0), ((2 * norm.cdf(3 * (ts / rss_v if rss_v > 0 else 0)) - 1) * 100 if rss_v > 0 else 0)
        res1, res2 = st.columns(2)
        res1.metric("Worst Case", f"± {wc_v:.3f}" if wc_v > 0 else ""); res2.metric("RSS Total", f"± {rss_v:.3f}" if rss_v > 0 else "")
        res1.metric("Est. CPK", f"{cpk_v:.2f}" if rss_v > 0 else ""); res2.metric("Est. Yield", f"{yld_v:.2f} %" if rss_v > 0 else "")

    
    st.markdown('<p class="section-label">✍️ Conclusion</p>', unsafe_allow_html=True)
    with st.container(border=True):
        # 💡 修復：確保換行符號正確渲染，不再出現亂碼
        con_auto = (
            f"1. Target +/-{ts:.3f}, CPK {cpk_v:.2f}, Yield {yld_v:.2f}%.\n"
            f"2. Use the RSS method for the spec. All calculated tolerances must meet a minimum Cpk of 1.0."
        )
        st.text_area("Conclusion", value=con_auto if wc_v > 0 else "", height=100, label_visibility="collapsed")
