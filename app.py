import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

# 設定頁面資訊
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# --- 新增 CSS 樣式以縮小間距 ---
st.markdown("""
    <style>
    /* 縮小元件之間的底部間距 */
    .element-container { margin-bottom: -10px; }
    /* 特別針對圖片元件縮小間距 */
    .stImage { margin-bottom: -20px; }
    /* 調整 subheader 的間距 */
    h3 { margin-top: -20px; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 頁面標題
st.markdown("<h2 style='text-align: center;'>設計累計公差分析</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Design Tolerance Stack-up Analysis</h4>", unsafe_allow_html=True)

# 專案基本資訊
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("專案名稱 (Project Name)", "TM-P4125-001")
        st.text_input("分析標題 (Title)", "Connector Y-Position Analysis")
    with c2:
        st.text_input("日期 (Date)", "2025/12/17")
        st.text_input("尺寸單位 (Unit)", "mm")

st.divider()

# --- 圖片上傳區域 (優化佈局) ---
with st.container():
    st.subheader("累積公差圖示 (Tolerance Stack-up Diagram)")
    uploaded_image = st.file_uploader("匯入圖片檔 (Upload Image)", type=["png", "jpg", "jpeg"], key="diagram_uploader")

    if uploaded_image is not None:
        # 移除 caption 可以省下更多空間
        st.image(uploaded_image, use_container_width=True)

# 這裡移除原有的 st.divider()，讓標題直接緊跟圖片
st.subheader("公差數據輸入 (Input Table)")

# 資料輸入表格
data = [
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "a", "Description": "Panel mark to unit mark", "Upper Tol": 0.100, "Lower Tol": 0.100},
    {"Part": "PCB", "Req. CPK": 1.33, "No.": "b", "Description": "Unit mark to soldering pad", "Upper Tol": 0.100, "Lower Tol": 0.100},
    {"Part": "SMT", "Req. CPK": 1.00, "No.": "c", "Description": "SMT tolerance", "Upper Tol": 0.150, "Lower Tol": 0.150},
    {"Part": "Connector", "Req. CPK": 1.33, "No.": "d", "Description": "Connector housing (0.25/2)", "Upper Tol": 0.125, "Lower Tol": 0.125},
]
df = pd.DataFrame(data)
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# 計算區
target_spec = st.number_input("目前設計公差目標 (Target Spec ±)", value=0.200, format="%.3f")

# --- 核心邏輯計算 ---
worst_case = edited_df["Upper Tol"].sum()
rss_val = np.sqrt((edited_df["Upper Tol"]**2).sum())

# 預估 CPK 計算 (F21 / F23)
est_cpk = target_spec / rss_val if rss_val != 0 else 0

# 預估良率計算 (2 * NORM.S.DIST(3 * CPK, TRUE) - 1)
z_score = 3 * est_cpk
yield_val = (2 * norm.cdf(z_score) - 1) * 100

st.divider()

# 顯示結果 (Results)
st.subheader("公差疊加分析結果 (Results)")
r1, r2, r3 = st.columns(3)
r1.metric("Worst Case (最壞情況)", f"± {worst_case:.3f} mm")
r2.metric("RSS Total (均方根)", f"± {rss_val:.3f} mm")
r3.metric("預估良率 (Yield)", f"{yield_val:.2f} %")

# 結論自動生成
st.info(f"結論：若採用 {target_spec:.3f} mm 為規格，預估良率約為 {yield_val:.2f}%，CPK 約為 {est_cpk:.2f}。")
