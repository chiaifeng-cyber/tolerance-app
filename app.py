import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from fpdf import FPDF
import datetime
import os

# 設定頁面為寬螢幕模式，並自訂標題
st.set_page_config(page_title="Tolerance Stack-up Tool", layout="wide")

# --- CSS 樣式優化：16:9 一覽式佈局與字體 ---
st.markdown("""
    <style>
    /* 移除頂部空白 */
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
    
    /* 結果數值：30px 加粗藍色 */
    [data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
    }
    
    /* 結果標題：24px 加粗 (1.5倍) */
    [data-testid="stMetricLabel"] {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #333333 !important;
    }
    
    /* 壓縮元件間距，確保一畫面看全 */
    .element-container { margin-bottom: -5px !important; }
    .stImage { margin-bottom: -10px !important; }
    hr { margin: 1em 0 !important; }
    
    /* 調整資料編輯器高度 */
    div[data-testid="stDataEditor"] > div {
        max-height: 350px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 產生函數 (維持 A4 格式) ---
def create_full_report_pdf(proj, title, date, unit, target, wc, rss, yield_val, cpk, df, img_path=None):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 15, txt="Design Tolerance Analysis Report", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(45, 8, "Project", 1, 0, 'L', True); pdf.cell(145, 8, proj, 1, 1)
    pdf.cell(45, 8, "Title", 1, 0, 'L', True); pdf.cell(145, 8, title, 1, 1)
    pdf.ln(5)
    if img_path and os.path.exists(img_path):
        pdf.image(img_path, x=10, w=140)
        pdf.ln(75)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Summary Results:", ln=True)
    pdf.cell(63, 10, f"Worst Case: +/- {wc:.3f}", 1); pdf.cell(63, 10, f"RSS Total: +/- {rss:.3f}", 1); pdf.cell(64, 10, f"Yield: {yield_val:.2f}%", 1, 1)
    return pdf.output(dest="S").encode("latin-1")

# --- 資料初始化 ---
DEFAULT_DATA = [
    {"Part": "PCB", "No.": "a", "Description": "Panel mark to unit mark", "Upper Tol": 0.100},
    {"Part": "PCB", "No.": "b", "Description": "Unit mark to soldering pad", "Upper Tol": 0.100},
    {"Part": "SMT", "No.": "c", "Description": "SMT tolerance", "Upper Tol": 0.150},
    {"Part": "Connector", "No.": "d", "Description": "Connector housing", "Upper Tol": 0.125},
]
if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

def clear_all(): st.session_state.df_data = pd.DataFrame(columns=["Part", "No.", "Description", "Upper Tol"])
def reset_default(): st.session_state.df_data = pd.DataFrame(DEFAULT_DATA)

# --- 主介面佈局 (左右分欄) ---
st.markdown("<h2 style='text-align: center; margin-bottom: 0px;'>設計累計公差分析工具</h2>", unsafe_allow_html=True)

left_col, right_col = st.columns([1.2, 1]) # 左側略寬於右側

with left_col:
    st.subheader("🖼️ 範例示意與數據輸入")
    # 示意圖區域
    img_filename = "4125.jpg"
    if os.path.exists(img_filename):
        st.image(img_filename, use_container_width=True)
    else:
        st.info("請上傳 4125.jpg 至 GitHub 以顯示範例圖。")
    
    # 數據編輯器
    c1, c2, _ = st.columns([1, 1, 2])
    with c1: st.button("🗑️ 清除資料", on_click=clear_all, use_container_width=True)
    with c2: st.button("🔄 還原範例", on_click=reset_default, use_container_width=True)
    
    edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", use_container_width=True)
    st.session_state.df_data = edited_df

with right_col:
    st.subheader("📋 專案資訊與結果")
    with st.container(border=True):
        proj_name = st.text_input("專案名稱", "TM-P4125-001")
        title_text = st.text_input("分析標題", "Connector Y-Position Analysis")
        c1, c2 = st.columns(2)
        with c1: date_text = st.text_input("日期", "2025/12/29")
        with c2: unit_text = st.text_input("單位", "mm")

    st.divider()
    
    # 計算邏輯
    target_spec = st.number_input("設計公差目標 (Target Spec ±)", value=0.200, format="%.3f")
    if not edited_df.empty and "Upper Tol" in edited_df.columns:
        wc = edited_df["Upper Tol"].sum()
        rss = np.sqrt((edited_df["Upper Tol"]**2).sum())
        cpk = target_spec / rss if rss != 0 else 0
        yield_val = (2 * norm.cdf(3 * cpk) - 1) * 100
    else:
        wc, rss, cpk, yield_val = 0, 0, 0, 0

    # 分析結果區 (字體已按要求放大)
    st.metric("Worst Case (最壞情況)", f"± {wc:.3f} {unit_text}")
    st.metric("RSS Total (均方根)", f"± {rss:.3f} {unit_text}")
    st.metric("預估良率 (Estimated Yield)", f"{yield_val:.2f} %")
    
    st.info(f"結論：CPK 為 {cpk:.2f}。")

    # PDF 下載
    try:
        pdf_bytes = create_full_report_pdf(proj_name, title_text, date_text, unit_text, target_spec, wc, rss, yield_val, cpk, edited_df, img_filename)
        st.download_button("📥 匯出 A4 PDF 報告", data=pdf_bytes, file_name=f"Report_{proj_name}.pdf", use_container_width=True)
    except:
        st.warning("PDF 匯出失敗 (僅支援英文字元)")
