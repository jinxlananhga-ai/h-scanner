from datetime import datetime
import time
import numpy as np
import pandas as pd
import streamlit as st
from vnstock import stock_historical_data

st.set_page_config(
    page_title="Hệ Thống Quét Sóng Thời Gian Thực", page_icon="🚀", layout="wide"
)

st.title("🚀 HỆ THỐNG QUÉT SÓNG THỜI GIAN THỰC (KHUNG 5 PHÚT)")
st.write(
    "Hệ thống đa luồng tốc độ cao quét toàn bộ danh sách mã cổ phiếu, lọc ra"
    " các mã có thanh khoản đột biến."
)

# Test nhanh kết nối vnstock
symbol = st.sidebar.text_input("Nhập mã cổ phiếu kiểm tra:", value="HPG").upper()
if st.button("Kiểm tra dữ liệu"):
  try:
    df = stock_historical_data(
        symbol=symbol,
        resolution="5",
        start_date="2026-01-01",
        end_date=datetime.now().strftime("%Y-%m-%d"),
        source="VCI",
    )
    if df is not None and not df.empty:
      st.success(f"Tải thành công dữ liệu mã {symbol}!")
      st.dataframe(df.tail())
    else:
      st.warning("Không có dữ liệu trả về.")
  except Exception as e:
    st.error(f"Lỗi: {e}")

