Python

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

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

# 資料輸入表格 (對應你提供的圖片欄位)
st.subheader("公差數據輸入 (Input Table)")
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

# 核心邏輯計算
worst_case = edited_df["Upper Tol"].sum()
rss_val = np.sqrt((edited_df["Upper Tol"]**2).sum())
z_score = target_spec / rss_val
yield_val = (2 * norm.cdf(z_score) - 1) * 100
est_cpk = target_spec / (3 * rss_val)

st.divider()

# 顯示結果
st.subheader("公差疊加分析結果 (Results)")
r1, r2, r3 = st.columns(3)
r1.metric("Worst Case (最壞情況)", f"± {worst_case:.3f} mm")
r2.metric("RSS Total (均方根)", f"± {rss_val:.3f} mm")
r3.metric("預估良率 (Yield)", f"{yield_val:.2f} %")

# 結論自動生成
st.info(f"結論：若採用 {target_spec:.3f} mm 為規格，預估良率約為 {yield_val:.2f}%，CPK